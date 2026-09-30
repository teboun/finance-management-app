import unittest
from datetime import date

from salary_app import calc
from salary_app.db import DB


class CalcTest(unittest.TestCase):
    def test_daily_rate(self):
        self.assertEqual(calc.daily_rate("monthly", 30000), 1000)
        self.assertEqual(calc.daily_rate("weekly", 6000), 1000)
        self.assertEqual(calc.daily_rate("daily", 1500), 1500)

    def test_periods(self):
        self.assertEqual(calc.month_period(date(2026, 2, 10)), (date(2026, 2, 1), date(2026, 2, 28)))
        start, end = calc.week_period(date(2026, 9, 30))  # mercredi
        self.assertEqual(start.weekday(), calc.WEEK_START)
        self.assertEqual((end - start).days, 6)
        self.assertTrue(start <= date(2026, 9, 30) <= end)

    def test_monthly_payslip(self):
        start, end = calc.month_period(date(2026, 9, 1))
        slip = calc.compute_payslip("monthly", 30000, 2, 3500, start, end)
        self.assertEqual(slip["gross"], 30000)
        self.assertEqual(slip["absence_deduction"], 2000)
        self.assertEqual(slip["net"], 30000 - 2000 - 3500)

    def test_monthly_employee_weekly_period(self):
        start, end = calc.week_period(date(2026, 9, 30))
        self.assertEqual(calc.period_gross("monthly", 30000, start, end), 7000)

    def test_weekly_payslip(self):
        start, end = calc.week_period(date(2026, 9, 30))
        slip = calc.compute_payslip("weekly", 6000, 1, 0, start, end)
        self.assertEqual(slip["net"], 5000)

    def test_daily_payslip(self):
        start, end = calc.week_period(date(2026, 9, 30))
        slip = calc.compute_payslip("daily", 1000, 0.5, 200, start, end)
        self.assertEqual(slip["gross"], 6000)  # 7 jours - vendredi
        self.assertEqual(slip["net"], 6000 - 500 - 200)

    def test_negative_net(self):
        start, end = calc.month_period(date(2026, 9, 1))
        self.assertLess(calc.compute_payslip("monthly", 10000, 0, 12000, start, end)["net"], 0)

    def test_fmt(self):
        self.assertEqual(calc.fmt_da(12345.5), "12 345,50 DA")


class DBTest(unittest.TestCase):
    def test_totals_in_period(self):
        db = DB(":memory:")
        emp = db.add_employee("Ali", "monthly", 30000)
        db.add_absence(emp, "2026-09-10", 1)
        db.add_absence(emp, "2026-10-01", 1)
        db.add_employee_purchase(emp, "2026-09-15", 1200, "sucre")
        self.assertEqual(db.absence_days(emp, "2026-09-01", "2026-09-30"), 1)
        self.assertEqual(db.purchases_total(emp, "2026-09-01", "2026-09-30"), 1200)

    def test_settings(self):
        db = DB(":memory:")
        self.assertEqual(db.get_setting("lang", "en"), "en")
        db.set_setting("lang", "fr")
        self.assertEqual(db.get_setting("lang", "en"), "fr")


if __name__ == "__main__":
    unittest.main()
