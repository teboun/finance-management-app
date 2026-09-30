import os
import sqlite3
import tempfile
import unittest
import zipfile
from datetime import date

from salary_app import calc
from salary_app.db import DB
from salary_app.report import payslip_html
from salary_app.xlsx import write_xlsx


class OvertimeTest(unittest.TestCase):
    def test_hourly_rate(self):
        self.assertAlmostEqual(calc.hourly_rate("monthly", 30000), 173.08, places=2)
        self.assertEqual(calc.hourly_rate("weekly", 8000), 200)
        self.assertEqual(calc.hourly_rate("daily", 1600), 200)

    def test_overtime_amount(self):
        self.assertEqual(calc.overtime_amount("monthly", 30000, 2), 519.23)
        self.assertEqual(calc.overtime_amount("daily", 1600, 3), 900)

    def test_payslip_with_bonuses(self):
        start, end = calc.month_period(date(2026, 9, 1))
        slip = calc.compute_payslip("monthly", 30000, 1, 500, start, end, bonuses_total=2500)
        self.assertEqual(slip["bonuses"], 2500)
        self.assertEqual(slip["net"], 30000 + 2500 - 1000 - 500)


class DBv2Test(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def test_bonuses_total_and_payment(self):
        db = DB(":memory:")
        emp = db.add_employee("Ali", "monthly", 30000)
        db.add_bonus(emp, "2026-09-05", "bonus", 2000)
        db.add_bonus(emp, "2026-09-06", "overtime", 519.23, hours=2)
        db.add_bonus(emp, "2026-10-01", "bonus", 999)
        self.assertAlmostEqual(db.bonuses_total(emp, "2026-09-01", "2026-09-30"), 2519.23)
        slip = calc.compute_payslip("monthly", 30000, 0, 0, date(2026, 9, 1), date(2026, 9, 30), 2519.23)
        db.add_payment(emp, "2026-09-01", "2026-09-30", slip, "2026-09-30")
        self.assertEqual(db.payments()[0]["bonuses"], 2519.23)

    def test_migrates_old_database(self):
        path = os.path.join(self.tmp, "old.db")
        conn = sqlite3.connect(path)
        conn.executescript("""CREATE TABLE payments (id INTEGER PRIMARY KEY, employee_id INTEGER, period_start TEXT,
            period_end TEXT, gross REAL, absence_deduction REAL, purchases_deduction REAL, net REAL, paid_on TEXT);
            INSERT INTO payments VALUES (1, 1, '2026-08-01', '2026-08-31', 100, 0, 0, 100, '2026-08-31');""")
        conn.commit()
        conn.close()
        db = DB(path)
        self.assertEqual(db.conn.execute("SELECT bonuses FROM payments").fetchone()[0], 0)
        self.assertEqual(db.bonuses_total(1, "2026-01-01", "2026-12-31"), 0)

    def test_backup_restore(self):
        db = DB(os.path.join(self.tmp, "main.db"))
        db.add_employee("Ali", "monthly", 30000)
        backup = os.path.join(self.tmp, "backup.db")
        db.backup_to(backup)
        db.add_employee("Karim", "weekly", 6000)
        self.assertEqual(len(db.employees()), 2)
        db.restore_from(backup)
        self.assertEqual([e["name"] for e in db.employees()], ["Ali"])


class ExportTest(unittest.TestCase):
    def test_write_xlsx(self):
        path = os.path.join(tempfile.mkdtemp(), "t.xlsx")
        write_xlsx(path, ["Name", "Net"], [["Ali & Co <x>", 26500.5], ["Karim", -10]], sheet_name="Salaires")
        with zipfile.ZipFile(path) as z:
            self.assertIn("xl/worksheets/sheet1.xml", z.namelist())
            sheet = z.read("xl/worksheets/sheet1.xml").decode()
        self.assertIn("Ali &amp; Co &lt;x&gt;", sheet)
        self.assertIn("<v>26500.5</v>", sheet)
        self.assertIn('r="B3"', sheet)

    def test_payslip_html(self):
        start, end = calc.month_period(date(2026, 9, 1))
        slip = calc.compute_payslip("monthly", 30000, 2, 1500, start, end, bonuses_total=1000)
        html = payslip_html(lambda k: {"from_to": "From {} to {}"}.get(k, k), "Ali", "Monthly",
                            "2026-09-01", "2026-09-30", slip)
        self.assertIn("Ali", html)
        self.assertIn(calc.fmt_da(27500), html)
        self.assertIn("From 2026-09-01 to 2026-09-30", html)


if __name__ == "__main__":
    unittest.main()
