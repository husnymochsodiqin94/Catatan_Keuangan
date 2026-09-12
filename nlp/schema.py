"""Skema output parser + schema validation.

Skema ini adalah kontrak antara AI/parser dan pipeline. Structured output dari
parser mana pun (rule-based sekarang, LLM nanti) harus sesuai skema ini dan
lolos ``validate_schema`` sebelum masuk business validation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, time
from typing import List, Optional

ALLOWED_TYPES = {"income", "expense", "transfer", "refund"}
ALLOWED_CURRENCIES = {"IDR"}


@dataclass
class ParsedTransaction:
    """Satu transaksi terstruktur hasil parsing (belum tervalidasi bisnis)."""

    type: Optional[str]
    amount: Optional[int]  # rupiah (minor unit), > 0
    currency: str = "IDR"
    merchant: Optional[str] = None
    category: Optional[str] = None
    subcategory: Optional[str] = None
    account: Optional[str] = None  # untuk expense/income (nama, belum di-resolve)
    from_account: Optional[str] = None  # untuk transfer
    to_account: Optional[str] = None  # untuk transfer
    date: Optional[date] = None
    time: Optional[time] = None
    note: Optional[str] = None
    confidence: float = 0.0
    ambiguous: bool = False
    low_confidence_fields: List[str] = field(default_factory=list)


@dataclass
class ParseResult:
    """Hasil parsing sebuah input mentah (bisa berisi >1 transaksi)."""

    raw_input: str
    transactions: List[ParsedTransaction] = field(default_factory=list)
    is_transaction: bool = True
    notes: List[str] = field(default_factory=list)


def validate_schema(pt: ParsedTransaction) -> List[str]:
    """Validasi struktural (bukan bisnis). Mengembalikan daftar error; kosong = valid.

    Tidak mengecek keberadaan akun / kelengkapan (itu tugas business validation).
    Field yang belum terisi (amount/account None) BUKAN error skema — ditangani
    sebagai 'missing' di business validation.
    """
    errors: List[str] = []

    if pt.type is not None and pt.type not in ALLOWED_TYPES:
        errors.append(f"type tidak dikenal: {pt.type!r}")

    if pt.amount is not None:
        if isinstance(pt.amount, bool) or not isinstance(pt.amount, int):
            errors.append("amount harus integer (rupiah)")
        elif pt.amount <= 0:
            errors.append("amount harus > 0")

    if pt.currency not in ALLOWED_CURRENCIES:
        errors.append(f"currency tidak didukung: {pt.currency!r} (MVP: IDR)")

    if not isinstance(pt.confidence, (int, float)) or not (0.0 <= pt.confidence <= 1.0):
        errors.append("confidence harus berada di rentang [0, 1]")

    return errors
