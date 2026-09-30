"""Application de gestion des salaires / تطبيق تسيير الرواتب.

Lancer: python -m salary_app.app
"""
import tkinter as tk
from datetime import date
from tkinter import messagebox, ttk

from . import calc
from .db import DB

PAY_LABELS = {
    "monthly": "Mensuel / شهري",
    "weekly": "Hebdomadaire / أسبوعي",
    "daily": "Journalier / يومي",
}
PAY_FROM_LABEL = {v: k for k, v in PAY_LABELS.items()}
PERIOD_MONTH = "Mois / شهر"
PERIOD_WEEK = "Semaine / أسبوع"
ALL = "Tous / الكل"


def parse_date(text):
    try:
        return date.fromisoformat(text.strip())
    except ValueError:
        raise ValueError("Date invalide (AAAA-MM-JJ) / تاريخ غير صحيح")


def parse_amount(text):
    try:
        return float(text.replace(" ", "").replace(",", "."))
    except ValueError:
        raise ValueError("Montant invalide / مبلغ غير صحيح")


def make_tree(parent, columns, height=12):
    """Treeview avec barre de défilement. columns = [(id, titre, largeur)]."""
    frame = ttk.Frame(parent)
    tree = ttk.Treeview(frame, columns=[c[0] for c in columns], show="headings", height=height)
    for cid, title, width in columns:
        tree.heading(cid, text=title)
        tree.column(cid, width=width, anchor="center")
    sb = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=sb.set)
    tree.pack(side="left", fill="both", expand=True)
    sb.pack(side="right", fill="y")
    frame.pack(fill="both", expand=True, padx=8, pady=8)
    return tree


def fill_tree(tree, rows):
    tree.delete(*tree.get_children())
    for iid, values in rows:
        tree.insert("", "end", iid=str(iid), values=values)


class App(tk.Tk):
    def __init__(self, db):
        super().__init__()
        self.db = db
        self.title("Gestion des salaires / تسيير الرواتب")
        self.geometry("980x620")
        self.emp_combos = []

        nb = ttk.Notebook(self)
        nb.pack(fill="both", expand=True)
        for title, builder in (
            ("Employés / الموظفون", self.build_employees),
            ("Absences / الغيابات", self.build_absences),
            ("Achats employés / مشتريات الموظفين", self.build_emp_purchases),
            ("Calcul salaire / حساب الراتب", self.build_calc),
            ("Historique / السجل", self.build_history),
            ("Achats entreprise / مشتريات المؤسسة", self.build_business),
        ):
            tab = ttk.Frame(nb)
            nb.add(tab, text=title)
            builder(tab)
        nb.bind("<<NotebookTabChanged>>", lambda e: self.refresh_emp_combos())
        self.refresh_emp_combos()

    # ---------- helpers ----------
    def form(self, parent, fields):
        """Crée une ligne de champs. fields = [(clé, label, widget_factory)]. Retourne dict de variables."""
        box = ttk.Frame(parent)
        box.pack(fill="x", padx=8, pady=8)
        vars_ = {}
        for col, (key, label, kind) in enumerate(fields):
            ttk.Label(box, text=label).grid(row=0, column=col, sticky="w", padx=4)
            var = tk.StringVar()
            if kind == "emp":
                w = ttk.Combobox(box, textvariable=var, state="readonly", width=22)
                self.emp_combos.append((w, False))
            elif kind == "emp_all":
                w = ttk.Combobox(box, textvariable=var, state="readonly", width=22)
                self.emp_combos.append((w, True))
                var.set(ALL)
            elif isinstance(kind, tuple):
                w = ttk.Combobox(box, textvariable=var, values=kind, state="readonly", width=20)
                var.set(kind[0])
            else:
                w = ttk.Entry(box, textvariable=var, width=kind or 16)
            if key == "date":
                var.set(date.today().isoformat())
            elif key == "month":
                var.set(date.today().strftime("%Y-%m"))
            w.grid(row=1, column=col, sticky="w", padx=4)
            vars_[key] = var
        vars_["_box"] = box
        return vars_

    def button(self, box, text, cmd, col):
        ttk.Button(box, text=text, command=cmd).grid(row=1, column=col, padx=4)

    def refresh_emp_combos(self):
        names = [f"{e['id']} - {e['name']}" for e in self.db.employees(only_active=True)]
        for combo, with_all in self.emp_combos:
            combo["values"] = ([ALL] if with_all else []) + names

    @staticmethod
    def emp_id(var):
        text = var.get()
        if not text or text == ALL:
            return None
        return int(text.split(" - ")[0])

    def safe(self, fn):
        """Exécute fn en affichant les erreurs."""
        def run():
            try:
                fn()
            except ValueError as err:
                messagebox.showerror("Erreur / خطأ", str(err))
        return run

    def delete_selected(self, tree, table, refresh):
        sel = tree.selection()
        if not sel:
            return
        if messagebox.askyesno("Supprimer / حذف", "Supprimer la ligne ? / حذف السطر؟"):
            for iid in sel:
                self.db.delete(table, int(iid))
            refresh()

    def require_emp(self, var):
        emp_id = self.emp_id(var)
        if emp_id is None:
            raise ValueError("Choisir un employé / اختر موظفا")
        return emp_id

    # ---------- Employés ----------
    def build_employees(self, tab):
        v = self.form(tab, [
            ("name", "Nom / الاسم", 24),
            ("pay_type", "Type de paie / نوع الأجر", tuple(PAY_LABELS.values())),
            ("base", "Salaire (DA) / الراتب", 14),
        ])
        v["active"] = tk.IntVar(value=1)
        ttk.Checkbutton(v["_box"], text="Actif / نشط", variable=v["active"]).grid(row=1, column=3, padx=4)
        tree = make_tree(tab, [
            ("name", "Nom / الاسم", 220), ("type", "Type / النوع", 170),
            ("base", "Salaire / الراتب", 150), ("rate", "Taux jour / الأجر اليومي", 150),
            ("active", "Actif / نشط", 80),
        ])

        def refresh():
            rows = []
            for e in self.db.employees():
                rows.append((e["id"], (e["name"], PAY_LABELS[e["pay_type"]], calc.fmt_da(e["base_amount"]),
                                       calc.fmt_da(calc.daily_rate(e["pay_type"], e["base_amount"])),
                                       "Oui / نعم" if e["active"] else "Non / لا")))
            fill_tree(tree, rows)
            self.refresh_emp_combos()

        def values():
            name = v["name"].get().strip()
            if not name:
                raise ValueError("Nom obligatoire / الاسم إجباري")
            return name, PAY_FROM_LABEL[v["pay_type"].get()], parse_amount(v["base"].get())

        def add():
            self.db.add_employee(*values())
            refresh()

        def update():
            sel = tree.selection()
            if not sel:
                raise ValueError("Sélectionner un employé / اختر موظفا")
            self.db.update_employee(int(sel[0]), *values(), active=v["active"].get())
            refresh()

        def on_select(_):
            sel = tree.selection()
            if sel:
                e = self.db.employee(int(sel[0]))
                v["name"].set(e["name"])
                v["pay_type"].set(PAY_LABELS[e["pay_type"]])
                v["base"].set(str(e["base_amount"]))
                v["active"].set(e["active"])

        tree.bind("<<TreeviewSelect>>", on_select)
        self.button(v["_box"], "Ajouter / إضافة", self.safe(add), 4)
        self.button(v["_box"], "Modifier / تعديل", self.safe(update), 5)
        refresh()

    # ---------- Absences ----------
    def build_absences(self, tab):
        v = self.form(tab, [
            ("emp", "Employé / الموظف", "emp"),
            ("date", "Date / التاريخ", 12),
            ("days", "Jours / الأيام", 6),
            ("note", "Remarque / ملاحظة", 24),
        ])
        v["days"].set("1")
        tree = make_tree(tab, [
            ("date", "Date / التاريخ", 120), ("name", "Employé / الموظف", 220),
            ("days", "Jours / الأيام", 90), ("note", "Remarque / ملاحظة", 300),
        ])

        def refresh():
            fill_tree(tree, [(a["id"], (a["date"], a["name"], a["days"], a["note"])) for a in self.db.absences()])

        def add():
            emp_id = self.require_emp(v["emp"])
            days = parse_amount(v["days"].get())
            self.db.add_absence(emp_id, parse_date(v["date"].get()).isoformat(), days, v["note"].get())
            refresh()

        self.button(v["_box"], "Ajouter / إضافة", self.safe(add), 4)
        self.button(v["_box"], "Supprimer / حذف",
                    lambda: self.delete_selected(tree, "absences", refresh), 5)
        refresh()

    # ---------- Achats employés ----------
    def build_emp_purchases(self, tab):
        v = self.form(tab, [
            ("emp", "Employé / الموظف", "emp"),
            ("date", "Date / التاريخ", 12),
            ("amount", "Montant (DA) / المبلغ", 12),
            ("desc", "Article / avance - السلعة / تسبيق", 26),
        ])
        tree = make_tree(tab, [
            ("date", "Date / التاريخ", 120), ("name", "Employé / الموظف", 220),
            ("amount", "Montant / المبلغ", 150), ("desc", "Description / الوصف", 300),
        ])

        def refresh():
            fill_tree(tree, [(p["id"], (p["date"], p["name"], calc.fmt_da(p["amount"]), p["description"]))
                             for p in self.db.employee_purchases()])

        def add():
            emp_id = self.require_emp(v["emp"])
            self.db.add_employee_purchase(emp_id, parse_date(v["date"].get()).isoformat(),
                                          parse_amount(v["amount"].get()), v["desc"].get())
            refresh()

        self.button(v["_box"], "Ajouter / إضافة", self.safe(add), 4)
        self.button(v["_box"], "Supprimer / حذف",
                    lambda: self.delete_selected(tree, "employee_purchases", refresh), 5)
        refresh()

    # ---------- Calcul ----------
    def build_calc(self, tab):
        v = self.form(tab, [
            ("emp", "Employé / الموظف", "emp_all"),
            ("period", "Période / الفترة", (PERIOD_MONTH, PERIOD_WEEK)),
            ("date", "Date dans la période / تاريخ ضمن الفترة", 12),
        ])
        period_lbl = ttk.Label(tab, text="", font=("TkDefaultFont", 10, "bold"))
        period_lbl.pack(anchor="w", padx=12)
        tree = make_tree(tab, [
            ("name", "Employé / الموظف", 170), ("gross", "Brut / الخام", 130),
            ("abs", "Jours abs. / أيام الغياب", 100), ("absded", "Retenue abs. / خصم الغياب", 140),
            ("achats", "Achats / المشتريات", 130), ("net", "Net à payer / الصافي", 140),
        ])
        total_lbl = ttk.Label(tab, text="", font=("TkDefaultFont", 11, "bold"))
        total_lbl.pack(anchor="e", padx=12, pady=6)
        results = {}

        def period():
            d = parse_date(v["date"].get())
            return calc.month_period(d) if v["period"].get() == PERIOD_MONTH else calc.week_period(d)

        def compute():
            start, end = period()
            s, e = start.isoformat(), end.isoformat()
            emp_id = self.emp_id(v["emp"])
            emps = [self.db.employee(emp_id)] if emp_id else self.db.employees(only_active=True)
            results.clear()
            rows, total = [], 0
            for emp in emps:
                slip = calc.compute_payslip(emp["pay_type"], emp["base_amount"],
                                            self.db.absence_days(emp["id"], s, e),
                                            self.db.purchases_total(emp["id"], s, e), start, end)
                results[emp["id"]] = (s, e, slip)
                total += slip["net"]
                net = calc.fmt_da(slip["net"]) + (" (reste dû / دين)" if slip["net"] < 0 else "")
                rows.append((emp["id"], (emp["name"], calc.fmt_da(slip["gross"]), slip["absence_days"],
                                         calc.fmt_da(slip["absence_deduction"]),
                                         calc.fmt_da(slip["purchases_deduction"]), net)))
            fill_tree(tree, rows)
            period_lbl.config(text=f"Du / من {s}  au / إلى {e}")
            total_lbl.config(text=f"Total net / المجموع الصافي: {calc.fmt_da(total)}")

        def save():
            ids = [int(i) for i in tree.selection()] or list(results)
            if not ids:
                raise ValueError("Calculer d'abord / احسب أولا")
            if not messagebox.askyesno("Paiement / الدفع",
                                       f"Enregistrer {len(ids)} paiement(s) ? / تسجيل الدفع؟"):
                return
            today = date.today().isoformat()
            for emp_id in ids:
                s, e, slip = results[emp_id]
                self.db.add_payment(emp_id, s, e, slip, today)
            messagebox.showinfo("OK", "Paiement enregistré / تم تسجيل الدفع")

        self.button(v["_box"], "Calculer / احسب", self.safe(compute), 3)
        self.button(v["_box"], "Enregistrer paiement / تسجيل الدفع", self.safe(save), 4)

    # ---------- Historique ----------
    def build_history(self, tab):
        v = self.form(tab, [
            ("emp", "Employé / الموظف", "emp_all"),
            ("month", "Mois (AAAA-MM, vide = tout) / الشهر", 12),
        ])
        tree = make_tree(tab, [
            ("period", "Période / الفترة", 190), ("name", "Employé / الموظف", 160),
            ("gross", "Brut / الخام", 120), ("absded", "Abs. / الغياب", 110),
            ("achats", "Achats / المشتريات", 110), ("net", "Net / الصافي", 120),
            ("paid", "Payé le / تاريخ الدفع", 110),
        ])
        total_lbl = ttk.Label(tab, text="", font=("TkDefaultFont", 11, "bold"))
        total_lbl.pack(anchor="e", padx=12, pady=6)

        def refresh():
            pays = self.db.payments(self.emp_id(v["emp"]), v["month"].get().strip() or None)
            fill_tree(tree, [(p["id"], (f"{p['period_start']} → {p['period_end']}", p["name"],
                                        calc.fmt_da(p["gross"]), calc.fmt_da(p["absence_deduction"]),
                                        calc.fmt_da(p["purchases_deduction"]), calc.fmt_da(p["net"]),
                                        p["paid_on"])) for p in pays])
            total_lbl.config(text=f"Total payé / مجموع المدفوع: {calc.fmt_da(sum(p['net'] for p in pays))}")

        self.button(v["_box"], "Afficher / عرض", self.safe(refresh), 2)
        self.button(v["_box"], "Supprimer / حذف",
                    lambda: self.delete_selected(tree, "payments", refresh), 3)
        refresh()

    # ---------- Achats entreprise ----------
    def build_business(self, tab):
        v = self.form(tab, [
            ("date", "Date / التاريخ", 12),
            ("amount", "Montant (DA) / المبلغ", 12),
            ("desc", "Description / الوصف", 26),
            ("supplier", "Fournisseur / المورد", 18),
        ])
        f = self.form(tab, [("month", "Mois (AAAA-MM, vide = tout) / الشهر", 12)])
        tree = make_tree(tab, [
            ("date", "Date / التاريخ", 120), ("amount", "Montant / المبلغ", 150),
            ("desc", "Description / الوصف", 300), ("supplier", "Fournisseur / المورد", 200),
        ])
        total_lbl = ttk.Label(tab, text="", font=("TkDefaultFont", 11, "bold"))
        total_lbl.pack(anchor="e", padx=12, pady=6)

        def refresh():
            rows = self.db.business_purchases(f["month"].get().strip() or None)
            fill_tree(tree, [(p["id"], (p["date"], calc.fmt_da(p["amount"]), p["description"], p["supplier"]))
                             for p in rows])
            total_lbl.config(text=f"Total achats / مجموع المشتريات: {calc.fmt_da(sum(p['amount'] for p in rows))}")

        def add():
            self.db.add_business_purchase(parse_date(v["date"].get()).isoformat(),
                                          parse_amount(v["amount"].get()), v["desc"].get(), v["supplier"].get())
            refresh()

        self.button(v["_box"], "Ajouter / إضافة", self.safe(add), 4)
        self.button(f["_box"], "Afficher / عرض", self.safe(refresh), 1)
        self.button(f["_box"], "Supprimer / حذف",
                    lambda: self.delete_selected(tree, "business_purchases", refresh), 2)
        refresh()


def main():
    App(DB()).mainloop()


if __name__ == "__main__":
    main()
