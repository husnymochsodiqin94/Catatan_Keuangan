"""Persistensi SQLite (stdlib) untuk akun & transaksi.

Menyimpan data mentah; perhitungan (saldo/laporan) tetap dilakukan Financial
Engine. Transaksi = sumber kebenaran, saldo = turunan.
"""

from __future__ import annotations

import sqlite3
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

_SCHEMA = """
CREATE TABLE IF NOT EXISTS accounts (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    type TEXT NOT NULL,
    currency TEXT NOT NULL DEFAULT 'IDR',
    starting_balance INTEGER NOT NULL DEFAULT 0,
    archived INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS transactions (
    id TEXT PRIMARY KEY,
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
CREATE INDEX IF NOT EXISTS ix_tx_occurred ON transactions(occurred_at);
"""


class Storage:
    def __init__(self, db_path: str = "data.db"):
        # check_same_thread=False: http.server dapat memakai thread berbeda.
        self._db = sqlite3.connect(db_path, check_same_thread=False)
        self._db.row_factory = sqlite3.Row
        self._db.executescript(_SCHEMA)
        self._db.commit()

    # ---- akun ------------------------------------------------------- #
    def add_account(self, name: str, type: str, starting_balance: int = 0,
                    currency: str = "IDR") -> Dict[str, Any]:
        acc = {
            "id": "acc_" + uuid.uuid4().hex[:12], "name": name, "type": type,
            "currency": currency, "starting_balance": int(starting_balance),
            "archived": 0, "created_at": datetime.now().isoformat(timespec="seconds"),
        }
        self._db.execute(
            "INSERT INTO accounts(id,name,type,currency,starting_balance,archived,created_at)"
            " VALUES(:id,:name,:type,:currency,:starting_balance,:archived,:created_at)", acc)
        self._db.commit()
        return acc

    def list_accounts(self) -> List[Dict[str, Any]]:
        rows = self._db.execute("SELECT * FROM accounts ORDER BY created_at").fetchall()
        return [dict(r) for r in rows]

    # ---- transaksi -------------------------------------------------- #
    def add_transaction(self, tx: Dict[str, Any]) -> Dict[str, Any]:
        row = {
            "id": "tx_" + uuid.uuid4().hex[:12],
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
            "INSERT INTO transactions(id,type,amount,occurred_at,from_account_id,to_account_id,"
            "category,note,related_transaction_id,source,deleted,created_at) VALUES("
            ":id,:type,:amount,:occurred_at,:from_account_id,:to_account_id,:category,:note,"
            ":related_transaction_id,:source,:deleted,:created_at)", row)
        self._db.commit()
        return row

    def list_transactions(self, include_deleted: bool = False) -> List[Dict[str, Any]]:
        sql = "SELECT * FROM transactions"
        if not include_deleted:
            sql += " WHERE deleted=0"
        return [dict(r) for r in self._db.execute(sql).fetchall()]

    def soft_delete(self, tx_id: str) -> bool:
        cur = self._db.execute("UPDATE transactions SET deleted=1 WHERE id=?", (tx_id,))
        self._db.commit()
        return cur.rowcount > 0

    def close(self) -> None:
        self._db.close()
