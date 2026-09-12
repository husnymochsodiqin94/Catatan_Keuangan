"""Pipeline: input -> parse -> schema validation -> business validation.

Menghasilkan ``Draft`` tervalidasi yang SIAP dikirim ke Financial Engine, tetapi
TIDAK menyimpan apa pun secara otomatis. Penyimpanan hanya terjadi lewat
``commit(draft)`` yang eksplisit (mensimulasikan konfirmasi pengguna).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional

from financial_engine import FinancialEngine, Transaction, TransactionType

from .parser import RuleBasedParser, TransactionParser
from .schema import ParsedTransaction, validate_schema

# Status draft
READY = "ready"
INCOMPLETE = "incomplete"
AMBIGUOUS = "ambiguous"
NOT_TRANSACTION = "not_transaction"
INVALID = "invalid"


class PipelineError(ValueError):
    """Operasi pipeline tidak valid (mis. commit draft yang belum ready)."""


@dataclass
class Draft:
    parsed: ParsedTransaction
    occurred_at: datetime
    status: str = INCOMPLETE
    missing: List[str] = field(default_factory=list)
    schema_errors: List[str] = field(default_factory=list)
    account_id: Optional[str] = None
    from_account_id: Optional[str] = None
    to_account_id: Optional[str] = None
    duplicates: List[Transaction] = field(default_factory=list)

    @property
    def is_ready(self) -> bool:
        return self.status == READY


class ParsePipeline:
    def __init__(self, engine: FinancialEngine, parser: Optional[TransactionParser] = None):
        self.engine = engine
        self.parser = parser or RuleBasedParser()

    # ------------------------------------------------------------------ #
    def process(
        self, text: str, now: Optional[datetime] = None,
        default_account_id: Optional[str] = None,
    ) -> List[Draft]:
        now = now or datetime.now()
        result = self.parser.parse(text, today=now.date())
        drafts: List[Draft] = []

        if not result.is_transaction:
            drafts.append(Draft(
                parsed=ParsedTransaction(type=None, amount=None),
                occurred_at=now, status=NOT_TRANSACTION,
            ))
            return drafts

        for pt in result.transactions:
            occurred_at = self._combine(pt, now)
            draft = Draft(parsed=pt, occurred_at=occurred_at)
            # 1) schema validation
            draft.schema_errors = validate_schema(pt)
            if draft.schema_errors:
                draft.status = INVALID
                drafts.append(draft)
                continue
            # 2) business validation
            self._business_validate(draft, default_account_id)
            drafts.append(draft)
        return drafts

    # ------------------------------------------------------------------ #
    def _business_validate(self, draft: Draft, default_account_id: Optional[str]) -> None:
        pt = draft.parsed
        missing: List[str] = []

        if pt.amount is None:
            missing.append("amount")

        if pt.type == "transfer":
            draft.from_account_id = self._resolve(pt.from_account)
            draft.to_account_id = self._resolve(pt.to_account)
            if not draft.from_account_id:
                missing.append("from_account")
            if not draft.to_account_id:
                missing.append("to_account")
            if (draft.from_account_id and draft.to_account_id
                    and draft.from_account_id == draft.to_account_id):
                missing.append("distinct_accounts")
        else:  # expense / income / refund
            draft.account_id = self._resolve(pt.account) or default_account_id
            if not draft.account_id:
                missing.append("account")

        draft.missing = missing

        # penetapan status (prioritas: missing amount > ambiguous > missing account)
        if "amount" in missing:
            draft.status = INCOMPLETE
        elif pt.ambiguous:
            draft.status = AMBIGUOUS
        elif missing:
            draft.status = INCOMPLETE
        else:
            draft.status = READY
            draft.duplicates = self._detect_duplicates(draft)

    # ------------------------------------------------------------------ #
    def apply_correction(self, draft: Draft, default_account_id: Optional[str] = None,
                         **changes) -> Draft:
        """Terapkan koreksi pengguna ke draft lalu validasi ulang.

        Field yang bisa dikoreksi: type, amount, account, from_account,
        to_account, category, subcategory, date, time, note. Koreksi manual
        menghapus flag ambiguous.
        """
        pt = draft.parsed
        for key, value in changes.items():
            if not hasattr(pt, key):
                raise PipelineError(f"field koreksi tidak dikenal: {key!r}")
            setattr(pt, key, value)
        if "type" in changes or any(k in changes for k in ("account", "from_account", "to_account", "amount")):
            pt.ambiguous = False
        draft.schema_errors = validate_schema(pt)
        if draft.schema_errors:
            draft.status = INVALID
            return draft
        draft.occurred_at = self._combine(pt, draft.occurred_at)
        self._business_validate(draft, default_account_id)
        return draft

    # ------------------------------------------------------------------ #
    def commit(self, draft: Draft, allow_duplicate: bool = True) -> Transaction:
        """Kirim draft ke Financial Engine. Hanya untuk draft berstatus READY.

        Inilah satu-satunya titik penulisan; parser tidak pernah menulis sendiri.
        """
        if not draft.is_ready:
            raise PipelineError(f"draft belum siap disimpan (status={draft.status})")
        if draft.duplicates and not allow_duplicate:
            raise PipelineError("draft ditandai kemungkinan duplikat; perlu konfirmasi")
        pt = draft.parsed
        if pt.type == "expense":
            return self.engine.create_expense(pt.amount, draft.account_id,
                                              category=pt.category, occurred_at=draft.occurred_at, source="text")
        if pt.type == "income":
            return self.engine.create_income(pt.amount, draft.account_id,
                                             category=pt.category, occurred_at=draft.occurred_at, source="text")
        if pt.type == "transfer":
            return self.engine.create_transfer(pt.amount, draft.from_account_id, draft.to_account_id,
                                               occurred_at=draft.occurred_at, source="text")
        if pt.type == "refund":
            return self.engine.create_refund(pt.amount, draft.account_id,
                                             category=pt.category, occurred_at=draft.occurred_at, source="text")
        raise PipelineError(f"tipe transaksi tidak didukung: {pt.type!r}")

    # ------------------------------------------------------------------ #
    def _resolve(self, name: Optional[str]) -> Optional[str]:
        if not name:
            return None
        target = name.strip().lower()
        for acc in self.engine.accounts():
            if acc.name.lower() == target:
                return acc.id
        for acc in self.engine.accounts():
            if target in acc.name.lower() or acc.name.lower() in target:
                return acc.id
        return None

    def _detect_duplicates(self, draft: Draft) -> List[Transaction]:
        pt = draft.parsed
        candidate = Transaction(
            id="__candidate__",
            type=TransactionType(pt.type),
            amount=pt.amount,
            occurred_at=draft.occurred_at,
            from_account_id=draft.from_account_id if pt.type == "transfer" else (
                draft.account_id if pt.type in ("expense",) else None),
            to_account_id=draft.to_account_id if pt.type == "transfer" else (
                draft.account_id if pt.type in ("income", "refund") else None),
        )
        return self.engine.find_duplicates(candidate)

    def _combine(self, pt: ParsedTransaction, now: datetime) -> datetime:
        d = pt.date or now.date()
        t = pt.time or now.time()
        return datetime.combine(d, t)
