"""Service: Storage + Financial Engine + NLP + Reporting, multi-user.

Setiap operasi data ter-scope ``user_id``. Merehidrasi FinancialEngine dari data
milik user, memakai engine untuk validasi & perhitungan, lalu menyimpan hasilnya.
Tidak ada logika finansial yang diduplikasi di sini.
"""

from __future__ import annotations

import re
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

from . import auth, email_alert
from .storage import Storage

DEFAULT_SETTINGS: Dict[str, Any] = {
    "alert_threshold": 90, "alert_email": "",
    "spending_limit": None, "income_target": None, "category_budgets": [],
}
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class AuthError(ValueError):
    """Kredensial/registrasi tidak valid."""


# --------------------------------------------------------------------- #
# Autentikasi
# --------------------------------------------------------------------- #
def _public_user(u: Dict[str, Any]) -> Dict[str, Any]:
    return {"id": u["id"], "email": u["email"], "display_name": u.get("display_name")}


def register(storage: Storage, email: str, password: str,
             display_name: str = "") -> Dict[str, Any]:
    email = (email or "").strip().lower()
    if not _EMAIL_RE.match(email):
        raise AuthError("email tidak valid")
    if not password or len(password) < 6:
        raise AuthError("kata sandi minimal 6 karakter")
    if storage.get_user_by_email(email):
        raise AuthError("email sudah terdaftar")
    user = storage.create_user(email, auth.hash_password(password), (display_name or "").strip())
    token = storage.create_session(user["id"])
    return {"token": token, "user": _public_user(user)}


def login(storage: Storage, email: str, password: str) -> Dict[str, Any]:
    email = (email or "").strip().lower()
    user = storage.get_user_by_email(email)
    if not user or not auth.verify_password(password or "", user["password_hash"]):
        raise AuthError("email atau kata sandi salah")
    token = storage.create_session(user["id"])
    return {"token": token, "user": _public_user(user)}


def logout(storage: Storage, token: str) -> Dict[str, Any]:
    storage.delete_session(token)
    return {"ok": True}


def current_user(storage: Storage, user_id: str) -> Dict[str, Any]:
    u = storage.get_user(user_id)
    if not u:
        raise AuthError("sesi tidak valid")
    return _public_user(u)


# --------------------------------------------------------------------- #
# Engine per-user
# --------------------------------------------------------------------- #
def build_engine(storage: Storage, user_id: str) -> FinancialEngine:
    e = FinancialEngine()
    for a in storage.list_accounts(user_id):
        acc = e.add_account(a["name"], AccountType(a["type"]),
                            starting_balance=a["starting_balance"],
                            currency=a["currency"], id=a["id"])
        if a["archived"]:
            acc.archived = True
    for r in storage.list_transactions(user_id, include_deleted=True):
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
def list_accounts(storage: Storage, user_id: str) -> List[Dict[str, Any]]:
    e = build_engine(storage, user_id)
    return [
        {"id": a.id, "name": a.name, "type": a.type.value, "balance": e.balance(a.id)}
        for a in e.accounts()
    ]


def create_account(storage: Storage, user_id: str, name: str, type: str,
                   starting_balance: int = 0) -> Dict[str, Any]:
    if not name or not str(name).strip():
        raise ValidationError("nama akun wajib diisi")
    AccountType(type)
    if not isinstance(starting_balance, int) or isinstance(starting_balance, bool):
        raise ValidationError("saldo awal harus integer")
    return storage.add_account(user_id, name.strip(), type, starting_balance)


# --------------------------------------------------------------------- #
# Parse (AI) — tidak menyimpan
# --------------------------------------------------------------------- #
def parse_text(storage: Storage, user_id: str, text: str,
               now: Optional[datetime] = None) -> Dict[str, Any]:
    e = build_engine(storage, user_id)
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
# Transaksi (commit)
# --------------------------------------------------------------------- #
def create_transaction(storage: Storage, user_id: str, f: Dict[str, Any],
                       now: Optional[datetime] = None) -> Dict[str, Any]:
    e = build_engine(storage, user_id)
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

    row = storage.add_transaction(user_id, {
        "type": tx.type.value, "amount": tx.amount,
        "occurred_at": tx.occurred_at.isoformat(),
        "from_account_id": tx.from_account_id, "to_account_id": tx.to_account_id,
        "category": tx.category, "note": tx.note, "source": tx.source,
    })
    tx.id = row["id"]
    return {
        "transaction": _tx_view(e, tx),
        "summary": _summary_from_engine(e, occurred_at.year, occurred_at.month),
    }


def list_transactions(storage: Storage, user_id: str, type: Optional[str] = None,
                      text: Optional[str] = None,
                      account_id: Optional[str] = None) -> List[Dict[str, Any]]:
    e = build_engine(storage, user_id)
    return transaction_views(e, type=type, text=text, account_id=account_id)


def delete_transaction(storage: Storage, user_id: str, tx_id: str,
                       year: Optional[int] = None,
                       month: Optional[int] = None) -> Dict[str, Any]:
    if not storage.soft_delete(user_id, tx_id):
        raise ValidationError(f"transaksi {tx_id!r} tidak ditemukan")
    e = build_engine(storage, user_id)
    now = datetime.now()
    return {"summary": _summary_from_engine(e, year or now.year, month or now.month)}


_EDIT_FIELDS = ("amount", "category", "note", "occurred_at",
                "from_account_id", "to_account_id")


def edit_transaction(storage: Storage, user_id: str, tx_id: str, fields: Dict[str, Any],
                     now: Optional[datetime] = None) -> Dict[str, Any]:
    e = build_engine(storage, user_id)
    changes: Dict[str, Any] = {k: fields[k] for k in _EDIT_FIELDS if k in fields}
    if "occurred_at" in changes:
        changes["occurred_at"] = _parse_dt(changes["occurred_at"]) or datetime.now()
    e.edit_transaction(tx_id, **changes)  # validasi
    db = dict(changes)
    if "occurred_at" in db and db["occurred_at"] is not None:
        db["occurred_at"] = db["occurred_at"].isoformat()
    if not storage.update_transaction(user_id, tx_id, db):
        raise ValidationError(f"transaksi {tx_id!r} tidak ditemukan")
    now = now or datetime.now()
    return {"summary": _summary_from_engine(build_engine(storage, user_id), now.year, now.month)}


# --------------------------------------------------------------------- #
# Pengaturan (batas, target, alert) & anggaran
# --------------------------------------------------------------------- #
def get_settings(storage: Storage, user_id: str) -> Dict[str, Any]:
    return {**DEFAULT_SETTINGS, **storage.get_settings(user_id)}


def update_settings(storage: Storage, user_id: str, patch: Dict[str, Any]) -> Dict[str, Any]:
    cur = storage.get_settings(user_id)
    for k in ("alert_threshold", "alert_email", "spending_limit",
              "income_target", "category_budgets"):
        if k in patch:
            cur[k] = patch[k]
    storage.save_settings(user_id, cur)
    return {**DEFAULT_SETTINGS, **cur}


def budget_status(storage: Storage, user_id: str,
                  ref: Optional[datetime] = None) -> Dict[str, Any]:
    return evaluate_budgets(build_engine(storage, user_id), get_settings(storage, user_id), ref)


def send_alerts(storage: Storage, user_id: str) -> Dict[str, Any]:
    cfg = get_settings(storage, user_id)
    alerts = budget_status(storage, user_id)["alerts"]
    if not alerts:
        return {"sent": False, "reason": "tidak ada alert", "alerts": []}
    email = (cfg.get("alert_email") or "").strip()
    if not email_alert.is_configured() or not email:
        return {"sent": False, "reason": "email belum dikonfigurasi", "alerts": alerts}
    body = "\n\n".join(f"{a['title']}: {a['message']}" for a in alerts)
    email_alert.send_email(email, "Peringatan Anggaran — AI Financial Assistant", body)
    return {"sent": True, "alerts": alerts}


# --------------------------------------------------------------------- #
def summary(storage: Storage, user_id: str, year: Optional[int] = None,
            month: Optional[int] = None) -> Dict[str, Any]:
    now = datetime.now()
    e = build_engine(storage, user_id)
    return _summary_from_engine(e, year or now.year, month or now.month)


def _summary_from_engine(e: FinancialEngine, year: int, month: int) -> Dict[str, Any]:
    return asdict(build_dashboard(e, year, month))


def _parse_dt(value) -> Optional[datetime]:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except (TypeError, ValueError):
        return None
