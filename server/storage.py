"""Persistensi SQLite (stdlib) — multi-user.

Menyimpan pengguna, sesi, akun, transaksi, dan pengaturan; semua data keuangan
ter-scope per ``user_id``. Perhitungan tetap dilakukan Financial Engine.
"""

from __future__ import annotations

import json
import sqlite3
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

SESSION_TTL_DAYS = 30  # sesi kedaluwarsa setelah 30 hari

_SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    display_name TEXT,
    last_2fa_at TEXT,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS sessions (
    token TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS twofa_codes (
    user_id TEXT PRIMARY KEY,
    code_hash TEXT NOT NULL,
    expires_at TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS accounts (
    id TEXT PRIMARY KEY,
    user_id TEXT,
    name TEXT NOT NULL,
    type TEXT NOT NULL,
    currency TEXT NOT NULL DEFAULT 'IDR',
    starting_balance INTEGER NOT NULL DEFAULT 0,
    archived INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS transactions (
    id TEXT PRIMARY KEY,
    user_id TEXT,
    type TEXT NOT NULL,
    amount INTEGER NOT NULL,
    occurred_at TEXT NOT NULL,
    from_account_id TEXT,
    to_account_id TEXT,
    category TEXT,
    note TEXT,
    related_transaction_id TEXT,
    source TEXT NOT NULL DEFAULT 'manual',
    deleted INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS user_settings (
    user_id TEXT PRIMARY KEY,
    data TEXT NOT NULL
);
"""

# Index dibuat SETELAH _migrate() agar DB lama (yang belum punya kolom
# user_id) mendapatkan kolomnya lebih dulu.
_INDEXES = """
CREATE INDEX IF NOT EXISTS ix_tx_user ON transactions(user_id);
CREATE INDEX IF NOT EXISTS ix_acc_user ON accounts(user_id);
"""

_EDITABLE_TX = ("amount", "category", "note", "occurred_at",
                "from_account_id", "to_account_id")


class Storage:
    def __init__(self, db_path: str = "data.db"):
        self._db = sqlite3.connect(db_path, check_same_thread=False)
        self._db.row_factory = sqlite3.Row
        # WAL + busy_timeout: aman untuk akses banyak thread (ThreadingHTTPServer)
        # dan menghindari error "database is locked" saat tulis bersamaan.
        self._db.execute("PRAGMA journal_mode=WAL")
        self._db.execute("PRAGMA busy_timeout=5000")
        self._db.executescript(_SCHEMA)
        self._migrate()
        self._db.executescript(_INDEXES)
        self._db.commit()

    def _migrate(self) -> None:
        # Tambah kolom yang belum ada pada DB lama agar skema baru tetap jalan.
        # (mis. DB single-user lama belum punya user_id/archived.)
        wanted = {
            "accounts": [("user_id", "TEXT"), ("archived", "INTEGER NOT NULL DEFAULT 0")],
            "transactions": [("user_id", "TEXT")],
            "users": [("last_2fa_at", "TEXT")],
        }
        for table, columns in wanted.items():
            existing = {r["name"] for r in self._db.execute(f"PRAGMA table_info({table})")}
            for name, decl in columns:
                if name not in existing:
                    self._db.execute(f"ALTER TABLE {table} ADD COLUMN {name} {decl}")

    # ------------------------------------------------------------------ #
    # Pengguna & sesi
    # ------------------------------------------------------------------ #
    def create_user(self, email: str, password_hash: str,
                    display_name: str = "") -> Dict[str, Any]:
        user = {
            "id": "usr_" + uuid.uuid4().hex[:12], "email": email,
            "password_hash": password_hash, "display_name": display_name or email.split("@")[0],
            "created_at": datetime.now().isoformat(timespec="seconds"),
        }
        self._db.execute(
            "INSERT INTO users(id,email,password_hash,display_name,created_at)"
            " VALUES(:id,:email,:password_hash,:display_name,:created_at)", user)
        self._db.commit()
        return user

    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        row = self._db.execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()
        return dict(row) if row else None

    def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        row = self._db.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()
        return dict(row) if row else None

    def create_session(self, user_id: str) -> str:
        import secrets
        token = secrets.token_urlsafe(32)
        self._db.execute("INSERT INTO sessions(token,user_id,created_at) VALUES(?,?,?)",
                         (token, user_id, datetime.now().isoformat(timespec="seconds")))
        self._db.commit()
        return token

    def get_session_user(self, token: str) -> Optional[str]:
        if not token:
            return None
        row = self._db.execute(
            "SELECT user_id, created_at FROM sessions WHERE token=?", (token,)).fetchone()
        if not row:
            return None
        try:
            if datetime.now() - datetime.fromisoformat(row["created_at"]) > \
                    timedelta(days=SESSION_TTL_DAYS):
                self._db.execute("DELETE FROM sessions WHERE token=?", (token,))
                self._db.commit()
                return None
        except (TypeError, ValueError):
            pass
        return row["user_id"]

    def delete_session(self, token: str) -> None:
        self._db.execute("DELETE FROM sessions WHERE token=?", (token,))
        self._db.commit()

    # ---- 2FA (verifikasi email berkala) ---- #
    def set_last_2fa(self, user_id: str, ts: str) -> None:
        self._db.execute("UPDATE users SET last_2fa_at=? WHERE id=?", (ts, user_id))
        self._db.commit()

    def set_twofa(self, user_id: str, code_hash: str, expires_at: str) -> None:
        self._db.execute(
            "INSERT INTO twofa_codes(user_id,code_hash,expires_at,created_at) VALUES(?,?,?,?) "
            "ON CONFLICT(user_id) DO UPDATE SET code_hash=excluded.code_hash, "
            "expires_at=excluded.expires_at, created_at=excluded.created_at",
            (user_id, code_hash, expires_at, datetime.now().isoformat(timespec="seconds")))
        self._db.commit()

    def get_twofa(self, user_id: str) -> Optional[Dict[str, Any]]:
        row = self._db.execute(
            "SELECT * FROM twofa_codes WHERE user_id=?", (user_id,)).fetchone()
        return dict(row) if row else None

    def delete_twofa(self, user_id: str) -> None:
        self._db.execute("DELETE FROM twofa_codes WHERE user_id=?", (user_id,))
        self._db.commit()

    # ------------------------------------------------------------------ #
    # Akun (per user)
    # ------------------------------------------------------------------ #
    def add_account(self, user_id: str, name: str, type: str,
                    starting_balance: int = 0, currency: str = "IDR") -> Dict[str, Any]:
        acc = {
            "id": "acc_" + uuid.uuid4().hex[:12], "user_id": user_id, "name": name, "type": type,
            "currency": currency, "starting_balance": int(starting_balance),
            "archived": 0, "created_at": datetime.now().isoformat(timespec="seconds"),
        }
        self._db.execute(
            "INSERT INTO accounts(id,user_id,name,type,currency,starting_balance,archived,created_at)"
            " VALUES(:id,:user_id,:name,:type,:currency,:starting_balance,:archived,:created_at)", acc)
        self._db.commit()
        return acc

    def list_accounts(self, user_id: str) -> List[Dict[str, Any]]:
        rows = self._db.execute(
            "SELECT * FROM accounts WHERE user_id=? ORDER BY created_at", (user_id,)).fetchall()
        return [dict(r) for r in rows]

    def get_account(self, user_id: str, acc_id: str) -> Optional[Dict[str, Any]]:
        row = self._db.execute(
            "SELECT * FROM accounts WHERE id=? AND user_id=?", (acc_id, user_id)).fetchone()
        return dict(row) if row else None

    def update_account(self, user_id: str, acc_id: str, fields: Dict[str, Any]) -> bool:
        allowed = ("name", "type", "starting_balance", "currency", "archived")
        cols = [k for k in fields if k in allowed]
        if not cols:
            return False
        sets = ", ".join(f"{c}=?" for c in cols)
        params = [fields[c] for c in cols] + [acc_id, user_id]
        cur = self._db.execute(
            f"UPDATE accounts SET {sets} WHERE id=? AND user_id=?", params)
        self._db.commit()
        return cur.rowcount > 0

    def account_has_transactions(self, user_id: str, acc_id: str) -> bool:
        row = self._db.execute(
            "SELECT 1 FROM transactions WHERE user_id=? AND deleted=0 "
            "AND (from_account_id=? OR to_account_id=?) LIMIT 1",
            (user_id, acc_id, acc_id)).fetchone()
        return row is not None

    def reassign_transactions(self, user_id: str, old_id: str, new_id: str) -> None:
        """Pindahkan semua transaksi dari old_id ke new_id (milik user)."""
        self._db.execute(
            "UPDATE transactions SET from_account_id=? WHERE user_id=? AND from_account_id=?",
            (new_id, user_id, old_id))
        self._db.execute(
            "UPDATE transactions SET to_account_id=? WHERE user_id=? AND to_account_id=?",
            (new_id, user_id, old_id))
        # transfer yang jadi 'ke diri sendiri' (from==to) tak bermakna -> soft delete
        self._db.execute(
            "UPDATE transactions SET deleted=1 WHERE user_id=? AND type='transfer' "
            "AND from_account_id IS NOT NULL AND from_account_id=to_account_id", (user_id,))
        self._db.commit()

    def delete_account(self, user_id: str, acc_id: str) -> bool:
        cur = self._db.execute(
            "DELETE FROM accounts WHERE id=? AND user_id=?", (acc_id, user_id))
        self._db.commit()
        return cur.rowcount > 0

    # ------------------------------------------------------------------ #
    # Transaksi (per user)
    # ------------------------------------------------------------------ #
    def add_transaction(self, user_id: str, tx: Dict[str, Any]) -> Dict[str, Any]:
        row = {
            "id": "tx_" + uuid.uuid4().hex[:12], "user_id": user_id,
            "type": tx["type"], "amount": int(tx["amount"]),
            "occurred_at": tx["occurred_at"],
            "from_account_id": tx.get("from_account_id"),
            "to_account_id": tx.get("to_account_id"),
            "category": tx.get("category"), "note": tx.get("note"),
            "related_transaction_id": tx.get("related_transaction_id"),
            "source": tx.get("source", "manual"), "deleted": 0,
            "created_at": datetime.now().isoformat(timespec="seconds"),
        }
        self._db.execute(
            "INSERT INTO transactions(id,user_id,type,amount,occurred_at,from_account_id,to_account_id,"
            "category,note,related_transaction_id,source,deleted,created_at) VALUES("
            ":id,:user_id,:type,:amount,:occurred_at,:from_account_id,:to_account_id,:category,:note,"
            ":related_transaction_id,:source,:deleted,:created_at)", row)
        self._db.commit()
        return row

    def list_transactions(self, user_id: str, include_deleted: bool = False) -> List[Dict[str, Any]]:
        sql = "SELECT * FROM transactions WHERE user_id=?"
        if not include_deleted:
            sql += " AND deleted=0"
        return [dict(r) for r in self._db.execute(sql, (user_id,)).fetchall()]

    def soft_delete(self, user_id: str, tx_id: str) -> bool:
        cur = self._db.execute(
            "UPDATE transactions SET deleted=1 WHERE id=? AND user_id=?", (tx_id, user_id))
        self._db.commit()
        return cur.rowcount > 0

    def update_transaction(self, user_id: str, tx_id: str, fields: Dict[str, Any]) -> bool:
        cols = [k for k in fields if k in _EDITABLE_TX]
        if not cols:
            return False
        sets = ", ".join(f"{c}=?" for c in cols)
        params = [fields[c] for c in cols] + [tx_id, user_id]
        cur = self._db.execute(
            f"UPDATE transactions SET {sets} WHERE id=? AND user_id=?", params)
        self._db.commit()
        return cur.rowcount > 0

    # ------------------------------------------------------------------ #
    # Pengaturan (per user, JSON)
    # ------------------------------------------------------------------ #
    def get_settings(self, user_id: str) -> Dict[str, Any]:
        row = self._db.execute(
            "SELECT data FROM user_settings WHERE user_id=?", (user_id,)).fetchone()
        if not row:
            return {}
        try:
            return json.loads(row["data"])
        except (ValueError, TypeError):
            return {}

    def save_settings(self, user_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        payload = json.dumps(data, ensure_ascii=False)
        self._db.execute(
            "INSERT INTO user_settings(user_id,data) VALUES(?,?) "
            "ON CONFLICT(user_id) DO UPDATE SET data=excluded.data", (user_id, payload))
        self._db.commit()
        return data

    def close(self) -> None:
        self._db.close()
