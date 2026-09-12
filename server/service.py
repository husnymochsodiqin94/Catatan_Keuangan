"""Service: menyatukan Storage + Financial Engine + NLP + Reporting.

Setiap operasi merehidrasi FinancialEngine dari Storage (transaksi = sumber
kebenaran), memakai engine untuk validasi & perhitungan, lalu menyimpan hasilnya.
Tidak ada logika finansial yang diduplikasi di sini.
"""

from __future__ import annotations

from dataclasses import asdict
from datetime import datetime
from typing import Any, Dict, List, Optional

from financial_engine import (
    AccountType,
    FinancialEngine,
    Transaction,
    TransactionType,
    ValidationError,
)
from financial_engine.budgeting import evaluate as evaluate_budgets
from nlp import ParsePipeline
from reporting.dashboard import _tx_view, build_dashboard, transaction_views

from . import email_alert
from .storage import Storage

DEFAULT_SETTINGS: Dict[str, Any] = {
    "alert_threshold": 90, "alert_email": "",
    "spending_limit": None, "income_target": None, "category_budgets": [],
}


def build_engine(storage: Storage) -> FinancialEngine:
    """Rehidrasi engine dari data tersimpan."""
    e = FinancialEngine()
    for a in storage.list_accounts():
        acc = e.add_account(a["name"], AccountType(a["type"]),
                            starting_balance=a["starting_balance"],
                            currency=a["currency"], id=a["id"])
        if a["archived"]:
            acc.archived = True
    for r in storage.list_transactions(include_deleted=True):
        e.load_transaction(Transaction(
            id=r["id"], type=TransactionType(r["type"]), amount=r["amount"],
            occurred_at=datetime.fromisoformat(r["occurred_at"]),
            from_account_id=r["from_account_id"], to_account_id=r["to_account_id"],
            category=r["category"], note=r["note"],
            related_transaction_id=r["related_transaction_id"],
            source=r["source"], deleted=bool(r["deleted"]),
        ))
    return e


# --------------------------------------------------------------------- #
# Akun
# --------------------------------------------------------------------- #
def list_accounts(storage: Storage) -> List[Dict[str, Any]]:
    e = build_engine(storage)
    return [
        {"id": a.id, "name": a.name, "type": a.type.value, "balance": e.balance(a.id)}
        for a in e.accounts()
    ]


def create_account(storage: Storage, name: str, type: str,
                   starting_balance: int = 0) -> Dict[str, Any]:
    if not name or not str(name).strip():
        raise ValidationError("nama akun wajib diisi")
    AccountType(type)  # validasi tipe (raise ValueError bila tidak dikenal)
    if not isinstance(starting_balance, int) or isinstance(starting_balance, bool):
        raise ValidationError("saldo awal harus integer")
    return storage.add_account(name.strip(), type, starting_balance)


# --------------------------------------------------------------------- #
# Parse (AI) — tidak menyimpan
# --------------------------------------------------------------------- #
def parse_text(storage: Storage, text: str,
               now: Optional[datetime] = None) -> Dict[str, Any]:
    e = build_engine(storage)
    drafts = ParsePipeline(e).process(text, now=now)
    return {"drafts": [_serialize_draft(d) for d in drafts]}


def _serialize_draft(d) -> Dict[str, Any]:
    p = d.parsed
    return {
        "type": p.type, "amount": p.amount, "currency": p.currency,
        "category": p.category, "subcategory": p.subcategory,
        "account": p.account, "from_account": p.from_account, "to_account": p.to_account,
        "account_id": d.account_id, "from_account_id": d.from_account_id,
        "to_account_id": d.to_account_id,
        "date": p.date.isoformat() if p.date else None,
        "occurred_at": d.occurred_at.isoformat(),
        "note": p.note, "confidence": p.confidence, "ambiguous": p.ambiguous,
        "status": d.status, "missing": d.missing,
        "duplicates": [t.id for t in d.duplicates],
    }


# --------------------------------------------------------------------- #
# Transaksi (commit) — deterministik, tervalidasi engine lalu disimpan
# --------------------------------------------------------------------- #
def create_transaction(storage: Storage, f: Dict[str, Any],
                       now: Optional[datetime] = None) -> Dict[str, Any]:
    e = build_engine(storage)
    typ = f.get("type")
    amount = f.get("amount")
    occurred_at = _parse_dt(f.get("occurred_at")) or now or datetime.now()
    category = f.get("category")
    note = f.get("note")

    if typ == "expense":
        tx = e.create_expense(amount, f.get("account_id"), category=category,
                              occurred_at=occurred_at, note=note, source="app")
    elif typ == "income":
        tx = e.create_income(amount, f.get("account_id"), category=category,
                             occurred_at=occurred_at, note=note, source="app")
    elif typ == "transfer":
        tx = e.create_transfer(amount, f.get("from_account_id"), f.get("to_account_id"),
                               occurred_at=occurred_at, note=note, source="app")
    elif typ == "refund":
        tx = e.create_refund(amount, f.get("account_id"), category=category,
                             occurred_at=occurred_at, note=note, source="app")
    else:
        raise ValidationError(f"tipe transaksi tidak didukung: {typ!r}")

    row = storage.add_transaction({
        "type": tx.type.value, "amount": tx.amount,
        "occurred_at": tx.occurred_at.isoformat(),
        "from_account_id": tx.from_account_id, "to_account_id": tx.to_account_id,
        "category": tx.category, "note": tx.note, "source": tx.source,
    })
    tx.id = row["id"]  # samakan id engine (in-memory) dengan id tersimpan
    return {
        "transaction": _tx_view(e, tx),
        "summary": _summary_from_engine(e, occurred_at.year, occurred_at.month),
    }


def list_transactions(storage: Storage, type: Optional[str] = None,
                      text: Optional[str] = None,
                      account_id: Optional[str] = None) -> List[Dict[str, Any]]:
    e = build_engine(storage)
    return transaction_views(e, type=type, text=text, account_id=account_id)


def delete_transaction(storage: Storage, tx_id: str,
                       year: Optional[int] = None,
                       month: Optional[int] = None) -> Dict[str, Any]:
    if not storage.soft_delete(tx_id):
        raise ValidationError(f"transaksi {tx_id!r} tidak ditemukan")
    e = build_engine(storage)
    now = datetime.now()
    return {"summary": _summary_from_engine(e, year or now.year, month or now.month)}


# --------------------------------------------------------------------- #
# Dashboard
# --------------------------------------------------------------------- #
def summary(storage: Storage, year: Optional[int] = None,
            month: Optional[int] = None) -> Dict[str, Any]:
    now = datetime.now()
    e = build_engine(storage)
    return _summary_from_engine(e, year or now.year, month or now.month)


def _summary_from_engine(e: FinancialEngine, year: int, month: int) -> Dict[str, Any]:
    return asdict(build_dashboard(e, year, month))


# --------------------------------------------------------------------- #
# Edit transaksi
# --------------------------------------------------------------------- #
_EDIT_FIELDS = ("amount", "category", "note", "occurred_at",
                "from_account_id", "to_account_id")


def edit_transaction(storage: Storage, tx_id: str, fields: Dict[str, Any],
                     now: Optional[datetime] = None) -> Dict[str, Any]:
    e = build_engine(storage)
    changes: Dict[str, Any] = {k: fields[k] for k in _EDIT_FIELDS if k in fields}
    if "occurred_at" in changes:
        changes["occurred_at"] = _parse_dt(changes["occurred_at"]) or datetime.now()
    e.edit_transaction(tx_id, **changes)  # validasi (raise bila tidak valid)
    db = dict(changes)
    if "occurred_at" in db and db["occurred_at"] is not None:
        db["occurred_at"] = db["occurred_at"].isoformat()
    storage.update_transaction(tx_id, db)
    now = now or datetime.now()
    return {"summary": _summary_from_engine(build_engine(storage), now.year, now.month)}


# --------------------------------------------------------------------- #
# Pengaturan (batas, target, alert) & anggaran
# --------------------------------------------------------------------- #
def get_settings(storage: Storage) -> Dict[str, Any]:
    return {**DEFAULT_SETTINGS, **storage.get_settings()}


def update_settings(storage: Storage, patch: Dict[str, Any]) -> Dict[str, Any]:
    cur = storage.get_settings()
    for k in ("alert_threshold", "alert_email", "spending_limit",
              "income_target", "category_budgets"):
        if k in patch:
            cur[k] = patch[k]
    storage.save_settings(cur)
    return {**DEFAULT_SETTINGS, **cur}


def budget_status(storage: Storage, ref: Optional[datetime] = None) -> Dict[str, Any]:
    return evaluate_budgets(build_engine(storage), get_settings(storage), ref)


def send_alerts(storage: Storage) -> Dict[str, Any]:
    cfg = get_settings(storage)
    alerts = budget_status(storage)["alerts"]
    if not alerts:
        return {"sent": False, "reason": "tidak ada alert", "alerts": []}
    email = (cfg.get("alert_email") or "").strip()
    if not email_alert.is_configured() or not email:
        return {"sent": False, "reason": "email belum dikonfigurasi", "alerts": alerts}
    body = "\n\n".join(f"{a['title']}: {a['message']}" for a in alerts)
    email_alert.send_email(email, "Peringatan Anggaran — AI Financial Assistant", body)
    return {"sent": True, "alerts": alerts}


def _parse_dt(value) -> Optional[datetime]:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except (TypeError, ValueError):
        return None
