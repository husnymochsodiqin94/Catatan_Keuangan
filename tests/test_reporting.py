"""Tests reporting: angka dashboard bersumber dari Financial Engine + query/edit."""

import unittest
from datetime import datetime

from financial_engine import AccountType, FinancialEngine
from reporting import build_dashboard, transaction_views


class BaseCase(unittest.TestCase):
    def setUp(self):
        self.e = FinancialEngine()
        self.bca = self.e.add_account("BCA", AccountType.BANK, starting_balance=5_000_000)
        self.cash = self.e.add_account("Cash", AccountType.CASH, starting_balance=200_000)

        def dt(day):
            return datetime(2026, 9, day, 10, 0, 0)

        self.e.create_income(8_000_000, self.bca.id, category="Gaji", occurred_at=dt(1))
        self.e.create_expense(35_000, self.bca.id, category="Makanan & Minuman", occurred_at=dt(2))
        self.e.create_expense(50_000, self.bca.id, category="Makanan & Minuman", occurred_at=dt(3))
        self.e.create_expense(100_000, self.bca.id, category="Transport", occurred_at=dt(4))
        self.e.create_refund(20_000, self.bca.id, category="Transport", occurred_at=dt(5))


class TestDashboardFromEngine(BaseCase):
    def test_angka_dashboard_sama_dengan_engine(self):
        d = build_dashboard(self.e, 2026, 9)
        ms = self.e.month_summary(2026, 9)
        self.assertEqual(d.total_balance, self.e.net_worth())
        self.assertEqual(d.income, ms["income"])
        self.assertEqual(d.expense, ms["expense"])
        self.assertEqual(d.net_cash_flow, ms["net_cash_flow"])

    def test_expense_by_category_neto(self):
        d = build_dashboard(self.e, 2026, 9)
        cats = {c["category"]: c["amount"] for c in d.expense_by_category}
        self.assertEqual(cats["Makanan & Minuman"], 85_000)
        self.assertEqual(cats["Transport"], 80_000)  # 100.000 − refund 20.000

    def test_expense_by_category_terurut_desc(self):
        d = build_dashboard(self.e, 2026, 9)
        amounts = [c["amount"] for c in d.expense_by_category]
        self.assertEqual(amounts, sorted(amounts, reverse=True))

    def test_recent_terbaru_dulu(self):
        d = build_dashboard(self.e, 2026, 9)
        dates = [r["date"] for r in d.recent]
        self.assertEqual(dates, sorted(dates, reverse=True))


class TestHistoryQuery(BaseCase):
    def test_filter_by_type(self):
        rows = transaction_views(self.e, type="expense")
        self.assertTrue(all(r["type"] == "expense" for r in rows))
        self.assertEqual(len(rows), 3)

    def test_search_text(self):
        rows = transaction_views(self.e, text="transport")
        self.assertTrue(len(rows) >= 1)
        self.assertTrue(all("Transport" in (r["category"] or "") for r in rows))

    def test_filter_by_account(self):
        rows = transaction_views(self.e, account_id=self.cash.id)
        self.assertEqual(rows, [])  # tidak ada transaksi Cash


class TestEditDelete(BaseCase):
    def test_edit_amount_memengaruhi_saldo(self):
        tx = self.e.query_transactions(type="expense")[-1]  # transaksi paling awal
        before = self.e.balance(self.bca.id)
        self.e.edit_transaction(tx.id, amount=tx.amount + 10_000)
        self.assertEqual(self.e.balance(self.bca.id), before - 10_000)

    def test_delete_memengaruhi_dashboard(self):
        tx = self.e.query_transactions(type="expense", text="Transport")[0]
        self.e.delete_transaction(tx.id)
        d = build_dashboard(self.e, 2026, 9)
        cats = {c["category"]: c["amount"] for c in d.expense_by_category}
        # transport expense terhapus; refund 20.000 membuat net negatif -> disaring
        self.assertNotIn("Transport", cats)


if __name__ == "__main__":
    unittest.main()
