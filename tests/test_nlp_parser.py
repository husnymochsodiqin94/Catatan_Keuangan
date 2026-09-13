"""Automated tests untuk AI Transaction Parser (rule-based) + pipeline.

Menguji alur: Natural Language -> ParsedTransaction -> schema validation ->
business validation -> (Financial Engine). Output parser tidak pernah langsung
disimpan; commit selalu eksplisit.
"""

import unittest
from datetime import date, datetime, timedelta

from financial_engine import AccountType, FinancialEngine
from nlp import ParsePipeline, PipelineError, RuleBasedParser, validate_schema
from nlp.pipeline import AMBIGUOUS, INCOMPLETE, NOT_TRANSACTION, READY


class BaseCase(unittest.TestCase):
    def setUp(self):
        self.e = FinancialEngine()
        self.bca = self.e.add_account("BCA", AccountType.BANK, starting_balance=5_000_000)
        self.mandiri = self.e.add_account("Mandiri", AccountType.BANK, starting_balance=1_000_000)
        self.gopay = self.e.add_account("GoPay", AccountType.EWALLET, starting_balance=0)
        self.pipe = ParsePipeline(self.e)
        self.parser = RuleBasedParser()


class TestExpense(BaseCase):
    def test_expense(self):
        drafts = self.pipe.process("beli kopi 35 ribu pakai BCA")
        self.assertEqual(len(drafts), 1)
        d = drafts[0]
        self.assertEqual(d.parsed.type, "expense")
        self.assertEqual(d.parsed.amount, 35_000)
        self.assertEqual(d.parsed.currency, "IDR")
        self.assertEqual(d.parsed.category, "Makanan & Minuman")
        self.assertEqual(d.parsed.subcategory, "Restoran & Cafe")
        self.assertEqual(d.account_id, self.bca.id)
        self.assertEqual(d.status, READY)
        self.assertGreaterEqual(d.parsed.confidence, 0.8)
        # output belum tersimpan sampai commit
        self.assertEqual(len(self.e.transactions()), 0)
        self.pipe.commit(d)
        self.assertEqual(self.e.balance(self.bca.id), 4_965_000)


class TestIncome(BaseCase):
    def test_income(self):
        d = self.pipe.process("gajian 8 juta masuk BCA")[0]
        self.assertEqual(d.parsed.type, "income")
        self.assertEqual(d.parsed.amount, 8_000_000)
        self.assertEqual(d.account_id, self.bca.id)
        self.assertEqual(d.status, READY)
        self.pipe.commit(d)
        self.assertEqual(self.e.balance(self.bca.id), 13_000_000)


class TestTransfer(BaseCase):
    def test_transfer(self):
        d = self.pipe.process("transfer 2 juta dari BCA ke Mandiri")[0]
        self.assertEqual(d.parsed.type, "transfer")
        self.assertEqual(d.parsed.amount, 2_000_000)
        self.assertEqual(d.from_account_id, self.bca.id)
        self.assertEqual(d.to_account_id, self.mandiri.id)
        self.assertEqual(d.status, READY)
        self.pipe.commit(d)
        self.assertEqual(self.e.balance(self.bca.id), 3_000_000)
        self.assertEqual(self.e.balance(self.mandiri.id), 3_000_000)


class TestMultipleTransaction(BaseCase):
    def test_multiple(self):
        drafts = self.pipe.process("beli kopi 35 ribu dan parkir 5 ribu")
        self.assertEqual(len(drafts), 2)
        self.assertEqual(drafts[0].parsed.amount, 35_000)
        self.assertEqual(drafts[0].parsed.type, "expense")
        self.assertEqual(drafts[1].parsed.amount, 5_000)
        self.assertEqual(drafts[1].parsed.type, "expense")
        self.assertEqual(drafts[1].parsed.category, "Transportasi & Mobilitas")


class TestNaturalDate(BaseCase):
    def test_kemarin(self):
        now = datetime(2026, 9, 12, 10, 0, 0)
        d = self.pipe.process("beli kopi 35 ribu pakai BCA kemarin", now=now)[0]
        self.assertEqual(d.parsed.date, date(2026, 9, 11))
        self.assertEqual(d.occurred_at.date(), date(2026, 9, 11))

    def test_n_hari_lalu(self):
        now = datetime(2026, 9, 12, 10, 0, 0)
        d = self.pipe.process("bayar listrik 100 ribu pakai BCA 3 hari lalu", now=now)[0]
        self.assertEqual(d.parsed.date, date(2026, 9, 9))

    def test_default_hari_ini(self):
        now = datetime(2026, 9, 12, 10, 0, 0)
        d = self.pipe.process("beli kopi 35 ribu pakai BCA", now=now)[0]
        self.assertEqual(d.parsed.date, date(2026, 9, 12))


class TestIndonesianNominal(BaseCase):
    def test_variasi_nominal(self):
        cases = {
            "beli kopi 35 ribu pakai BCA": 35_000,
            "beli kopi 35rb pakai BCA": 35_000,
            "beli kopi 35k pakai BCA": 35_000,
            "beli laptop 10 juta pakai BCA": 10_000_000,
            "beli hp 1,5 juta pakai BCA": 1_500_000,
            "beli makan 25.000 pakai BCA": 25_000,
            "belanja 1.250.000 pakai BCA": 1_250_000,
        }
        for text, expected in cases.items():
            with self.subTest(text=text):
                d = self.pipe.process(text)[0]
                self.assertEqual(d.parsed.amount, expected)


class TestTemporalNotAmount(BaseCase):
    """Regresi audit: angka pada frasa waktu tidak boleh dibaca sebagai nominal."""

    def test_n_hari_lalu_bukan_nominal(self):
        now = datetime(2026, 9, 12, 10, 0, 0)
        d = self.pipe.process("makan 3 hari lalu pakai BCA", now=now)[0]
        self.assertIsNone(d.parsed.amount)  # "3" bukan nominal
        self.assertEqual(d.parsed.date, date(2026, 9, 9))
        self.assertIn("amount", d.missing)

    def test_jam_bukan_nominal(self):
        d = self.pipe.process("beli kopi jam 9 pakai BCA")[0]
        self.assertIsNone(d.parsed.amount)

    def test_nominal_tetap_terbaca_dengan_frasa_waktu(self):
        now = datetime(2026, 9, 12, 10, 0, 0)
        d = self.pipe.process("bayar listrik 100 ribu pakai BCA 3 hari lalu", now=now)[0]
        self.assertEqual(d.parsed.amount, 100_000)
        self.assertEqual(d.parsed.date, date(2026, 9, 9))


class TestMissingAccount(BaseCase):
    def test_missing_account(self):
        d = self.pipe.process("beli kopi 35 ribu")[0]
        self.assertEqual(d.parsed.type, "expense")
        self.assertEqual(d.parsed.amount, 35_000)
        self.assertIsNone(d.account_id)
        self.assertIn("account", d.missing)
        self.assertEqual(d.status, INCOMPLETE)
        # tidak boleh bisa di-commit selagi belum lengkap
        with self.assertRaises(PipelineError):
            self.pipe.commit(d)

    def test_default_account_melengkapi(self):
        d = self.pipe.process("beli kopi 35 ribu", default_account_id=self.bca.id)[0]
        self.assertEqual(d.account_id, self.bca.id)
        self.assertEqual(d.status, READY)


class TestAmbiguous(BaseCase):
    def test_amount_only_ambiguous(self):
        d = self.pipe.process("40 ribu")[0]
        self.assertTrue(d.parsed.ambiguous)
        self.assertEqual(d.status, AMBIGUOUS)
        self.assertIn("type", d.parsed.low_confidence_fields)
        with self.assertRaises(PipelineError):
            self.pipe.commit(d)

    def test_bukan_transaksi(self):
        drafts = self.pipe.process("halo apa kabar")
        self.assertEqual(drafts[0].status, NOT_TRANSACTION)


class TestCorrection(BaseCase):
    def test_correction_melengkapi_dan_commit(self):
        d = self.pipe.process("beli kopi 35 ribu")[0]
        self.assertEqual(d.status, INCOMPLETE)  # akun belum ada
        self.pipe.apply_correction(d, account="BCA")
        self.assertEqual(d.account_id, self.bca.id)
        self.assertEqual(d.status, READY)
        self.pipe.commit(d)
        self.assertEqual(self.e.balance(self.bca.id), 4_965_000)

    def test_correction_amount(self):
        d = self.pipe.process("beli kopi 35 ribu pakai BCA")[0]
        self.pipe.apply_correction(d, amount=40_000)
        self.assertEqual(d.parsed.amount, 40_000)
        self.assertEqual(d.status, READY)

    def test_correction_menghapus_ambiguous(self):
        d = self.pipe.process("40 ribu")[0]
        self.assertEqual(d.status, AMBIGUOUS)
        self.pipe.apply_correction(d, type="income", account="BCA")
        self.assertFalse(d.parsed.ambiguous)
        self.assertEqual(d.status, READY)


class TestDuplicate(BaseCase):
    def test_duplicate_ditandai_tidak_diblokir(self):  # FINANCIAL_RULES #15
        now = datetime(2026, 9, 12, 10, 0, 0)
        d1 = self.pipe.process("beli kopi 35 ribu pakai BCA", now=now)[0]
        self.pipe.commit(d1)
        d2 = self.pipe.process("beli kopi 35 ribu pakai BCA", now=now + timedelta(seconds=30))[0]
        self.assertEqual(d2.status, READY)
        self.assertEqual(len(d2.duplicates), 1)  # ditandai
        # commit default tetap boleh (konfirmasi pengguna), atau bisa ditolak
        with self.assertRaises(PipelineError):
            self.pipe.commit(d2, allow_duplicate=False)
        self.pipe.commit(d2)  # dikonfirmasi -> tersimpan
        self.assertEqual(len(self.e.transactions()), 2)


class TestSchemaValidation(BaseCase):
    def test_output_lolos_schema(self):
        for d in self.pipe.process("beli kopi 35 ribu pakai BCA"):
            self.assertEqual(validate_schema(d.parsed), [])


class TestTaksonomi(BaseCase):
    def test_kategori_dari_taksonomi(self):
        cases = {
            "beli sepatu lari 500rb pakai BCA":
                ("expense", "Kesehatan & Olahraga", "Peralatan Olahraga & Apparel"),
            "isi pertamax 100rb pakai BCA":
                ("expense", "Transportasi & Mobilitas", "BBM & Bahan Bakar"),
            "bayar parkir 5rb pakai BCA":
                ("expense", "Transportasi & Mobilitas", "Parkir & Tol"),
        }
        for text, (typ, cat, sub) in cases.items():
            r = self.parser.parse(text).transactions[0]
            self.assertEqual((r.type, r.category, r.subcategory), (typ, cat, sub), text)

    def test_langganan_bukan_transfer(self):  # regresi: "tf" di "neTFlix"
        r = self.parser.parse("langganan netflix 186rb pakai BCA").transactions[0]
        self.assertEqual(r.type, "expense")
        self.assertEqual(r.category, "Tagihan & Utilitas")

    def test_kategori_pemasukan_menentukan_tipe_income(self):
        r = self.parser.parse("dividen saham 1 juta masuk BCA").transactions[0]
        self.assertEqual(r.type, "income")
        self.assertEqual(r.category, "Pemasukan Pasif & Investasi")


if __name__ == "__main__":
    unittest.main()
