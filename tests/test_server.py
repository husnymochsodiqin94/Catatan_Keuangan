"""Tests server: auth multi-user + Storage + service (sambungan ke Engine)."""

import unittest
from datetime import datetime

from financial_engine import ValidationError
from server import service
from server.service import AuthError
from server.storage import Storage


class BaseCase(unittest.TestCase):
    def setUp(self):
        self.s = Storage(":memory:")
        reg = service.register(self.s, "dina@mail.com", "rahasia", "Dina")
        self.uid = reg["user"]["id"]
        self.token = reg["token"]
        self.bca = service.create_account(self.s, self.uid, "BCA", "bank", 5_000_000)
        self.mandiri = service.create_account(self.s, self.uid, "Mandiri", "bank", 1_000_000)

    def tearDown(self):
        self.s.close()


class TestAuth(unittest.TestCase):
    def setUp(self):
        self.s = Storage(":memory:")

    def tearDown(self):
        self.s.close()

    def test_register_login(self):
        service.register(self.s, "a@b.com", "secret1", "A")
        out = service.login(self.s, "a@b.com", "secret1")
        self.assertIn("token", out)
        self.assertEqual(out["user"]["email"], "a@b.com")

    def test_password_salah_ditolak(self):
        service.register(self.s, "a@b.com", "secret1")
        with self.assertRaises(AuthError):
            service.login(self.s, "a@b.com", "salah")

    def test_email_ganda_ditolak(self):
        service.register(self.s, "a@b.com", "secret1")
        with self.assertRaises(AuthError):
            service.register(self.s, "a@b.com", "secret2")

    def test_password_pendek_ditolak(self):
        with self.assertRaises(AuthError):
            service.register(self.s, "a@b.com", "123")

    def test_token_resolve_user(self):
        reg = service.register(self.s, "a@b.com", "secret1")
        self.assertEqual(self.s.get_session_user(reg["token"]), reg["user"]["id"])
        service.logout(self.s, reg["token"])
        self.assertIsNone(self.s.get_session_user(reg["token"]))


class TestIsolation(BaseCase):
    def test_data_terpisah_per_user(self):
        service.create_transaction(self.s, self.uid, {
            "type": "expense", "amount": 100_000, "account_id": self.bca["id"]})
        # user kedua tidak melihat akun/transaksi user pertama
        reg2 = service.register(self.s, "budi@mail.com", "rahasia2", "Budi")
        uid2 = reg2["user"]["id"]
        self.assertEqual(service.list_accounts(self.s, uid2), [])
        self.assertEqual(service.list_transactions(self.s, uid2), [])
        self.assertEqual(service.summary(self.s, uid2)["total_balance"], 0)
        # user pertama tetap punya datanya
        self.assertEqual(len(service.list_accounts(self.s, self.uid)), 2)


class TestAccounts(BaseCase):
    def test_list_dengan_saldo(self):
        accs = {a["name"]: a for a in service.list_accounts(self.s, self.uid)}
        self.assertEqual(accs["BCA"]["balance"], 5_000_000)

    def test_tipe_tidak_valid_ditolak(self):
        with self.assertRaises((ValidationError, ValueError)):
            service.create_account(self.s, self.uid, "X", "kripto", 0)


class TestAccountEditDelete(BaseCase):
    def test_update_account(self):
        service.update_account(self.s, self.uid, self.mandiri["id"],
                               {"name": "Mandiri Utama", "starting_balance": 2_000_000})
        accs = {a["name"]: a for a in service.list_accounts(self.s, self.uid)}
        self.assertIn("Mandiri Utama", accs)
        self.assertEqual(accs["Mandiri Utama"]["balance"], 2_000_000)

    def test_delete_akun_kosong(self):
        service.delete_account(self.s, self.uid, self.mandiri["id"])
        names = [a["name"] for a in service.list_accounts(self.s, self.uid)]
        self.assertNotIn("Mandiri", names)

    def test_delete_akun_bertransaksi_ditolak(self):
        service.create_transaction(self.s, self.uid, {
            "type": "expense", "amount": 10_000, "account_id": self.bca["id"]})
        with self.assertRaises(ValidationError):
            service.delete_account(self.s, self.uid, self.bca["id"])

    def test_update_akun_milik_orang_lain_ditolak(self):
        reg2 = service.register(self.s, "b@b.com", "rahasia2")
        with self.assertRaises(ValidationError):
            service.update_account(self.s, reg2["user"]["id"], self.bca["id"], {"name": "X"})

    def test_arsipkan_akun_disembunyikan_dari_transaksi(self):
        service.update_account(self.s, self.uid, self.mandiri["id"], {"archived": True})
        accs = {a["name"]: a for a in service.list_accounts(self.s, self.uid)}
        self.assertTrue(accs["Mandiri"]["archived"])
        # akun terarsip tidak boleh dipakai transaksi baru
        with self.assertRaises(ValidationError):
            service.create_transaction(self.s, self.uid, {
                "type": "expense", "amount": 10_000, "account_id": self.mandiri["id"]})
        # bisa diaktifkan kembali
        service.update_account(self.s, self.uid, self.mandiri["id"], {"archived": False})
        accs = {a["name"]: a for a in service.list_accounts(self.s, self.uid)}
        self.assertFalse(accs["Mandiri"]["archived"])

    def test_pindahkan_transaksi_lalu_hapus(self):
        service.create_transaction(self.s, self.uid, {
            "type": "expense", "amount": 100_000, "account_id": self.bca["id"],
            "occurred_at": datetime(2026, 9, 12, 10, 0).isoformat()})
        # pindahkan transaksi BCA -> Mandiri lalu hapus BCA
        service.delete_account(self.s, self.uid, self.bca["id"], move_to=self.mandiri["id"])
        names = [a["name"] for a in service.list_accounts(self.s, self.uid)]
        self.assertNotIn("BCA", names)
        # transaksi kini membebani Mandiri (5jt awal → 4jt)
        accs = {a["name"]: a for a in service.list_accounts(self.s, self.uid)}
        self.assertEqual(accs["Mandiri"]["balance"], 900_000)
        self.assertEqual(len(service.list_transactions(self.s, self.uid)), 1)

    def test_pindahkan_ke_akun_tak_dikenal_ditolak(self):
        service.create_transaction(self.s, self.uid, {
            "type": "expense", "amount": 10_000, "account_id": self.bca["id"]})
        with self.assertRaises(ValidationError):
            service.delete_account(self.s, self.uid, self.bca["id"], move_to="acc_tidak_ada")


class TestCategories(BaseCase):
    def test_listing_kategori(self):
        cats = service.list_categories()
        self.assertIn("income", cats)
        self.assertIn("expense", cats)
        names = [g["category"] for g in cats["expense"]]
        self.assertIn("Makanan & Minuman", names)
        self.assertIn("Transportasi & Mobilitas", names)
        # tiap kategori punya subkategori
        self.assertTrue(all(g["subcategories"] for g in cats["expense"]))


class TestParse(BaseCase):
    def test_parse_resolve_akun(self):
        d = service.parse_text(self.s, self.uid, "beli kopi 35 ribu pakai BCA")["drafts"][0]
        self.assertEqual(d["type"], "expense")
        self.assertEqual(d["amount"], 35_000)
        self.assertEqual(d["account_id"], self.bca["id"])
        self.assertEqual(d["status"], "ready")


class TestCommitAndPersist(BaseCase):
    def test_expense_disimpan_dan_saldo_turun(self):
        res = service.create_transaction(self.s, self.uid, {
            "type": "expense", "amount": 35_000, "account_id": self.bca["id"],
            "occurred_at": datetime(2026, 9, 12, 10, 0).isoformat()})
        self.assertEqual(res["transaction"]["amount"], 35_000)
        self.assertEqual(len(service.list_transactions(self.s, self.uid)), 1)
        summ = service.summary(self.s, self.uid, 2026, 9)
        self.assertEqual(summ["total_balance"], 5_965_000)

    def test_delete_recompute(self):
        res = service.create_transaction(self.s, self.uid, {
            "type": "expense", "amount": 100_000, "account_id": self.bca["id"],
            "occurred_at": datetime(2026, 9, 12, 10, 0).isoformat()})
        service.delete_transaction(self.s, self.uid, res["transaction"]["id"], 2026, 9)
        self.assertEqual(len(service.list_transactions(self.s, self.uid)), 0)


class TestSettingsBudgetEdit(BaseCase):
    def test_settings_roundtrip(self):
        service.update_settings(self.s, self.uid, {"alert_threshold": 80,
            "spending_limit": {"period": "monthly", "amount": 3_000_000}})
        cfg = service.get_settings(self.s, self.uid)
        self.assertEqual(cfg["alert_threshold"], 80)
        self.assertEqual(cfg["spending_limit"]["amount"], 3_000_000)

    def test_budget_status_alert(self):
        ref = datetime(2026, 9, 15, 12)
        service.create_transaction(self.s, self.uid, {"type": "expense", "amount": 2_700_000,
            "account_id": self.bca["id"], "occurred_at": datetime(2026, 9, 3, 10).isoformat()})
        service.update_settings(self.s, self.uid, {"alert_threshold": 90,
            "spending_limit": {"period": "monthly", "amount": 3_000_000}})
        st = service.budget_status(self.s, self.uid, ref)
        self.assertTrue(st["spending_limit"]["alert"])

    def test_edit_transaction(self):
        res = service.create_transaction(self.s, self.uid, {"type": "expense", "amount": 100_000,
            "account_id": self.bca["id"], "occurred_at": datetime(2026, 9, 10, 10).isoformat()})
        service.edit_transaction(self.s, self.uid, res["transaction"]["id"],
                                 {"amount": 40_000, "category": "Transport"})
        summ = service.summary(self.s, self.uid, 2026, 9)
        self.assertEqual(summ["expense"], 40_000)


if __name__ == "__main__":
    unittest.main()
