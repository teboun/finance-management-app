"""Base de données SQLite / قاعدة البيانات."""
import os
import sqlite3

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "salaires.db")

SCHEMA = """
CREATE TABLE IF NOT EXISTS employees (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    pay_type TEXT NOT NULL CHECK (pay_type IN ('monthly','weekly','daily')),
    base_amount REAL NOT NULL,
    active INTEGER NOT NULL DEFAULT 1
);
CREATE TABLE IF NOT EXISTS absences (
    id INTEGER PRIMARY KEY,
    employee_id INTEGER NOT NULL REFERENCES employees(id),
    date TEXT NOT NULL,
    days REAL NOT NULL DEFAULT 1,
    note TEXT DEFAULT ''
);
CREATE TABLE IF NOT EXISTS employee_purchases (
    id INTEGER PRIMARY KEY,
    employee_id INTEGER NOT NULL REFERENCES employees(id),
    date TEXT NOT NULL,
    amount REAL NOT NULL,
    description TEXT DEFAULT ''
);
CREATE TABLE IF NOT EXISTS business_purchases (
    id INTEGER PRIMARY KEY,
    date TEXT NOT NULL,
    amount REAL NOT NULL,
    description TEXT DEFAULT '',
    supplier TEXT DEFAULT ''
);
CREATE TABLE IF NOT EXISTS payments (
    id INTEGER PRIMARY KEY,
    employee_id INTEGER NOT NULL REFERENCES employees(id),
    period_start TEXT NOT NULL,
    period_end TEXT NOT NULL,
    gross REAL NOT NULL,
    absence_deduction REAL NOT NULL,
    purchases_deduction REAL NOT NULL,
    net REAL NOT NULL,
    paid_on TEXT NOT NULL
);
"""


class DB:
    def __init__(self, path=DB_PATH):
        self.conn = sqlite3.connect(path)
        self.conn.row_factory = sqlite3.Row
        self.conn.executescript(SCHEMA)

    def _exec(self, sql, params=()):
        cur = self.conn.execute(sql, params)
        self.conn.commit()
        return cur

    def _all(self, sql, params=()):
        return self.conn.execute(sql, params).fetchall()

    # Employés
    def add_employee(self, name, pay_type, base):
        return self._exec("INSERT INTO employees (name, pay_type, base_amount) VALUES (?,?,?)",
                          (name, pay_type, base)).lastrowid

    def update_employee(self, emp_id, name, pay_type, base, active=1):
        self._exec("UPDATE employees SET name=?, pay_type=?, base_amount=?, active=? WHERE id=?",
                   (name, pay_type, base, active, emp_id))

    def employees(self, only_active=False):
        sql = "SELECT * FROM employees" + (" WHERE active=1" if only_active else "") + " ORDER BY name"
        return self._all(sql)

    def employee(self, emp_id):
        return self.conn.execute("SELECT * FROM employees WHERE id=?", (emp_id,)).fetchone()

    # Absences
    def add_absence(self, emp_id, day, days, note=""):
        self._exec("INSERT INTO absences (employee_id, date, days, note) VALUES (?,?,?,?)",
                   (emp_id, day, days, note))

    def absences(self, emp_id=None):
        if emp_id:
            return self._all("SELECT a.*, e.name FROM absences a JOIN employees e ON e.id=a.employee_id "
                             "WHERE employee_id=? ORDER BY date DESC", (emp_id,))
        return self._all("SELECT a.*, e.name FROM absences a JOIN employees e ON e.id=a.employee_id "
                         "ORDER BY date DESC")

    def absence_days(self, emp_id, start, end):
        row = self.conn.execute("SELECT COALESCE(SUM(days),0) FROM absences WHERE employee_id=? "
                                "AND date BETWEEN ? AND ?", (emp_id, start, end)).fetchone()
        return row[0]

    # Achats employés (avances / crédit)
    def add_employee_purchase(self, emp_id, day, amount, desc=""):
        self._exec("INSERT INTO employee_purchases (employee_id, date, amount, description) VALUES (?,?,?,?)",
                   (emp_id, day, amount, desc))

    def employee_purchases(self, emp_id=None):
        base = ("SELECT p.*, e.name FROM employee_purchases p JOIN employees e ON e.id=p.employee_id ")
        if emp_id:
            return self._all(base + "WHERE employee_id=? ORDER BY date DESC", (emp_id,))
        return self._all(base + "ORDER BY date DESC")

    def purchases_total(self, emp_id, start, end):
        row = self.conn.execute("SELECT COALESCE(SUM(amount),0) FROM employee_purchases WHERE employee_id=? "
                                "AND date BETWEEN ? AND ?", (emp_id, start, end)).fetchone()
        return row[0]

    # Achats entreprise
    def add_business_purchase(self, day, amount, desc="", supplier=""):
        self._exec("INSERT INTO business_purchases (date, amount, description, supplier) VALUES (?,?,?,?)",
                   (day, amount, desc, supplier))

    def business_purchases(self, month=None):
        if month:
            return self._all("SELECT * FROM business_purchases WHERE substr(date,1,7)=? ORDER BY date DESC",
                             (month,))
        return self._all("SELECT * FROM business_purchases ORDER BY date DESC")

    # Paiements
    def add_payment(self, emp_id, start, end, slip, paid_on):
        self._exec("INSERT INTO payments (employee_id, period_start, period_end, gross, absence_deduction, "
                   "purchases_deduction, net, paid_on) VALUES (?,?,?,?,?,?,?,?)",
                   (emp_id, start, end, slip["gross"], slip["absence_deduction"],
                    slip["purchases_deduction"], slip["net"], paid_on))

    def payments(self, emp_id=None, month=None):
        sql = "SELECT p.*, e.name FROM payments p JOIN employees e ON e.id=p.employee_id WHERE 1=1"
        params = []
        if emp_id:
            sql += " AND employee_id=?"
            params.append(emp_id)
        if month:
            sql += " AND substr(period_start,1,7)=?"
            params.append(month)
        return self._all(sql + " ORDER BY period_start DESC", params)

    # Suppression générique
    def delete(self, table, row_id):
        if table not in ("absences", "employee_purchases", "business_purchases", "payments"):
            raise ValueError(table)
        self._exec(f"DELETE FROM {table} WHERE id=?", (row_id,))
