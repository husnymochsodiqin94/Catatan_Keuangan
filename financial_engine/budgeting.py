"""Evaluasi anggaran, batas pengeluaran, target pemasukan, dan alert.

Deterministik & murni: memakai angka dari FinancialEngine (cash_flow,
expense_by_category) untuk menghitung pemakaian per periode. Tidak mengirim
apa pun (email dsb) — hanya menghasilkan status & daftar alert siap-kirim.
"""

from __future__ import annotations

import calendar
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from .engine import FinancialEngine

PERIOD_LABEL = {"daily": "hari ini", "weekly": "minggu ini", "monthly": "bulan ini"}
DEFAULT_THRESHOLD = 90


def period_bounds(period: str, ref: datetime) -> Tuple[datetime, datetime]:
    """Batas awal–akhir periode yang memuat ``ref``."""
    if period == "daily":
        start = datetime(ref.year, ref.month, ref.day)
        return start, start.replace(hour=23, minute=59, second=59, microsecond=999999)
    if period == "weekly":
        monday = ref - timedelta(days=ref.weekday())
        start = datetime(monday.year, monday.month, monday.day)
        return start, start + timedelta(days=6, hours=23, minutes=59, seconds=59, microseconds=999999)
    if period == "monthly":
        start = datetime(ref.year, ref.month, 1)
        last = calendar.monthrange(ref.year, ref.month)[1]
        return start, datetime(ref.year, ref.month, last, 23, 59, 59, 999999)
    raise ValueError(f"periode tidak dikenal: {period!r}")


def _rp(n: int) -> str:
    return "Rp" + format(int(n), ",d").replace(",", ".")


def _pct(used: int, amount: int) -> int:
    return round(used / amount * 100) if amount else 0


def evaluate(engine: FinancialEngine, config: Dict[str, Any],
             ref: Optional[datetime] = None) -> Dict[str, Any]:
    """Hitung status batas/target/anggaran + daftar alert.

    config: {alert_threshold, spending_limit:{period,amount}, income_target:{period,amount},
             category_budgets:[{category,amount}] (bulanan)}
    """
    ref = ref or datetime.now()
    threshold = int(config.get("alert_threshold") or DEFAULT_THRESHOLD)
    out: Dict[str, Any] = {"spending_limit": None, "income_target": None,
                           "categories": [], "alerts": []}

    sl = config.get("spending_limit") or {}
    if sl.get("amount"):
        s, e = period_bounds(sl.get("period", "monthly"), ref)
        used = engine.cash_flow(s, e)["net_expense"]
        amount = int(sl["amount"]); pct = _pct(used, amount); over = used > amount
        out["spending_limit"] = {
            "period": sl.get("period", "monthly"), "amount": amount, "used": used,
            "remaining": amount - used, "pct": pct, "alert": pct >= threshold, "over": over,
        }
        if pct >= threshold:
            lbl = PERIOD_LABEL.get(sl.get("period"), "periode ini")
            out["alerts"].append({
                "kind": "spending_limit", "level": "over" if over else "warn",
                "title": "Batas pengeluaran",
                "message": f"Pengeluaran {lbl} sudah {_rp(used)} ({pct}%) dari batas {_rp(amount)}.",
            })

    it = config.get("income_target") or {}
    if it.get("amount"):
        s, e = period_bounds(it.get("period", "monthly"), ref)
        achieved = engine.cash_flow(s, e)["income"]
        amount = int(it["amount"])
        out["income_target"] = {
            "period": it.get("period", "monthly"), "amount": amount,
            "achieved": achieved, "pct": _pct(achieved, amount),
        }

    s, e = period_bounds("monthly", ref)
    by = engine.expense_by_category(s, e)
    for b in config.get("category_budgets") or []:
        amount = int(b.get("amount") or 0)
        if amount <= 0:
            continue
        used = by.get(b["category"], 0)
        pct = _pct(used, amount)
        status = "over" if used > amount else ("warn" if pct >= threshold else "ok")
        out["categories"].append({
            "category": b["category"], "amount": amount, "used": used,
            "pct": pct, "status": status,
        })
        if status in ("warn", "over"):
            out["alerts"].append({
                "kind": "category", "level": status,
                "title": f"Anggaran {b['category']}",
                "message": (f"{b['category']} sudah {_rp(used)} ({pct}%) "
                            f"dari anggaran {_rp(amount)} bulan ini."),
            })

    return out
