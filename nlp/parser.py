"""Parser bahasa natural -> ParsedTransaction.

``TransactionParser`` = antarmuka. ``RuleBasedParser`` = implementasi
deterministik berbasis aturan (Indonesia), tanpa dependency/LLM. Adapter LLM
di masa depan cukup mengimplementasikan ``parse``.
"""

from __future__ import annotations

import re
from datetime import date, time, timedelta
from typing import List, Optional, Protocol, Tuple

from . import taxonomy
from .schema import ParsedTransaction, ParseResult


class TransactionParser(Protocol):
    def parse(self, text: str, today: Optional[date] = None) -> ParseResult:
        ...


# --- Kamus aturan (ringkas; dapat diperluas / kelak digantikan model) --------

# nama akun yang dikenal -> label tampilan
ACCOUNTS = {
    "bca": "BCA", "mandiri": "Mandiri", "bni": "BNI", "bri": "BRI",
    "gopay": "GoPay", "ovo": "OVO", "dana": "Dana", "shopeepay": "ShopeePay",
    "cash": "Cash", "tunai": "Cash",
}

# Pemetaan kategori/subkategori berbasis keyword: lihat ``nlp/taxonomy.py``
# (sumber kebenaran tunggal untuk listing & deteksi).

INCOME_KEYWORDS = ("gaji", "gajian", "terima", "diterima", "bonus", "pemasukan", "thr")
EXPENSE_VERBS = ("beli", "bayar", "belanja", "jajan", "keluar")
TRANSFER_KEYWORDS = ("transfer", "pindah", "kirim", "top up", "topup", "tf")
REFUND_KEYWORDS = ("refund", "pengembalian", "dikembalikan", "retur")

# Pemisah multi-transaksi. "lalu" dikecualikan bila bagian dari "hari lalu" (frasa tanggal).
SPLIT_RE = re.compile(r"\s*(?:,|;|\bdan\b|\bkemudian\b|\bterus\b|(?<!hari )\blalu\b)\s+")


class RuleBasedParser:
    """Parser deterministik untuk bahasa Indonesia informal."""

    def parse(self, text: str, today: Optional[date] = None) -> ParseResult:
        today = today or date.today()
        raw = (text or "").strip()
        result = ParseResult(raw_input=raw)
        if not raw:
            result.is_transaction = False
            result.notes.append("input kosong")
            return result

        segments = self._split_segments(raw)
        any_tx = False
        for seg in segments:
            pt = self._parse_segment(seg, today)
            # segmen dianggap transaksi bila ada nominal atau ada sinyal finansial
            if pt.amount is not None or pt.type is not None:
                any_tx = True
                result.transactions.append(pt)

        if not any_tx:
            result.is_transaction = False
            result.notes.append("tidak terdeteksi transaksi (tidak ada nominal/kata kunci)")
        return result

    # ------------------------------------------------------------------ #
    def _split_segments(self, raw: str) -> List[str]:
        parts = [p.strip() for p in SPLIT_RE.split(raw) if p.strip()]
        return parts or [raw]

    def _parse_segment(self, seg: str, today: date) -> ParsedTransaction:
        low = seg.lower()
        pt = ParsedTransaction(type=None, amount=self._parse_amount(low))

        # tanggal & waktu
        pt.date = self._parse_date(low, today)
        pt.time = self._parse_time(low)

        # kategori
        cat = self._match_category(low)
        if cat:
            pt.category, pt.subcategory = cat

        # tipe transaksi + akun
        cat_type = taxonomy.type_of(pt.category)  # 'income'/'expense'/None dari listing
        type_signal = "none"
        if self._has_kw(low, TRANSFER_KEYWORDS) or self._has_dari_ke(low):
            pt.type = "transfer"
            pt.from_account, pt.to_account = self._parse_transfer_accounts(low)
            type_signal = "verb"
        elif self._has_kw(low, REFUND_KEYWORDS):
            pt.type = "refund"
            pt.account = self._first_account(low)
            type_signal = "verb"
        elif self._has_kw(low, INCOME_KEYWORDS) or cat_type == "income":
            pt.type = "income"
            pt.account = self._first_account(low)
            type_signal = "verb" if self._has_kw(low, INCOME_KEYWORDS) else "category"
        elif self._has_kw(low, EXPENSE_VERBS):
            pt.type = "expense"
            pt.account = self._first_account(low)
            type_signal = "verb"
        elif pt.category is not None:
            # ada kategori (pengeluaran) tanpa kata kerja -> tebak expense (conf lebih rendah)
            pt.type = "expense"
            pt.account = self._first_account(low)
            type_signal = "category"
        else:
            # tak ada sinyal tipe -> ambigu (tebak expense bila ada nominal)
            pt.type = "expense" if pt.amount is not None else None
            pt.account = self._first_account(low)
            pt.ambiguous = True

        pt.merchant = self._parse_merchant(low)
        pt.note = seg
        self._score(pt, type_signal)
        return pt

    # ------------------------------------------------------------------ #
    # Nominal Indonesia
    # ------------------------------------------------------------------ #
    # frasa waktu yang mengandung angka -> jangan dianggap nominal
    _TEMPORAL_RE = re.compile(
        r"\d+\s*hari\s*(?:yang\s*)?lalu|kemarin\s*lusa|kemarin|besok|"
        r"(?:jam|pukul)\s*\d{1,2}(?:[.:]\d{2})?"
    )

    def _parse_amount(self, low: str) -> Optional[int]:
        # buang token waktu dulu agar angka tanggal/jam tak salah jadi nominal
        low = self._TEMPORAL_RE.sub(" ", low)
        m = re.search(r"(\d+(?:[.,]\d+)?)\s*(?:juta|jt)\b", low)
        if m:
            return int(round(self._to_float(m.group(1)) * 1_000_000))
        m = re.search(r"(\d+(?:[.,]\d+)?)\s*(?:ribu|rb|k)\b", low)
        if m:
            return int(round(self._to_float(m.group(1)) * 1_000))
        # angka dengan pemisah ribuan: 35.000 atau 1.250.000
        m = re.search(r"\b(\d{1,3}(?:\.\d{3})+)\b", low)
        if m:
            return int(m.group(1).replace(".", ""))
        # angka polos
        m = re.search(r"\b(\d+)\b", low)
        if m:
            return int(m.group(1))
        return None

    @staticmethod
    def _to_float(num: str) -> float:
        # "1,5" -> 1.5 ; "1.5" -> 1.5
        return float(num.replace(".", "").replace(",", ".")) if "," in num else float(num)

    # ------------------------------------------------------------------ #
    # Tanggal & waktu natural
    # ------------------------------------------------------------------ #
    def _parse_date(self, low: str, today: date) -> date:
        m = re.search(r"(\d+)\s*hari\s*(?:yang\s*)?lalu", low)
        if m:
            return today - timedelta(days=int(m.group(1)))
        if "kemarin lusa" in low:
            return today - timedelta(days=2)
        if "kemarin" in low:
            return today - timedelta(days=1)
        if "besok" in low:
            return today + timedelta(days=1)
        return today  # default: hari ini

    def _parse_time(self, low: str) -> Optional[time]:
        m = re.search(r"(?:jam|pukul)\s*(\d{1,2})(?:[.:](\d{2}))?", low)
        if m:
            hh = int(m.group(1))
            mm = int(m.group(2)) if m.group(2) else 0
            if 0 <= hh <= 23 and 0 <= mm <= 59:
                return time(hh, mm)
        return None

    # ------------------------------------------------------------------ #
    # Kategori, akun, merchant
    # ------------------------------------------------------------------ #
    def _match_category(self, low: str) -> Optional[Tuple[str, Optional[str]]]:
        return taxonomy.match(low)

    def _first_account(self, low: str) -> Optional[str]:
        for kw, label in ACCOUNTS.items():
            if re.search(rf"\b{re.escape(kw)}\b", low):
                return label
        return None

    @staticmethod
    def _has_kw(low: str, keywords) -> bool:
        # Cocokkan per-kata (bukan substring) agar mis. "tf" tak cocok dgn "neTFlix".
        return any(re.search(rf"\b{re.escape(k)}\b", low) for k in keywords)

    def _has_dari_ke(self, low: str) -> bool:
        return bool(re.search(r"\bdari\b.*\bke\b", low))

    def _parse_transfer_accounts(self, low: str) -> Tuple[Optional[str], Optional[str]]:
        frm = to = None
        m = re.search(r"\bdari\s+([a-z]+)", low)
        if m:
            frm = ACCOUNTS.get(m.group(1))
        m = re.search(r"\bke\s+([a-z]+)", low)
        if m:
            to = ACCOUNTS.get(m.group(1))
        # "top up gopay dari bca" -> to = gopay (akun non-dari/ke)
        if to is None:
            for kw, label in ACCOUNTS.items():
                if re.search(rf"\b{re.escape(kw)}\b", low) and label != frm:
                    to = label
                    break
        return frm, to

    def _parse_merchant(self, low: str) -> Optional[str]:
        m = re.search(r"\bdi\s+([a-z0-9]+)", low)
        if m and m.group(1) not in ACCOUNTS:
            return m.group(1)
        return None

    # ------------------------------------------------------------------ #
    def _score(self, pt: ParsedTransaction, type_signal: str) -> None:
        conf = 0.0
        low_fields: List[str] = []
        if type_signal == "verb":
            conf += 0.40
        elif type_signal == "category":
            conf += 0.25
        else:
            low_fields.append("type")
        if pt.amount is not None:
            conf += 0.30
        else:
            low_fields.append("amount")
        if pt.category is not None:
            conf += 0.15
        else:
            low_fields.append("category")
        has_account = pt.account or pt.from_account or pt.to_account
        if has_account:
            conf += 0.15
        else:
            low_fields.append("account")
        pt.confidence = round(min(conf, 1.0), 2)
        pt.low_confidence_fields = low_fields
