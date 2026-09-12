"""Automated tests untuk Financial Engine.

Sumber kebenaran: docs/FINANCIAL_RULES.md. Kode TC merujuk ke bagian
"TEST CASES" pada dokumen tersebut.
"""

import unittest
from datetime import datetime, timedelta

from financial_engine import AccountType, FinancialEngine, ValidationError
from financial_engine.models import Transaction, TransactionType


class BaseCase(unittest.TestCase):
    def setUp(self):
        self.e = FinancialEngine()
        self.bca = self.e.add_account("BCA", AccountType.BANK, starting_balance=5_000_000)
        self.mandiri = self.e.add_account("Mandiri", AccountType.BANK, starting_balance=1_000_000)
        self.cash = self.e.add_account("Cash", AccountType.CASH, starting_balance=200_000)
        self.gopay = self.e.add_account("GoPay", AccountType.EWALLET, starting_balance=0)
        self.cc = self.e.add_account("Visa", AccountType.CREDIT_CARD, starting_balance=0)


class TestIncome(BaseCase):
    def test_income_menambah_saldo(self):  # TC-02
        self.e.create_income(8_000_000, self.bca.id, category="Gaji")
        self.assertEqual(self.e.balance(self.bca.id), 13_000_000)

    def test_income_ke_liability_ditolak(self):
        with self.assertRaises(ValidationError):
            self.e.create_income(100_000, self.cc.id)


class TestExpense(BaseCase):
    def test_expense_dari_asset_mengurangi_saldo(self):  # TC-01
        self.e.create_expense(35_000, self.bca.id, category="Kopi")
        self.assertEqual(self.e.balance(self.bca.id), 4_965_000)

    def test_expense_hanya_mempengaruhi_akun_terkait(self):
        self.e.create_expense(35_000, self.bca.id)
        self.assertEqual(self.e.balance(self.mandiri.id), 1_000_000)


class TestTransfer(BaseCase):
    def test_transfer_netral_terhadap_total_asset(self):  # TC-03
        assets_before = self.e.total_assets()
        cf_before = self.e.cash_flow()
        self.e.create_transfer(2_000_000, self.bca.id, self.mandiri.id)
        self.assertEqual(self.e.balance(self.bca.id), 3_000_000)
        self.assertEqual(self.e.balance(self.mandiri.id), 3_000_000)
        self.assertEqual(self.e.total_assets(), assets_before)  # total asset tetap
        cf = self.e.cash_flow()
        self.assertEqual(cf["income"], cf_before["income"])
        self.assertEqual(cf["expense"], cf_before["expense"])

    def test_transfer_ke_akun_sama_ditolak(self):  # TC-04
        with self.assertRaises(ValidationError):
            self.e.create_transfer(1_000, self.bca.id, self.bca.id)

    def test_topup_ewallet_adalah_transfer(self):
        self.e.create_transfer(100_000, self.bca.id, self.gopay.id)
        self.assertEqual(self.e.balance(self.bca.id), 4_900_000)
        self.assertEqual(self.e.balance(self.gopay.id), 100_000)
        self.assertEqual(self.e.cash_flow()["expense"], 0)


class TestRefund(BaseCase):
    def test_refund_ke_asset_menambah_saldo_dan_mengurangi_net_expense(self):  # TC-10, TC-11
        self.e.create_expense(300_000, self.bca.id, category="Belanja")
        self.e.create_refund(300_000, self.bca.id, category="Belanja")
        self.assertEqual(self.e.balance(self.bca.id), 5_000_000)  # kembali seperti semula
        cf = self.e.cash_flow()
        self.assertEqual(cf["expense"], 300_000)
        self.assertEqual(cf["refund"], 300_000)
        self.assertEqual(cf["net_expense"], 0)  # contra-expense, bukan income
        self.assertEqual(cf["income"], 0)

    def test_refund_bukan_income(self):
        self.e.create_refund(50_000, self.bca.id)
        self.assertEqual(self.e.cash_flow()["income"], 0)

    def test_refund_ke_credit_card_menurunkan_utang(self):  # TC-12
        self.e.create_expense(1_000_000, self.cc.id, category="Belanja")
        self.assertEqual(self.e.balance(self.cc.id), 1_000_000)  # utang
        self.e.create_refund(400_000, self.cc.id)
        self.assertEqual(self.e.balance(self.cc.id), 600_000)  # utang turun


class TestBalanceAndMultipleAccounts(BaseCase):
    def test_starting_balance(self):
        self.assertEqual(self.e.balance(self.bca.id), 5_000_000)
        self.assertEqual(self.e.total_assets(), 6_200_000)  # BCA+Mandiri+Cash+GoPay
        self.assertEqual(self.e.net_worth(), 6_200_000)

    def test_soft_delete_menghitung_ulang(self):  # TC-17
        tx = self.e.create_expense(100_000, self.bca.id)
        self.assertEqual(self.e.balance(self.bca.id), 4_900_000)
        self.e.delete_transaction(tx.id)
        self.assertEqual(self.e.balance(self.bca.id), 5_000_000)


class TestCreditCard(BaseCase):
    def test_belanja_cc_adalah_expense_dan_menaikkan_utang(self):  # TC-05
        self.e.create_expense(10_000_000, self.cc.id, category="Elektronik")
        self.assertEqual(self.e.balance(self.cc.id), 10_000_000)  # utang naik
        self.assertEqual(self.e.balance(self.bca.id), 5_000_000)  # asset tak berubah
        self.assertEqual(self.e.cash_flow()["expense"], 10_000_000)

    def test_bayar_cc_bukan_expense(self):  # TC-06
        self.e.create_expense(10_000_000, self.cc.id, category="Elektronik")
        self.e.create_transfer(10_000_000, self.bca.id, self.cc.id)  # bayar CC
        self.assertEqual(self.e.balance(self.cc.id), 0)  # utang lunas
        self.assertEqual(self.e.balance(self.bca.id), -5_000_000)
        self.assertEqual(self.e.cash_flow()["expense"], 10_000_000)  # tetap 10jt, bukan 20jt

    def test_net_worth_turun_sekali_bukan_dua_kali(self):  # TC-07
        nw_before = self.e.net_worth()
        self.e.create_expense(10_000_000, self.cc.id, category="Elektronik")
        self.assertEqual(self.e.net_worth(), nw_before - 10_000_000)  # setelah beli
        self.e.create_transfer(10_000_000, self.bca.id, self.cc.id)  # bayar CC
        self.assertEqual(self.e.net_worth(), nw_before - 10_000_000)  # bayar CC netral


class TestScenarioFinancialRules(BaseCase):
    """Reproduksi contoh kumulatif E1..E7 di FINANCIAL_RULES.md.

    Catatan: E8 (adjustment) sengaja tidak diuji karena adjustment di luar
    lingkup task ini. Karena itu Net Worth di sini 4.465.000 (tanpa koreksi
    Cash -50.000), sedangkan Net Cash Flow tetap -1.735.000 (adjustment memang
    tidak mempengaruhi cash flow).
    """

    def test_kumulatif(self):
        self.e.create_expense(35_000, self.bca.id, category="Kopi")            # E1
        self.e.create_income(8_000_000, self.bca.id, category="Gaji")          # E2
        self.e.create_transfer(2_000_000, self.bca.id, self.mandiri.id)        # E3
        self.e.create_transfer(100_000, self.bca.id, self.gopay.id)            # E4
        self.e.create_expense(10_000_000, self.cc.id, category="Elektronik")   # E5
        self.e.create_transfer(10_000_000, self.bca.id, self.cc.id)            # E6
        self.e.create_refund(300_000, self.bca.id, category="Belanja")         # E7

        self.assertEqual(self.e.balance(self.bca.id), 1_165_000)
        self.assertEqual(self.e.balance(self.mandiri.id), 3_000_000)
        self.assertEqual(self.e.balance(self.gopay.id), 100_000)
        self.assertEqual(self.e.balance(self.cc.id), 0)
        self.assertEqual(self.e.net_worth(), 4_465_000)
        self.assertEqual(self.e.cash_flow()["net_cash_flow"], -1_735_000)


class TestValidation(BaseCase):
    def test_amount_nol_ditolak(self):  # TC-21
        with self.assertRaises(ValidationError):
            self.e.create_expense(0, self.bca.id)

    def test_amount_negatif_ditolak(self):  # TC-21
        with self.assertRaises(ValidationError):
            self.e.create_expense(-100, self.bca.id)

    def test_amount_bukan_int_ditolak(self):
        with self.assertRaises(ValidationError):
            self.e.create_expense(35_000.5, self.bca.id)

    def test_akun_tidak_dikenal_ditolak(self):
        with self.assertRaises(ValidationError):
            self.e.create_expense(1_000, "acc_tidak_ada")


class TestDuplicate(BaseCase):
    def _base_time(self):
        return datetime(2026, 9, 12, 10, 0, 0)

    def test_kandidat_duplikat_dalam_jendela(self):  # TC-18
        t = self._base_time()
        self.e.create_expense(35_000, self.bca.id, occurred_at=t)
        dup = self.e.create_expense(35_000, self.bca.id, occurred_at=t + timedelta(seconds=30))
        self.assertEqual(len(self.e.find_duplicates(dup)), 1)

    def test_di_luar_jendela_bukan_duplikat(self):  # TC-19
        t = self._base_time()
        self.e.create_expense(35_000, self.bca.id, occurred_at=t)
        dup = self.e.create_expense(35_000, self.bca.id, occurred_at=t + timedelta(seconds=300))
        self.assertEqual(len(self.e.find_duplicates(dup)), 0)

    def test_amount_beda_bukan_duplikat(self):
        t = self._base_time()
        self.e.create_expense(35_000, self.bca.id, occurred_at=t)
        other = self.e.create_expense(40_000, self.bca.id, occurred_at=t + timedelta(seconds=10))
        self.assertEqual(len(self.e.find_duplicates(other)), 0)

    def test_duplikat_dikonfirmasi_tetap_tersimpan(self):  # TC-20
        t = self._base_time()
        self.e.create_expense(35_000, self.bca.id, occurred_at=t)
        dup = self.e.create_expense(35_000, self.bca.id, occurred_at=t + timedelta(seconds=30))
        self.assertGreater(len(self.e.find_duplicates(dup)), 0)  # ditandai
        self.assertEqual(len(self.e.transactions()), 2)  # tetap tersimpan (tidak diblokir)


if __name__ == "__main__":
    unittest.main()
