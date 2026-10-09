"""Base de données SQLite."""
import os
import sqlite3
import sys
from pathlib import Path

DB_NAME = "salaires.db"


def documents_dir():
    """Dossier « Documents » de l'utilisateur (le vrai, même s'il est déplacé dans OneDrive)."""
    if sys.platform == "win32":
        try:
            import ctypes
            buf = ctypes.create_unicode_buffer(260)
            if ctypes.windll.shell32.SHGetFolderPathW(None, 5, None, 0, buf) == 0 and buf.value:  # 5 = Mes documents
                return Path(buf.value)
        except (AttributeError, OSError):
            pass
    docs = Path.home() / "Documents"
    return docs if docs.is_dir() else Path.home()


def default_db_path():
    """Emplacement du fichier de données.
    - variable SALAIRES_DATA_DIR si elle est définie;
    - programme installé (Salaires.exe / Salaires.app): salaires.db à côté du programme s'il y en a un
      (mode portable), sinon Documents/Salaires/salaires.db (un dossier qui ne disparaît pas);
    - lancé depuis le code source (Lancer.bat / Lancer.command): à côté du dossier salary_app."""
    if os.environ.get("SALAIRES_DATA_DIR"):
        return str(Path(os.environ["SALAIRES_DATA_DIR"]) / DB_NAME)
    if getattr(sys, "frozen", False):
        beside = Path(sys.executable).resolve().parent / DB_NAME
        if beside.exists():
            return str(beside)
        return str(documents_dir() / "Salaires" / DB_NAME)
    return str(Path(__file__).resolve().parent.parent / DB_NAME)


DB_PATH = default_db_path()

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
CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT
);
CREATE TABLE IF NOT EXISTS bonuses (
    id INTEGER PRIMARY KEY,
    employee_id INTEGER NOT NULL REFERENCES employees(id),
    date TEXT NOT NULL,
    kind TEXT NOT NULL CHECK (kind IN ('bonus','overtime')),
    hours REAL NOT NULL DEFAULT 0,
    amount REAL NOT NULL,
    note TEXT DEFAULT ''
);
"""


class DB:
    def __init__(self, path=None):
        self.path = path or default_db_path()
        if self.path != ":memory:":
            os.makedirs(os.path.dirname(os.path.abspath(self.path)), exist_ok=True)
        self.conn = sqlite3.connect(self.path)
        self.conn.row_factory = sqlite3.Row
        self._migrate()

    def _migrate(self):
        """Crée les tables manquantes et met à jour les anciennes bases."""
        self.conn.executescript(SCHEMA)
        cols = [r["name"] for r in self.conn.execute("PRAGMA table_info(payments)")]
        if "bonuses" not in cols:
            self._exec("ALTER TABLE payments ADD COLUMN bonuses REAL NOT NULL DEFAULT 0")

    # Sauvegarde / restauration
    def backup_to(self, path):
        dest = sqlite3.connect(path)
        with dest:
            self.conn.backup(dest)
        dest.close()

    def restore_from(self, path):
        """Remplace les données par la sauvegarde; refuse un fichier qui n'en est pas une."""
        try:
            src = sqlite3.connect(Path(path).resolve().as_uri() + "?mode=ro", uri=True)
        except sqlite3.Error:
            raise ValueError("invalid_backup")
        try:
            ok = src.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='employees'").fetchone()
            if not ok:
                raise ValueError("invalid_backup")
            src.backup(self.conn)
        except sqlite3.DatabaseError:
            raise ValueError("invalid_backup")
        finally:
            src.close()
        self._migrate()

    def _exec(self, sql, params=()):
        cur = self.conn.execute(sql, params)
        self.conn.commit()
        return cur

    def _all(self, sql, params=()):
        return self.conn.execute(sql, params).fetchall()

    # Paramètres (langue, ...)
    def get_setting(self, key, default=None):
        row = self.conn.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
        return row[0] if row else default

    def set_setting(self, key, value):
        self._exec("INSERT OR REPLACE INTO settings (key, value) VALUES (?,?)", (key, value))

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

    def update_absence(self, row_id, emp_id, day, days, note=""):
        self._exec("UPDATE absences SET employee_id=?, date=?, days=?, note=? WHERE id=?",
                   (emp_id, day, days, note, row_id))

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

    def update_employee_purchase(self, row_id, emp_id, day, amount, desc=""):
        self._exec("UPDATE employee_purchases SET employee_id=?, date=?, amount=?, description=? WHERE id=?",
                   (emp_id, day, amount, desc, row_id))

    def purchases_total(self, emp_id, start, end):
        row = self.conn.execute("SELECT COALESCE(SUM(amount),0) FROM employee_purchases WHERE employee_id=? "
                                "AND date BETWEEN ? AND ?", (emp_id, start, end)).fetchone()
        return row[0]

    # Achats entreprise
    def add_business_purchase(self, day, amount, desc="", supplier=""):
        self._exec("INSERT INTO business_purchases (date, amount, description, supplier) VALUES (?,?,?,?)",
                   (day, amount, desc, supplier))

    def update_business_purchase(self, row_id, day, amount, desc="", supplier=""):
        self._exec("UPDATE business_purchases SET date=?, amount=?, description=?, supplier=? WHERE id=?",
                   (day, amount, desc, supplier, row_id))

    def business_purchases(self, month=None):
        if month:
            return self._all("SELECT * FROM business_purchases WHERE substr(date,1,7)=? ORDER BY date DESC",
                             (month,))
        return self._all("SELECT * FROM business_purchases ORDER BY date DESC")

    # Primes et heures supplémentaires
    def add_bonus(self, emp_id, day, kind, amount, hours=0, note=""):
        self._exec("INSERT INTO bonuses (employee_id, date, kind, hours, amount, note) VALUES (?,?,?,?,?,?)",
                   (emp_id, day, kind, hours, amount, note))

    def bonuses(self, emp_id=None):
        base = "SELECT b.*, e.name FROM bonuses b JOIN employees e ON e.id=b.employee_id "
        if emp_id:
            return self._all(base + "WHERE employee_id=? ORDER BY date DESC", (emp_id,))
        return self._all(base + "ORDER BY date DESC")

    def update_bonus(self, row_id, emp_id, day, kind, amount, hours=0, note=""):
        self._exec("UPDATE bonuses SET employee_id=?, date=?, kind=?, hours=?, amount=?, note=? WHERE id=?",
                   (emp_id, day, kind, hours, amount, note, row_id))

    def overtime_hours(self, emp_id, start, end, exclude_id=None):
        """Heures supplémentaires déjà saisies dans la période (hors ligne exclude_id)."""
        row = self.conn.execute("SELECT COALESCE(SUM(hours),0) FROM bonuses WHERE employee_id=? AND kind='overtime' "
                                "AND date BETWEEN ? AND ? AND id IS NOT ?", (emp_id, start, end, exclude_id)).fetchone()
        return row[0]

    def bonuses_total(self, emp_id, start, end):
        row = self.conn.execute("SELECT COALESCE(SUM(amount),0) FROM bonuses WHERE employee_id=? "
                                "AND date BETWEEN ? AND ?", (emp_id, start, end)).fetchone()
        return row[0]

    # Paiements
    def add_payment(self, emp_id, start, end, slip, paid_on):
        self._exec("INSERT INTO payments (employee_id, period_start, period_end, gross, bonuses, "
                   "absence_deduction, purchases_deduction, net, paid_on) VALUES (?,?,?,?,?,?,?,?,?)",
                   (emp_id, start, end, slip["gross"], slip.get("bonuses", 0), slip["absence_deduction"],
                    slip["purchases_deduction"], slip["net"], paid_on))

    def paid_ids(self, emp_id, start, end):
        """Paiements déjà enregistrés pour cet employé et cette période."""
        return [r[0] for r in self.conn.execute(
            "SELECT id FROM payments WHERE employee_id=? AND period_start=? AND period_end=?", (emp_id, start, end))]

    def save_payment(self, emp_id, start, end, slip, paid_on):
        """Enregistre le paiement en remplaçant un éventuel paiement de la même période."""
        for row_id in self.paid_ids(emp_id, start, end):
            self.conn.execute("DELETE FROM payments WHERE id=?", (row_id,))
        self.add_payment(emp_id, start, end, slip, paid_on)

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

    # Totaux du mois (tableau de bord)
    MONTH_SUMS = {
        "payments": ("net", "period_start"),
        "employee_purchases": ("amount", "date"),
        "business_purchases": ("amount", "date"),
        "bonuses": ("amount", "date"),
        "absences": ("days", "date"),
    }

    def month_sum(self, table, month):
        """Somme du mois (AAAA-MM) pour une table connue."""
        col, date_col = self.MONTH_SUMS[table]
        row = self.conn.execute(f"SELECT COALESCE(SUM({col}),0) FROM {table} WHERE substr({date_col},1,7)=?",
                                (month,)).fetchone()
        return row[0]

    # Lecture / suppression génériques
    TABLES = ("absences", "employee_purchases", "business_purchases", "payments", "bonuses")

    def get(self, table, row_id):
        if table not in self.TABLES:
            raise ValueError(table)
        return self.conn.execute(f"SELECT * FROM {table} WHERE id=?", (row_id,)).fetchone()

    def delete(self, table, row_id):
        if table not in self.TABLES:
            raise ValueError(table)
        self._exec(f"DELETE FROM {table} WHERE id=?", (row_id,))
