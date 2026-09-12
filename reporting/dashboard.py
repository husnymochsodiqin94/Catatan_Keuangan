"""Menyusun DashboardData & merender halaman dari data Financial Engine.

Aturan penting: seluruh ANGKA berasal dari ``FinancialEngine``. Modul ini tidak
menghitung ulang total/saldo/cash flow; ia hanya memetakan objek transaksi ke
dict tampilan, mengurutkan, dan memformat.
"""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, field
from typing import Dict, List, Optional

from financial_engine import FinancialEngine, Transaction, TransactionType


@dataclass
class DashboardData:
    year: int
    month: int
    total_balance: int  # net worth (dari engine)
    income: int
    expense: int
    net_cash_flow: int
    expense_by_category: List[Dict[str, object]] = field(default_factory=list)
    recent: List[Dict[str, object]] = field(default_factory=list)
    accounts: List[Dict[str, object]] = field(default_factory=list)


def _account_label(engine: FinancialEngine, tx: Transaction) -> str:
    def name(aid: Optional[str]) -> str:
        return engine.get_account(aid).name if aid else "-"

    if tx.type is TransactionType.TRANSFER:
        return f"{name(tx.from_account_id)} → {name(tx.to_account_id)}"
    return name(tx.from_account_id or tx.to_account_id)


def _tx_view(engine: FinancialEngine, tx: Transaction) -> Dict[str, object]:
    return {
        "id": tx.id,
        "type": tx.type.value,
        "amount": tx.amount,
        "category": tx.category,
        "account": _account_label(engine, tx),
        "date": tx.occurred_at.date().isoformat(),
        "note": tx.note,
    }


def transaction_views(engine: FinancialEngine, **filters) -> List[Dict[str, object]]:
    """Daftar transaksi (untuk History). Filter/search didelegasikan ke engine."""
    return [_tx_view(engine, tx) for tx in engine.query_transactions(**filters)]


def build_dashboard(engine: FinancialEngine, year: int, month: int) -> DashboardData:
    ms = engine.month_summary(year, month)
    cats = engine.expense_by_category(ms["start"], ms["end"])
    cat_list = [
        {"category": k, "amount": v}
        for k, v in sorted(cats.items(), key=lambda kv: kv[1], reverse=True)
    ]
    return DashboardData(
        year=year, month=month,
        total_balance=engine.net_worth(),
        income=int(ms["income"]),
        expense=int(ms["expense"]),
        net_cash_flow=int(ms["net_cash_flow"]),
        expense_by_category=cat_list,
        recent=[_tx_view(engine, tx) for tx in engine.recent_transactions(5)],
        accounts=[
            {"id": a.id, "name": a.name, "type": a.type.value, "balance": engine.balance(a.id)}
            for a in engine.accounts()
        ],
    )


# --------------------------------------------------------------------------- #
# Renderer: HTML statis yang HANYA menampilkan data (tanpa hitung ulang finansial)
# --------------------------------------------------------------------------- #
_TEMPLATE_PATH = os.path.join(os.path.dirname(__file__), "dashboard_template.html")


def render_dashboard_html(
    data: DashboardData, transactions: List[Dict[str, object]]
) -> str:
    payload = {"dashboard": asdict(data), "transactions": transactions}
    with open(_TEMPLATE_PATH, encoding="utf-8") as fh:
        template = fh.read()
    # Sisipkan data sebagai JSON (frontend hanya merender, tidak menghitung).
    return template.replace("/*__DATA__*/", json.dumps(payload, ensure_ascii=False))
