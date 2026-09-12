"""Financial Engine — operasi transaksi & perhitungan agregat.

Deterministik, tanpa I/O jaringan, tanpa AI. Menegakkan aturan pada
docs/FINANCIAL_RULES.md. Transaksi = sumber kebenaran; saldo = turunan.
"""

from __future__ import annotations

import calendar
import itertools
from datetime import datetime
from typing import Dict, List, Optional

from .models import Account, AccountType, Transaction, TransactionType


class ValidationError(ValueError):
    """Transaksi/akun melanggar aturan validasi."""


class FinancialEngine:
    def __init__(self) -> None:
        self._accounts: Dict[str, Account] = {}
        self._transactions: List[Transaction] = []
        self._acc_seq = itertools.count(1)
        self._tx_seq = itertools.count(1)

    # ------------------------------------------------------------------ #
    # Akun
    # ------------------------------------------------------------------ #
    def add_account(
        self,
        name: str,
        type: AccountType,
        starting_balance: int = 0,
        currency: str = "IDR",
        id: Optional[str] = None,
    ) -> Account:
        if not isinstance(starting_balance, int) or isinstance(starting_balance, bool):
            raise ValidationError("starting_balance harus integer")
        acc_id = id or f"acc_{next(self._acc_seq)}"
        if acc_id in self._accounts:
            raise ValidationError(f"akun dengan id {acc_id!r} sudah ada")
        account = Account(
            id=acc_id, name=name, type=type,
            currency=currency, starting_balance=starting_balance,
        )
        self._accounts[acc_id] = account
        return account

    def get_account(self, account_id: str) -> Account:
        try:
            return self._accounts[account_id]
        except KeyError:
            raise ValidationError(f"akun {account_id!r} tidak ditemukan") from None

    def accounts(self) -> List[Account]:
        return list(self._accounts.values())

    def transactions(self, include_deleted: bool = False) -> List[Transaction]:
        return [t for t in self._transactions if include_deleted or not t.deleted]

    # ------------------------------------------------------------------ #
    # Validasi
    # ------------------------------------------------------------------ #
    def _validate_amount(self, amount: int) -> None:
        if isinstance(amount, bool) or not isinstance(amount, int):
            raise ValidationError("amount harus berupa bilangan bulat (rupiah)")
        if amount <= 0:
            raise ValidationError("amount harus > 0")

    def _require_active_account(self, account_id: Optional[str], field: str) -> Account:
        if not account_id:
            raise ValidationError(f"{field} wajib diisi")
        account = self.get_account(account_id)
        if account.archived:
            raise ValidationError(f"akun {account.name!r} sudah diarsipkan")
        return account

    # ------------------------------------------------------------------ #
    # Pembuatan transaksi
    # ------------------------------------------------------------------ #
    def _add(self, tx: Transaction) -> Transaction:
        self._transactions.append(tx)
        return tx

    def _now(self, occurred_at: Optional[datetime]) -> datetime:
        return occurred_at if occurred_at is not None else datetime.now()

    def create_income(
        self, amount: int, account_id: str, category: Optional[str] = None,
        occurred_at: Optional[datetime] = None, note: Optional[str] = None,
        source: str = "manual",
    ) -> Transaction:
        self._validate_amount(amount)
        account = self._require_active_account(account_id, "account_id")
        if not account.type.is_asset:
            raise ValidationError("income harus masuk ke akun aset")
        return self._add(Transaction(
            id=f"tx_{next(self._tx_seq)}", type=TransactionType.INCOME,
            amount=amount, occurred_at=self._now(occurred_at),
            to_account_id=account_id, category=category, note=note, source=source,
        ))

    def create_expense(
        self, amount: int, account_id: str, category: Optional[str] = None,
        occurred_at: Optional[datetime] = None, note: Optional[str] = None,
        source: str = "manual",
    ) -> Transaction:
        self._validate_amount(amount)
        self._require_active_account(account_id, "account_id")
        return self._add(Transaction(
            id=f"tx_{next(self._tx_seq)}", type=TransactionType.EXPENSE,
            amount=amount, occurred_at=self._now(occurred_at),
            from_account_id=account_id, category=category, note=note, source=source,
        ))

    def create_transfer(
        self, amount: int, from_account_id: str, to_account_id: str,
        occurred_at: Optional[datetime] = None, note: Optional[str] = None,
        source: str = "manual",
    ) -> Transaction:
        self._validate_amount(amount)
        self._require_active_account(from_account_id, "from_account_id")
        self._require_active_account(to_account_id, "to_account_id")
        if from_account_id == to_account_id:
            raise ValidationError("transfer tidak boleh ke akun yang sama")
        return self._add(Transaction(
            id=f"tx_{next(self._tx_seq)}", type=TransactionType.TRANSFER,
            amount=amount, occurred_at=self._now(occurred_at),
            from_account_id=from_account_id, to_account_id=to_account_id,
            note=note, source=source,
        ))

    def create_refund(
        self, amount: int, account_id: str, related_transaction_id: Optional[str] = None,
        category: Optional[str] = None, occurred_at: Optional[datetime] = None,
        note: Optional[str] = None, source: str = "manual",
    ) -> Transaction:
        self._validate_amount(amount)
        self._require_active_account(account_id, "account_id")
        return self._add(Transaction(
            id=f"tx_{next(self._tx_seq)}", type=TransactionType.REFUND,
            amount=amount, occurred_at=self._now(occurred_at),
            to_account_id=account_id, category=category,
            related_transaction_id=related_transaction_id, note=note, source=source,
        ))

    def delete_transaction(self, tx_id: str) -> None:
        """Soft delete: transaksi dikecualikan dari saldo & laporan."""
        for tx in self._transactions:
            if tx.id == tx_id:
                tx.deleted = True
                return
        raise ValidationError(f"transaksi {tx_id!r} tidak ditemukan")

    # ------------------------------------------------------------------ #
    # Efek transaksi terhadap saldo akun
    # ------------------------------------------------------------------ #
    def _effects(self, tx: Transaction) -> Dict[str, int]:
        """Delta saldo per akun dalam makna alami akun.

        asset  : uang bertambah/berkurang.
        liability (CC): utang bertambah/berkurang.

        Aturan sisi:
          - uang MASUK ke akun (sisi 'to')  -> asset +amount, liability -amount
          - uang KELUAR dari akun (sisi 'from') -> asset -amount, liability +amount
        Refund diperlakukan sebagai uang kembali ke akun (sisi 'to'), sehingga
        pada asset menambah saldo dan pada CC menurunkan utang.
        """
        eff: Dict[str, int] = {}

        def side(account_id: Optional[str], incoming: bool) -> None:
            if not account_id:
                return
            account = self._accounts[account_id]
            if account.type.is_asset:
                delta = tx.amount if incoming else -tx.amount
            else:  # liability
                delta = -tx.amount if incoming else tx.amount
            eff[account_id] = eff.get(account_id, 0) + delta

        t = tx.type
        if t is TransactionType.INCOME:
            side(tx.to_account_id, incoming=True)
        elif t is TransactionType.EXPENSE:
            side(tx.from_account_id, incoming=False)
        elif t is TransactionType.TRANSFER:
            side(tx.from_account_id, incoming=False)
            side(tx.to_account_id, incoming=True)
        elif t is TransactionType.REFUND:
            side(tx.to_account_id, incoming=True)
        elif t is TransactionType.ADJUSTMENT:
            side(tx.to_account_id, incoming=True)
            side(tx.from_account_id, incoming=False)
        return eff

    # ------------------------------------------------------------------ #
    # Perhitungan agregat
    # ------------------------------------------------------------------ #
    def balance(self, account_id: str) -> int:
        account = self.get_account(account_id)
        total = account.starting_balance
        for tx in self._transactions:
            if tx.deleted:
                continue
            total += self._effects(tx).get(account_id, 0)
        return total

    def _all_balances(self) -> Dict[str, int]:
        """Saldo semua akun dalam SATU kali pindai transaksi (hindari rescan per-akun)."""
        totals = {aid: acc.starting_balance for aid, acc in self._accounts.items()}
        for tx in self._transactions:
            if tx.deleted:
                continue
            for aid, delta in self._effects(tx).items():
                totals[aid] = totals.get(aid, 0) + delta
        return totals

    def total_assets(self) -> int:
        balances = self._all_balances()
        return sum(balances[a.id] for a in self._accounts.values() if a.type.is_asset)

    def total_liabilities(self) -> int:
        balances = self._all_balances()
        return sum(balances[a.id] for a in self._accounts.values() if a.type.is_liability)

    def net_worth(self) -> int:
        balances = self._all_balances()
        worth = 0
        for a in self._accounts.values():
            worth += balances[a.id] if a.type.is_asset else -balances[a.id]
        return worth

    def cash_flow(
        self, start: Optional[datetime] = None, end: Optional[datetime] = None
    ) -> Dict[str, int]:
        """Ringkasan cash flow periode. Transfer & adjustment dikecualikan."""
        income = expense = refund = 0
        for tx in self._transactions:
            if tx.deleted:
                continue
            if start is not None and tx.occurred_at < start:
                continue
            if end is not None and tx.occurred_at > end:
                continue
            if tx.type is TransactionType.INCOME:
                income += tx.amount
            elif tx.type is TransactionType.EXPENSE:
                expense += tx.amount
            elif tx.type is TransactionType.REFUND:
                refund += tx.amount
        net_expense = expense - refund
        return {
            "income": income,
            "expense": expense,
            "refund": refund,
            "net_expense": net_expense,
            "net_cash_flow": income - net_expense,
        }

    def month_summary(self, year: int, month: int) -> Dict[str, object]:
        """Ringkasan cash flow untuk satu bulan (sumber angka dashboard)."""
        start = datetime(year, month, 1, 0, 0, 0)
        last_day = calendar.monthrange(year, month)[1]
        end = datetime(year, month, last_day, 23, 59, 59, 999999)
        cf = self.cash_flow(start, end)
        return {"year": year, "month": month, "start": start, "end": end, **cf}

    def expense_by_category(
        self, start: Optional[datetime] = None, end: Optional[datetime] = None
    ) -> Dict[str, int]:
        """Total pengeluaran neto per kategori (expense − refund). Hanya net > 0."""
        totals: Dict[str, int] = {}
        for tx in self._transactions:
            if tx.deleted:
                continue
            if start is not None and tx.occurred_at < start:
                continue
            if end is not None and tx.occurred_at > end:
                continue
            if tx.type is TransactionType.EXPENSE:
                key = tx.category or "Lainnya"
                totals[key] = totals.get(key, 0) + tx.amount
            elif tx.type is TransactionType.REFUND:
                key = tx.category or "Lainnya"
                totals[key] = totals.get(key, 0) - tx.amount
        return {k: v for k, v in totals.items() if v > 0}

    # ------------------------------------------------------------------ #
    # Query & edit (dipakai Transaction History; satu sumber kebenaran)
    # ------------------------------------------------------------------ #
    def _get_tx(self, tx_id: str) -> Transaction:
        for tx in self._transactions:
            if tx.id == tx_id:
                return tx
        raise ValidationError(f"transaksi {tx_id!r} tidak ditemukan")

    def query_transactions(
        self, type: Optional[object] = None, account_id: Optional[str] = None,
        start: Optional[datetime] = None, end: Optional[datetime] = None,
        text: Optional[str] = None, include_deleted: bool = False,
    ) -> List[Transaction]:
        """Filter + search transaksi. Mengembalikan terbaru dulu."""
        want_type = TransactionType(type) if isinstance(type, str) else type
        needle = text.lower().strip() if text else None
        res: List[Transaction] = []
        for tx in self._transactions:
            if not include_deleted and tx.deleted:
                continue
            if want_type is not None and tx.type is not want_type:
                continue
            if account_id is not None and account_id not in tx.account_ids():
                continue
            if start is not None and tx.occurred_at < start:
                continue
            if end is not None and tx.occurred_at > end:
                continue
            if needle:
                hay = " ".join(x for x in (tx.category, tx.note) if x).lower()
                if needle not in hay:
                    continue
            res.append(tx)
        res.sort(key=lambda t: t.occurred_at, reverse=True)
        return res

    def recent_transactions(self, limit: int = 5) -> List[Transaction]:
        return self.query_transactions()[:limit]

    def edit_transaction(self, tx_id: str, **changes) -> Transaction:
        """Edit transaksi; saldo/laporan otomatis konsisten (saldo = turunan)."""
        tx = self._get_tx(tx_id)
        allowed = {"amount", "category", "note", "occurred_at",
                   "from_account_id", "to_account_id"}
        unknown = set(changes) - allowed
        if unknown:
            raise ValidationError(f"field tidak dapat diedit: {sorted(unknown)}")
        # validasi nilai prospektif sebelum diterapkan
        self._validate_amount(changes.get("amount", tx.amount))
        for fld in ("from_account_id", "to_account_id"):
            if changes.get(fld) is not None and fld in changes:
                self._require_active_account(changes[fld], fld)
        p_from = changes.get("from_account_id", tx.from_account_id)
        p_to = changes.get("to_account_id", tx.to_account_id)
        if tx.type is TransactionType.TRANSFER and p_from == p_to:
            raise ValidationError("transfer tidak boleh ke akun yang sama")
        for key, value in changes.items():
            setattr(tx, key, value)
        return tx

    # ------------------------------------------------------------------ #
    # Deteksi duplikat (menandai, tidak memblokir)
    # ------------------------------------------------------------------ #
    def find_duplicates(
        self, tx: Transaction, window_seconds: int = 120
    ) -> List[Transaction]:
        """Kandidat duplikat: tipe + amount + akun terlibat sama, dalam jendela waktu.

        Tidak memblokir/menggabungkan — hanya mengembalikan kandidat untuk
        dikonfirmasi pengguna (FINANCIAL_RULES.md #15).
        """
        candidates: List[Transaction] = []
        target_accounts = tx.account_ids()
        for other in self._transactions:
            if other is tx or other.id == tx.id or other.deleted:
                continue
            if other.type is not tx.type or other.amount != tx.amount:
                continue
            if other.account_ids() != target_accounts:
                continue
            if abs((other.occurred_at - tx.occurred_at).total_seconds()) <= window_seconds:
                candidates.append(other)
        return candidates
