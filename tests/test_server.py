"""Tests server: Storage + service (sambungan ke Financial Engine)."""

import unittest
from datetime import datetime

from financial_engine import ValidationError
from server import service
from server.storage import Storage


class BaseCase(unittest.TestCase):
    def setUp(self):
        self.s = Storage(":memory:")
        self.bca = service.create_account(self.s, "BCA", "bank", 5_000_000)
        self.mandiri = service.create_account(self.s, "Mandiri", "bank", 1_000_000)

    def tearDown(self):
        self.s.close()


class TestAccounts(BaseCase):
    def test_list_dengan_saldo(self):
        accs = {a["name"]: a for a in service.list_accounts(self.s)}
        self.assertEqual(accs["BCA"]["balance"], 5_000_000)
        self.assertEqual(accs["BCA"]["type"], "bank")

    def test_tipe_tidak_valid_ditolak(self):
        with self.assertRaises((ValidationError, ValueError)):
            service.create_account(self.s, "X", "kripto", 0)


class TestParse(BaseCase):
    def test_parse_resolve_akun(self):
        out = service.parse_text(self.s, "beli kopi 35 ribu pakai BCA")
        d = out["drafts"][0]
        self.assertEqual(d["type"], "expense")
        self.assertEqual(d["amount"], 35_000)
        self.assertEqual(d["account_id"], self.bca["id"])
        self.assertEqual(d["status"], "ready")


class TestCommitAndPersist(BaseCase):
    def test_expense_disimpan_dan_saldo_turun(self):
        res = service.create_transaction(self.s, {
            "type": "expense", "amount": 35_000, "account_id": self.bca["id"],
            "category": "Makanan & Minuman",
            "occurred_at": datetime(2026, 9, 12, 10, 0).isoformat(),
        })
        self.assertEqual(res["transaction"]["amount"], 35_000)
        # tersimpan
        self.assertEqual(len(service.list_transactions(self.s)), 1)
        # saldo turun (via summary → engine)
        summ = service.summary(self.s, 2026, 9)
        self.assertEqual(summ["total_balance"], 5_965_000)  # 6.000.000 − 35.000
        self.assertEqual(summ["expense"], 35_000)

    def test_transfer_netral(self):
        service.create_transaction(self.s, {
            "type": "transfer", "amount": 2_000_000,
            "from_account_id": self.bca["id"], "to_account_id": self.mandiri["id"],
            "occurred_at": datetime(2026, 9, 12, 10, 0).isoformat(),
        })
        summ = service.summary(self.s, 2026, 9)
        self.assertEqual(summ["total_balance"], 6_000_000)  # tak berubah
        self.assertEqual(summ["expense"], 0)

    def test_amount_invalid_ditolak(self):
        with self.assertRaises(ValidationError):
            service.create_transaction(self.s, {
                "type": "expense", "amount": 0, "account_id": self.bca["id"]})

    def test_delete_recompute(self):
        res = service.create_transaction(self.s, {
            "type": "expense", "amount": 100_000, "account_id": self.bca["id"],
            "occurred_at": datetime(2026, 9, 12, 10, 0).isoformat()})
        tx_id = res["transaction"]["id"]
        service.delete_transaction(self.s, tx_id, 2026, 9)
        summ = service.summary(self.s, 2026, 9)
        self.assertEqual(summ["total_balance"], 6_000_000)  # kembali
        self.assertEqual(len(service.list_transactions(self.s)), 0)


class TestSummaryPersistence(BaseCase):
    def test_data_bertahan_lintas_koneksi_ulang(self):
        service.create_transaction(self.s, {
            "type": "income", "amount": 8_000_000, "account_id": self.bca["id"],
            "category": "Gaji", "occurred_at": datetime(2026, 9, 1, 9, 0).isoformat()})
        # rehidrasi engine baru dari storage yang sama
        summ = service.summary(self.s, 2026, 9)
        self.assertEqual(summ["income"], 8_000_000)
        self.assertEqual(summ["total_balance"], 14_000_000)


if __name__ == "__main__":
    unittest.main()
