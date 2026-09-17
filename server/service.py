"""Service: Storage + Financial Engine + NLP + Reporting, multi-user.

Setiap operasi data ter-scope ``user_id``. Merehidrasi FinancialEngine dari data
milik user, memakai engine untuk validasi & perhitungan, lalu menyimpan hasilnya.
Tidak ada logika finansial yang diduplikasi di sini.
"""

from __future__ import annotations

import os
import re
import threading
from dataclasses import asdict
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from financial_engine import (
    AccountType,
    FinancialEngine,
    Transaction,
    TransactionType,
    ValidationError,
)
from financial_engine.budgeting import evaluate as evaluate_budgets
from nlp import ParsePipeline, taxonomy
from reporting.dashboard import _tx_view, build_dashboard, transaction_views

from . import auth, email_alert
from .storage import Storage

DEFAULT_SETTINGS: Dict[str, Any] = {
    "alert_threshold": 90, "alert_email": "",
    "spending_limit": None, "income_target": None, "category_budgets": [],
}
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

TWOFA_INTERVAL_DAYS = 14      # verifikasi email diminta paling sering per 14 hari
TWOFA_CODE_TTL_MIN = 10       # kode OTP berlaku 10 menit
DUPLICATE_WINDOW_SEC = 300    # proteksi duplikat: 5 menit

# Rate limit anti brute-force (in-memory, cukup untuk 1 proses server).
MAX_LOGIN_ATTEMPTS = 8
LOGIN_WINDOW_MIN = 15
_ATTEMPTS: Dict[str, list] = {}          # key -> [gagal, waktu_pertama]
_ATTEMPTS_LOCK = threading.Lock()


class AuthError(ValueError):
    """Kredensial/registrasi tidak valid."""


def _rate_check(key: str, now: datetime) -> None:
    """Blokir sementara bila terlalu banyak percobaan gagal dalam jendela waktu."""
    with _ATTEMPTS_LOCK:
        rec = _ATTEMPTS.get(key)
        if rec and (now - rec[1]) <= timedelta(minutes=LOGIN_WINDOW_MIN):
            if rec[0] >= MAX_LOGIN_ATTEMPTS:
                raise AuthError("Terlalu banyak percobaan. Coba lagi dalam beberapa menit.")


def _rate_fail(key: str, now: datetime) -> None:
    with _ATTEMPTS_LOCK:
        rec = _ATTEMPTS.get(key)
        if not rec or (now - rec[1]) > timedelta(minutes=LOGIN_WINDOW_MIN):
            _ATTEMPTS[key] = [1, now]
        else:
            rec[0] += 1


def _rate_reset(key: str) -> None:
    with _ATTEMPTS_LOCK:
        _ATTEMPTS.pop(key, None)


def _rp(n: int) -> str:
    return "Rp" + format(int(n or 0), ",d").replace(",", ".")


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
    # baru daftar = dianggap terverifikasi, tak langsung diminta 2FA
    storage.set_last_2fa(user["id"], datetime.now().isoformat(timespec="seconds"))
    token = storage.create_session(user["id"])
    return {"token": token, "user": _public_user(user)}


def _twofa_fresh(user: Dict[str, Any], now: datetime) -> bool:
    last = user.get("last_2fa_at")
    if not last:
        return False
    try:
        return (now - datetime.fromisoformat(last)) <= timedelta(days=TWOFA_INTERVAL_DAYS)
    except (TypeError, ValueError):
        return False


def _mask_email(email: str) -> str:
    name, _, dom = email.partition("@")
    head = name[:2] if len(name) > 2 else name[:1]
    return f"{head}{'*' * max(1, len(name) - len(head))}@{dom}"


def _issue_twofa(storage: Storage, user: Dict[str, Any],
                 now: datetime) -> Optional[Dict[str, Any]]:
    """Buat & kirim kode OTP; kembalikan payload 'twofa_required' (tanpa token).

    Mengembalikan None bila kode tak dapat dikirim (SMTP belum dikonfigurasi &
    bukan mode dev) — pemanggil lalu melewati 2FA (tak membocorkan kode). Kode
    hanya ditampilkan di respons bila env ``CATATAN_2FA_DEV`` diaktifkan.
    """
    dev = bool(os.environ.get("CATATAN_2FA_DEV"))
    configured = email_alert.is_configured()
    if not configured and not dev:
        print(f"[2FA] SMTP belum dikonfigurasi; 2FA dilewati untuk {user['email']}")
        return None
    code = auth.new_otp()
    expires = (now + timedelta(minutes=TWOFA_CODE_TTL_MIN)).isoformat(timespec="seconds")
    storage.set_twofa(user["id"], auth.hash_otp(code), expires)
    out: Dict[str, Any] = {
        "twofa_required": True, "email": _mask_email(user["email"]),
        "expires_in_min": TWOFA_CODE_TTL_MIN,
    }
    subject = "Kode Verifikasi Masuk — AI Financial Assistant"
    body = (f"Kode verifikasi masuk Anda: {code}\n"
            f"Berlaku {TWOFA_CODE_TTL_MIN} menit. Abaikan bila ini bukan Anda.")
    if configured:
        try:
            email_alert.send_email(user["email"], subject, body)
            out["email_sent"] = True
        except Exception:
            out["email_sent"] = False
            if dev:
                out["dev_code"] = code
            else:
                storage.delete_twofa(user["id"])
                return None  # gagal kirim & bukan dev -> lewati 2FA, jangan bocor
    else:  # mode dev tanpa SMTP: tampilkan kode untuk uji lokal
        print(f"[2FA] kode dev untuk {user['email']}: {code}")
        out["email_sent"] = False
        out["dev_code"] = code
    return out


def login(storage: Storage, email: str, password: str,
          now: Optional[datetime] = None) -> Dict[str, Any]:
    now = now or datetime.now()
    email = (email or "").strip().lower()
    _rate_check(email, now)
    user = storage.get_user_by_email(email)
    if not user or not auth.verify_password(password or "", user["password_hash"]):
        _rate_fail(email, now)
        raise AuthError("email atau kata sandi salah")
    _rate_reset(email)
    if not _twofa_fresh(user, now):
        chal = _issue_twofa(storage, user, now)
        if chal is not None:
            return chal
        # tak dapat mengirim 2FA -> masuk dengan password saja
    token = storage.create_session(user["id"])
    return {"token": token, "user": _public_user(user)}


def verify_twofa(storage: Storage, email: str, code: str,
                 now: Optional[datetime] = None) -> Dict[str, Any]:
    now = now or datetime.now()
    email = (email or "").strip().lower()
    key = email + ":2fa"
    _rate_check(key, now)
    user = storage.get_user_by_email(email)
    if not user:
        _rate_fail(key, now)
        raise AuthError("pengguna tidak ditemukan")
    rec = storage.get_twofa(user["id"])
    if not rec:
        raise AuthError("kode tidak ditemukan, silakan masuk ulang")
    try:
        expired = datetime.fromisoformat(rec["expires_at"]) < now
    except (TypeError, ValueError):
        expired = True
    if expired:
        storage.delete_twofa(user["id"])
        raise AuthError("kode kedaluwarsa, silakan masuk ulang")
    if not auth.verify_otp((code or "").strip(), rec["code_hash"]):
        _rate_fail(key, now)
        raise AuthError("kode salah")
    _rate_reset(key)
    storage.delete_twofa(user["id"])
    storage.set_last_2fa(user["id"], now.isoformat(timespec="seconds"))
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
        {"id": a.id, "name": a.name, "type": a.type.value,
         "balance": e.balance(a.id), "starting_balance": a.starting_balance,
         "archived": bool(a.archived)}
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


def update_account(storage: Storage, user_id: str, acc_id: str,
                   fields: Dict[str, Any]) -> Dict[str, Any]:
    if not storage.get_account(user_id, acc_id):
        raise ValidationError("akun tidak ditemukan")
    patch: Dict[str, Any] = {}
    if "name" in fields:
        name = (fields["name"] or "").strip()
        if not name:
            raise ValidationError("nama akun wajib diisi")
        patch["name"] = name
    if "type" in fields:
        AccountType(fields["type"])  # validasi
        patch["type"] = fields["type"]
    if "starting_balance" in fields:
        sb = fields["starting_balance"]
        if not isinstance(sb, int) or isinstance(sb, bool):
            raise ValidationError("saldo awal harus integer")
        patch["starting_balance"] = sb
    if "archived" in fields:
        patch["archived"] = 1 if fields["archived"] else 0
    storage.update_account(user_id, acc_id, patch)
    e = build_engine(storage, user_id)
    a = storage.get_account(user_id, acc_id)
    return {"id": a["id"], "name": a["name"], "type": a["type"],
            "balance": e.balance(acc_id), "archived": bool(a["archived"])}


def delete_account(storage: Storage, user_id: str, acc_id: str,
                   move_to: Optional[str] = None) -> Dict[str, Any]:
    if not storage.get_account(user_id, acc_id):
        raise ValidationError("akun tidak ditemukan")
    if move_to:
        if move_to == acc_id:
            raise ValidationError("akun tujuan harus berbeda")
        if not storage.get_account(user_id, move_to):
            raise ValidationError("akun tujuan tidak ditemukan")
        storage.reassign_transactions(user_id, acc_id, move_to)
    elif storage.account_has_transactions(user_id, acc_id):
        raise ValidationError(
            "Akun masih punya transaksi — pindahkan transaksinya dulu atau arsipkan.")
    storage.delete_account(user_id, acc_id)
    return {"ok": True}


# --------------------------------------------------------------------- #
# Kategori (listing taksonomi — sumber kebenaran di nlp/taxonomy.py)
# --------------------------------------------------------------------- #
def list_categories() -> Dict[str, Any]:
    return taxonomy.grouped()


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

    # Proteksi duplikat: nominal+akun sama & kategori identik dalam <=5 menit.
    if not f.get("allow_duplicate"):
        dups = [d for d in e.find_duplicates(tx, DUPLICATE_WINDOW_SEC)
                if (d.category or None) == (tx.category or None)]
        if dups:
            recent = max(dups, key=lambda d: d.occurred_at)
            return {"duplicate": {
                "amount": tx.amount, "category": tx.category,
                "occurred_at": recent.occurred_at.isoformat(),
                "message": (f"Transaksi {_rp(tx.amount)}"
                            f"{' — ' + tx.category if tx.category else ''} baru saja dicatat. "
                            "Apakah ini transaksi baru?"),
            }}

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
# Laporan (Insight) — tren bulanan + rincian kategori, dari engine
# --------------------------------------------------------------------- #
_MONTH_ID = ["", "Jan", "Feb", "Mar", "Apr", "Mei", "Jun",
             "Jul", "Agu", "Sep", "Okt", "Nov", "Des"]


def reports(storage: Storage, user_id: str, months: int = 6,
            ref: Optional[datetime] = None) -> Dict[str, Any]:
    """Tren income/expense/net beberapa bulan + rincian kategori bulan ref."""
    e = build_engine(storage, user_id)
    ref = ref or datetime.now()
    months = max(1, min(int(months or 6), 24))
    trend: List[Dict[str, Any]] = []
    y, m = ref.year, ref.month
    seq = []
    for _ in range(months):
        seq.append((y, m))
        m -= 1
        if m == 0:
            m = 12; y -= 1
    for (yy, mm) in reversed(seq):
        cf = e.month_summary(yy, mm)
        trend.append({
            "year": yy, "month": mm, "label": f"{_MONTH_ID[mm]} {str(yy)[2:]}",
            "income": cf["income"], "expense": cf["net_expense"],
            "net": cf["net_cash_flow"],
        })
    cur = e.month_summary(ref.year, ref.month)
    by = e.expense_by_category(cur["start"], cur["end"])
    categories = sorted(({"category": k, "amount": v} for k, v in by.items()),
                        key=lambda c: c["amount"], reverse=True)
    total_exp = sum(c["amount"] for c in categories) or 1
    for c in categories:
        c["pct"] = round(c["amount"] / total_exp * 100)
    # rata-rata pengeluaran bulanan (dari tren, abaikan bulan tanpa data)
    exp_months = [t["expense"] for t in trend if t["expense"] > 0]
    avg_expense = int(sum(exp_months) / len(exp_months)) if exp_months else 0
    return {"trend": trend, "categories": categories,
            "month_label": f"{_MONTH_ID[ref.month]} {ref.year}",
            "avg_expense": avg_expense}


def export_csv(storage: Storage, user_id: str) -> str:
    """Ekspor seluruh transaksi user sebagai CSV (untuk unduh)."""
    import csv
    import io
    e = build_engine(storage, user_id)
    rows = transaction_views(e)
    rows.sort(key=lambda r: r["date"], reverse=True)
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["tanggal", "jenis", "kategori", "akun", "nominal", "catatan"])
    label = {"income": "Pemasukan", "expense": "Pengeluaran",
             "transfer": "Transfer", "refund": "Refund"}
    for r in rows:
        w.writerow([r["date"], label.get(r["type"], r["type"]), r.get("category") or "",
                    r.get("account") or "", r["amount"], r.get("note") or ""])
    return buf.getvalue()


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
