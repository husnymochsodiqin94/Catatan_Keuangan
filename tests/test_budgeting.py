"""Tests evaluasi anggaran/batas/target/alert (deterministik)."""

import unittest
from datetime import datetime

from financial_engine import AccountType, FinancialEngine
from financial_engine.budgeting import evaluate, period_bounds


class TestPeriodBounds(unittest.TestCase):
    def test_monthly(self):
        s, e = period_bounds("monthly", datetime(2026, 9, 15, 12))
        self.assertEqual(s, datetime(2026, 9, 1, 0, 0, 0))
        self.assertEqual(e.day, 30)

    def test_weekly_senin_ke_minggu(self):
        # 2026-09-15 = Selasa → minggu Senin 14 s/d Minggu 20
        s, e = period_bounds("weekly", datetime(2026, 9, 15, 12))
        self.assertEqual(s.day, 14)
        self.assertEqual(e.day, 20)

    def test_daily(self):
        s, e = period_bounds("daily", datetime(2026, 9, 15, 12))
        self.assertEqual((s.day, e.day), (15, 15))


class TestEvaluate(unittest.TestCase):
    def setUp(self):
        self.e = FinancialEngine()
        self.bca = self.e.add_account("BCA", AccountType.BANK, starting_balance=10_000_000)
        self.ref = datetime(2026, 9, 15, 12)

        def dt(day):
            return datetime(2026, 9, day, 10)

        self.e.create_income(8_000_000, self.bca.id, occurred_at=dt(1))
        self.e.create_expense(1_500_000, self.bca.id, category="Transport", occurred_at=dt(4))
        self.e.create_expense(1_200_000, self.bca.id, category="Makanan & Minuman", occurred_at=dt(5))

    def test_spending_limit_alert_90(self):
        out = evaluate(self.e, {"alert_threshold": 90,
                                "spending_limit": {"period": "monthly", "amount": 3_000_000}}, self.ref)
        sl = out["spending_limit"]
        self.assertEqual(sl["used"], 2_700_000)
        self.assertEqual(sl["pct"], 90)
        self.assertTrue(sl["alert"])
        self.assertFalse(sl["over"])
        self.assertTrue(any(a["kind"] == "spending_limit" for a in out["alerts"]))

    def test_income_target_progress(self):
        out = evaluate(self.e, {"income_target": {"period": "monthly", "amount": 10_000_000}}, self.ref)
        it = out["income_target"]
        self.assertEqual(it["achieved"], 8_000_000)
        self.assertEqual(it["pct"], 80)

    def test_category_over_dan_ok(self):
        out = evaluate(self.e, {"alert_threshold": 90, "category_budgets": [
            {"category": "Transport", "amount": 1_200_000},          # over (1.5jt)
            {"category": "Makanan & Minuman", "amount": 5_000_000},   # ok (1.2jt = 24%)
        ]}, self.ref)
        cats = {c["category"]: c for c in out["categories"]}
        self.assertEqual(cats["Transport"]["status"], "over")
        self.assertEqual(cats["Makanan & Minuman"]["status"], "ok")
        self.assertTrue(any(a["kind"] == "category" and a["level"] == "over" for a in out["alerts"]))

    def test_tanpa_konfigurasi_tanpa_alert(self):
        out = evaluate(self.e, {}, self.ref)
        self.assertEqual(out["alerts"], [])
        self.assertIsNone(out["spending_limit"])
        self.assertIsNone(out["safe_to_spend"])

    def test_safe_to_spend_harian(self):
        # batas 3jt, terpakai 2.7jt -> sisa 300rb; ref 15 Sep (bulan 30 hari) -> 16 hari tersisa
        out = evaluate(self.e, {"spending_limit": {"period": "monthly", "amount": 3_000_000}}, self.ref)
        sf = out["safe_to_spend"]
        self.assertEqual(sf["remaining"], 300_000)
        self.assertEqual(sf["days_left"], 16)   # 30 - 15 + 1
        self.assertEqual(sf["per_day"], 300_000 // 16)

    def test_safe_to_spend_nol_saat_over(self):
        out = evaluate(self.e, {"spending_limit": {"period": "monthly", "amount": 2_000_000}}, self.ref)
        self.assertEqual(out["safe_to_spend"]["per_day"], 0)


if __name__ == "__main__":
    unittest.main()
