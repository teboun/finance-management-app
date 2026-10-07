import os
import sqlite3
import tempfile
import unittest
from datetime import date

from salary_app import calc
from salary_app.chart import fmt_short, nice_ceiling
from salary_app.db import DB
from salary_app.report import payslip_section, payslips_document


class FormatTest(unittest.TestCase):
    def test_no_negative_zero(self):
        self.assertEqual(calc.fmt_da(-0.0), "0,00 DA")
        self.assertEqual(calc.fmt_da(-0.001), "0,00 DA")
        self.assertEqual(calc.fmt_da(-1500), "-1 500,00 DA")

    def test_fmt_num(self):
        self.assertEqual(calc.fmt_num(2.0), "2")
        self.assertEqual(calc.fmt_num(1.5), "1,5")
        self.assertEqual(calc.fmt_num(None), "0")

    def test_chart_scale(self):
        self.assertEqual(nice_ceiling(0), 1)
        self.assertEqual(nice_ceiling(124933.52), 200000)
        self.assertEqual(nice_ceiling(30000), 50000)
        self.assertEqual(nice_ceiling(20000), 20000)
        self.assertEqual(fmt_short(150000), "150 k")
        self.assertEqual(fmt_short(1500000), "1,5 M")
        self.assertEqual(fmt_short(0), "0")


class AppParsersTest(unittest.TestCase):
    def test_parsers(self):
        from salary_app.app import parse_days, parse_month, parse_positive, shift_month
        self.assertEqual(parse_positive("1 500,5"), 1500.5)
        for bad, fn in (("0", parse_positive), ("-3", parse_positive), ("abc", parse_positive),
                        ("0", parse_days), ("32", parse_days), ("2026-13", parse_month), ("09-2026", parse_month)):
            with self.assertRaises(ValueError, msg=bad):
                fn(bad)
        self.assertEqual(parse_days("0,5"), 0.5)
        self.assertEqual(parse_month(" 2026-09 "), "2026-09")
        self.assertIsNone(parse_month(""))
        self.assertEqual(shift_month(date(2026, 1, 1), -1), date(2025, 12, 1))
        self.assertEqual(shift_month(date(2026, 12, 1), 1), date(2027, 1, 1))


class DBv3Test(unittest.TestCase):
    def setUp(self):
        self.db = DB(":memory:")
        self.emp = self.db.add_employee("Ali", "monthly", 30000)

    def test_updates(self):
        db, emp = self.db, self.emp
        db.add_absence(emp, "2026-09-10", 1, "x")
        a = db.absences()[0]
        db.update_absence(a["id"], emp, "2026-09-11", 2, "y")
        self.assertEqual(tuple(db.get("absences", a["id"]))[2:], ("2026-09-11", 2, "y"))
        db.add_employee_purchase(emp, "2026-09-12", 100, "a")
        p = db.employee_purchases()[0]
        db.update_employee_purchase(p["id"], emp, "2026-09-13", 250, "b")
        self.assertEqual(db.purchases_total(emp, "2026-09-01", "2026-09-30"), 250)
        db.add_bonus(emp, "2026-09-05", "bonus", 1000)
        b = db.bonuses()[0]
        db.update_bonus(b["id"], emp, "2026-09-05", "overtime", 519.23, 2, "sat")
        self.assertEqual(db.overtime_hours(emp, "2026-09-01", "2026-09-30"), 2)
        self.assertEqual(db.overtime_hours(emp, "2026-09-01", "2026-09-30", exclude_id=b["id"]), 0)
        db.add_business_purchase("2026-09-01", 10, "c", "s")
        bp = db.business_purchases()[0]
        db.update_business_purchase(bp["id"], "2026-09-02", 20, "d", "t")
        self.assertEqual(db.month_sum("business_purchases", "2026-09"), 20)
        with self.assertRaises(ValueError):
            db.get("employees; DROP TABLE x", 1)

    def test_save_payment_replaces_same_period(self):
        db, emp = self.db, self.emp
        slip = calc.compute_payslip("monthly", 30000, 0, 0, date(2026, 9, 1), date(2026, 9, 30))
        db.save_payment(emp, "2026-09-01", "2026-09-30", slip, "2026-09-30")
        slip2 = calc.compute_payslip("monthly", 30000, 1, 0, date(2026, 9, 1), date(2026, 9, 30))
        db.save_payment(emp, "2026-09-01", "2026-09-30", slip2, "2026-10-01")
        pays = db.payments()
        self.assertEqual(len(pays), 1)
        self.assertEqual(pays[0]["net"], 29000)
        db.save_payment(emp, "2026-09-26", "2026-10-02", slip, "2026-10-02")  # autre période: gardée
        self.assertEqual(len(db.payments()), 2)
        self.assertEqual(db.month_sum("payments", "2026-09"), 29000 + 30000)

    def test_month_sums(self):
        db, emp = self.db, self.emp
        db.add_absence(emp, "2026-09-10", 1.5)
        db.add_absence(emp, "2026-10-10", 1)
        db.add_bonus(emp, "2026-09-05", "bonus", 1000)
        db.add_employee_purchase(emp, "2026-09-12", 300)
        self.assertEqual(db.month_sum("absences", "2026-09"), 1.5)
        self.assertEqual(db.month_sum("bonuses", "2026-09"), 1000)
        self.assertEqual(db.month_sum("employee_purchases", "2026-09"), 300)
        self.assertEqual(db.month_sum("payments", "2026-09"), 0)

    def test_restore_rejects_invalid_files(self):
        tmp = tempfile.mkdtemp()
        not_db = os.path.join(tmp, "notes.db")
        with open(not_db, "w") as f:
            f.write("this is not a database " * 100)
        other_db = os.path.join(tmp, "other.db")
        sqlite3.connect(other_db).execute("CREATE TABLE x (a)").connection.commit()
        for path in (not_db, other_db, os.path.join(tmp, "missing.db")):
            with self.assertRaises(ValueError, msg=path):
                self.db.restore_from(path)
            self.assertEqual([e["name"] for e in self.db.employees()], ["Ali"], path)  # données intactes

    def test_restore_path_with_spaces(self):
        tmp = tempfile.mkdtemp()
        path = os.path.join(tmp, "my backups", "salaires backup.db")
        os.makedirs(os.path.dirname(path))
        self.db.backup_to(path)
        self.db.add_employee("Karim", "weekly", 6000)
        self.db.restore_from(path)
        self.assertEqual([e["name"] for e in self.db.employees()], ["Ali"])


class ReportTest(unittest.TestCase):
    def test_multi_payslip_document(self):
        t = {"from_to": "{} - {}"}.get
        slip = calc.compute_payslip("monthly", 30000, 1.5, 0, date(2026, 9, 1), date(2026, 9, 30))
        doc = payslips_document(lambda k: t(k, k), [
            payslip_section(lambda k: t(k, k), "Ali", "Monthly", "a", "b", slip),
            payslip_section(lambda k: t(k, k), "Karim", "Weekly", "a", "b", slip),
        ], "title")
        self.assertEqual(doc.count('<section class="slip">'), 2)
        self.assertIn("break-after: page", doc)
        self.assertIn("(1,5 days)", doc)


if __name__ == "__main__":
    unittest.main()
