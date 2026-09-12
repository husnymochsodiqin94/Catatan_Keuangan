"""Model data inti Financial Engine.

Nominal (`amount`) selalu berupa integer minor unit (rupiah) dan > 0.
Arah (+/-) ditentukan oleh tipe transaksi & peran akun, bukan tanda nominal.
Lihat docs/FINANCIAL_RULES.md dan docs/DATABASE_DESIGN.md.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional


class AccountType(str, Enum):
    """Tipe akun. Credit card = liability; lainnya = asset."""

    CASH = "cash"
    BANK = "bank"
    EWALLET = "ewallet"
    CREDIT_CARD = "credit_card"

    @property
    def is_liability(self) -> bool:
        return self is AccountType.CREDIT_CARD

    @property
    def is_asset(self) -> bool:
        return not self.is_liability


class TransactionType(str, Enum):
    INCOME = "income"
    EXPENSE = "expense"
    TRANSFER = "transfer"
    REFUND = "refund"
    ADJUSTMENT = "adjustment"


@dataclass
class Account:
    """Sebuah akun/sumber dana.

    Untuk akun asset, ``balance`` bermakna uang yang dimiliki.
    Untuk akun liability (credit card), ``balance`` bermakna utang terutang
    (positif = jumlah yang harus dibayar).
    """

    id: str
    name: str
    type: AccountType
    currency: str = "IDR"
    starting_balance: int = 0
    archived: bool = False


@dataclass
class Transaction:
    """Satu transaksi. Model from/to melayani semua tipe.

    Pemetaan kolom per tipe (lihat FINANCIAL_RULES.md #3):
      - income    : to_account_id  (akun asset)
      - expense   : from_account_id (asset atau credit card)
      - transfer  : from_account_id + to_account_id
      - refund    : to_account_id  (akun tujuan pengembalian; asset atau CC)
      - adjustment: to_account_id (delta +) atau from_account_id (delta -)
    """

    id: str
    type: TransactionType
    amount: int
    occurred_at: datetime
    from_account_id: Optional[str] = None
    to_account_id: Optional[str] = None
    category: Optional[str] = None
    note: Optional[str] = None
    related_transaction_id: Optional[str] = None
    source: str = "manual"
    deleted: bool = False

    def account_ids(self) -> frozenset[str]:
        """Akun yang terlibat (tanpa None) — dipakai untuk deteksi duplikat."""
        return frozenset(a for a in (self.from_account_id, self.to_account_id) if a)
