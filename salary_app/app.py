"""Application de gestion des salaires (English / Français).

Lancer: python -m salary_app.app
"""
import tkinter as tk
from datetime import date
from tkinter import messagebox, ttk

from . import calc
from .db import DB

LANGS = ("en", "fr")

# clé -> (English, Français)
TEXT = {
    "title": ("Salary management", "Gestion des salaires"),
    "switch": ("Français", "English"),
    "tab_emp": ("Employees", "Employés"),
    "tab_abs": ("Absences", "Absences"),
    "tab_emp_purch": ("Employee purchases", "Achats employés"),
    "tab_calc": ("Salary calculation", "Calcul salaire"),
    "tab_hist": ("History", "Historique"),
    "tab_business": ("Business purchases", "Achats entreprise"),
    "monthly": ("Monthly", "Mensuel"),
    "weekly": ("Weekly", "Hebdomadaire"),
    "daily": ("Daily", "Journalier"),
    "month": ("Month", "Mois"),
    "week": ("Week", "Semaine"),
    "all": ("All", "Tous"),
    "error": ("Error", "Erreur"),
    "err_date": ("Invalid date (YYYY-MM-DD)", "Date invalide (AAAA-MM-JJ)"),
    "err_amount": ("Invalid amount", "Montant invalide"),
    "choose_emp": ("Choose an employee", "Choisir un employé"),
    "name_required": ("Name is required", "Nom obligatoire"),
    "delete_title": ("Delete", "Supprimer"),
    "delete_confirm": ("Delete the selected line(s)?", "Supprimer la/les ligne(s) ?"),
    "name": ("Name", "Nom"),
    "pay_type": ("Pay type", "Type de paie"),
    "salary_da": ("Salary (DA)", "Salaire (DA)"),
    "salary": ("Salary", "Salaire"),
    "type": ("Type", "Type"),
    "rate": ("Daily rate", "Taux jour"),
    "active": ("Active", "Actif"),
    "yes": ("Yes", "Oui"),
    "no": ("No", "Non"),
    "add": ("Add", "Ajouter"),
    "edit": ("Edit", "Modifier"),
    "delete": ("Delete", "Supprimer"),
    "employee": ("Employee", "Employé"),
    "date": ("Date", "Date"),
    "days": ("Days", "Jours"),
    "note": ("Note", "Remarque"),
    "amount_da": ("Amount (DA)", "Montant (DA)"),
    "amount": ("Amount", "Montant"),
    "item_advance": ("Item / advance", "Article / avance"),
    "description": ("Description", "Description"),
    "period": ("Period", "Période"),
    "date_in_period": ("Date in period", "Date dans la période"),
    "gross": ("Gross", "Brut"),
    "abs_days": ("Absent days", "Jours abs."),
    "abs_ded": ("Absence deduction", "Retenue abs."),
    "purchases": ("Purchases", "Achats"),
    "net_pay": ("Net to pay", "Net à payer"),
    "debt": ("owed", "reste dû"),
    "from_to": ("From {} to {}", "Du {} au {}"),
    "total_net": ("Total net", "Total net"),
    "calc": ("Calculate", "Calculer"),
    "save_payment": ("Save payment", "Enregistrer paiement"),
    "calc_first": ("Calculate first", "Calculer d'abord"),
    "payment": ("Payment", "Paiement"),
    "confirm_payments": ("Save {} payment(s)?", "Enregistrer {} paiement(s) ?"),
    "payment_saved": ("Payment saved", "Paiement enregistré"),
    "month_filter": ("Month (YYYY-MM, empty = all)", "Mois (AAAA-MM, vide = tout)"),
    "show": ("Show", "Afficher"),
    "abs_short": ("Absences", "Abs."),
    "net": ("Net", "Net"),
    "paid_on": ("Paid on", "Payé le"),
    "total_paid": ("Total paid", "Total payé"),
    "supplier": ("Supplier", "Fournisseur"),
    "total_purchases": ("Total purchases", "Total achats"),
}


def parse_date(text):
    try:
        return date.fromisoformat(text.strip())
    except ValueError:
        raise ValueError("err_date")


def parse_amount(text):
    try:
        return float(text.replace(" ", "").replace(",", "."))
    except ValueError:
        raise ValueError("err_amount")


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
        self.lang = db.get_setting("lang", "en")
        self.geometry("1100x650")
        self.root_frame = None
        self.build()

    def t(self, key):
        return TEXT[key][LANGS.index(self.lang)]

    def pay_label(self, pay_type):
        return self.t(pay_type)

    def pay_from_label(self, label):
        return next(p for p in calc.PAY_TYPES if self.t(p) == label)

    def switch_lang(self):
        self.lang = "fr" if self.lang == "en" else "en"
        self.db.set_setting("lang", self.lang)
        self.build()

    def build(self):
        """(Re)construit toute l'interface dans la langue courante."""
        if self.root_frame:
            self.root_frame.destroy()
        self.title(self.t("title"))
        self.emp_combos = []
        self.root_frame = ttk.Frame(self)
        self.root_frame.pack(fill="both", expand=True)
        ttk.Button(self.root_frame, text=self.t("switch"), command=self.switch_lang).pack(anchor="e", padx=8, pady=4)

        nb = ttk.Notebook(self.root_frame)
        nb.pack(fill="both", expand=True)
        for key, builder in (
            ("tab_emp", self.build_employees),
            ("tab_abs", self.build_absences),
            ("tab_emp_purch", self.build_emp_purchases),
            ("tab_calc", self.build_calc),
            ("tab_hist", self.build_history),
            ("tab_business", self.build_business),
        ):
            tab = ttk.Frame(nb)
            nb.add(tab, text=self.t(key))
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
            ttk.Label(box, text=self.t(label)).grid(row=0, column=col, sticky="w", padx=4)
            var = tk.StringVar()
            if kind == "emp":
                w = ttk.Combobox(box, textvariable=var, state="readonly", width=22)
                self.emp_combos.append((w, False))
            elif kind == "emp_all":
                w = ttk.Combobox(box, textvariable=var, state="readonly", width=22)
                self.emp_combos.append((w, True))
                var.set(self.t("all"))
            elif isinstance(kind, tuple):
                w = ttk.Combobox(box, textvariable=var, values=kind, state="readonly", width=16)
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

    def button(self, box, key, cmd, col):
        ttk.Button(box, text=self.t(key), command=cmd).grid(row=1, column=col, padx=4)

    def refresh_emp_combos(self):
        names = [f"{e['id']} - {e['name']}" for e in self.db.employees(only_active=True)]
        for combo, with_all in self.emp_combos:
            combo["values"] = ([self.t("all")] if with_all else []) + names

    def emp_id(self, var):
        text = var.get()
        if not text or text == self.t("all"):
            return None
        return int(text.split(" - ")[0])

    def safe(self, fn):
        """Exécute fn en affichant les erreurs."""
        def run():
            try:
                fn()
            except ValueError as err:
                msg = str(err)
                messagebox.showerror(self.t("error"), self.t(msg) if msg in TEXT else msg)
        return run

    def delete_selected(self, tree, table, refresh):
        sel = tree.selection()
        if not sel:
            return
        if messagebox.askyesno(self.t("delete_title"), self.t("delete_confirm")):
            for iid in sel:
                self.db.delete(table, int(iid))
            refresh()

    def require_emp(self, var):
        emp_id = self.emp_id(var)
        if emp_id is None:
            raise ValueError("choose_emp")
        return emp_id

    # ---------- Employés ----------
    def build_employees(self, tab):
        v = self.form(tab, [
            ("name", "name", 24),
            ("pay_type", "pay_type", tuple(self.t(p) for p in calc.PAY_TYPES)),
            ("base", "salary_da", 14),
        ])
        v["active"] = tk.IntVar(value=1)
        ttk.Checkbutton(v["_box"], text=self.t("active"), variable=v["active"]).grid(row=1, column=3, padx=4)
        tree = make_tree(tab, [
            ("name", self.t("name"), 220), ("type", self.t("type"), 150),
            ("base", self.t("salary"), 150), ("rate", self.t("rate"), 150),
            ("active", self.t("active"), 80),
        ])

        def refresh():
            rows = []
            for e in self.db.employees():
                rows.append((e["id"], (e["name"], self.pay_label(e["pay_type"]), calc.fmt_da(e["base_amount"]),
                                       calc.fmt_da(calc.daily_rate(e["pay_type"], e["base_amount"])),
                                       self.t("yes") if e["active"] else self.t("no"))))
            fill_tree(tree, rows)
            self.refresh_emp_combos()

        def values():
            name = v["name"].get().strip()
            if not name:
                raise ValueError("name_required")
            return name, self.pay_from_label(v["pay_type"].get()), parse_amount(v["base"].get())

        def add():
            self.db.add_employee(*values())
            refresh()

        def update():
            sel = tree.selection()
            if not sel:
                raise ValueError("choose_emp")
            self.db.update_employee(int(sel[0]), *values(), active=v["active"].get())
            refresh()

        def on_select(_):
            sel = tree.selection()
            if sel:
                e = self.db.employee(int(sel[0]))
                v["name"].set(e["name"])
                v["pay_type"].set(self.pay_label(e["pay_type"]))
                v["base"].set(str(e["base_amount"]))
                v["active"].set(e["active"])

        tree.bind("<<TreeviewSelect>>", on_select)
        self.button(v["_box"], "add", self.safe(add), 4)
        self.button(v["_box"], "edit", self.safe(update), 5)
        refresh()

    # ---------- Absences ----------
    def build_absences(self, tab):
        v = self.form(tab, [
            ("emp", "employee", "emp"),
            ("date", "date", 12),
            ("days", "days", 6),
            ("note", "note", 24),
        ])
        v["days"].set("1")
        tree = make_tree(tab, [
            ("date", self.t("date"), 120), ("name", self.t("employee"), 220),
            ("days", self.t("days"), 90), ("note", self.t("note"), 300),
        ])

        def refresh():
            fill_tree(tree, [(a["id"], (a["date"], a["name"], a["days"], a["note"])) for a in self.db.absences()])

        def add():
            emp_id = self.require_emp(v["emp"])
            days = parse_amount(v["days"].get())
            self.db.add_absence(emp_id, parse_date(v["date"].get()).isoformat(), days, v["note"].get())
            refresh()

        self.button(v["_box"], "add", self.safe(add), 4)
        self.button(v["_box"], "delete", lambda: self.delete_selected(tree, "absences", refresh), 5)
        refresh()

    # ---------- Achats employés ----------
    def build_emp_purchases(self, tab):
        v = self.form(tab, [
            ("emp", "employee", "emp"),
            ("date", "date", 12),
            ("amount", "amount_da", 12),
            ("desc", "item_advance", 26),
        ])
        tree = make_tree(tab, [
            ("date", self.t("date"), 120), ("name", self.t("employee"), 220),
            ("amount", self.t("amount"), 150), ("desc", self.t("description"), 300),
        ])

        def refresh():
            fill_tree(tree, [(p["id"], (p["date"], p["name"], calc.fmt_da(p["amount"]), p["description"]))
                             for p in self.db.employee_purchases()])

        def add():
            emp_id = self.require_emp(v["emp"])
            self.db.add_employee_purchase(emp_id, parse_date(v["date"].get()).isoformat(),
                                          parse_amount(v["amount"].get()), v["desc"].get())
            refresh()

        self.button(v["_box"], "add", self.safe(add), 4)
        self.button(v["_box"], "delete", lambda: self.delete_selected(tree, "employee_purchases", refresh), 5)
        refresh()

    # ---------- Calcul ----------
    def build_calc(self, tab):
        v = self.form(tab, [
            ("emp", "employee", "emp_all"),
            ("period", "period", (self.t("month"), self.t("week"))),
            ("date", "date_in_period", 12),
        ])
        period_lbl = ttk.Label(tab, text="", font=("TkDefaultFont", 10, "bold"))
        period_lbl.pack(anchor="w", padx=12)
        tree = make_tree(tab, [
            ("name", self.t("employee"), 170), ("gross", self.t("gross"), 130),
            ("abs", self.t("abs_days"), 100), ("absded", self.t("abs_ded"), 140),
            ("achats", self.t("purchases"), 130), ("net", self.t("net_pay"), 160),
        ])
        total_lbl = ttk.Label(tab, text="", font=("TkDefaultFont", 11, "bold"))
        total_lbl.pack(anchor="e", padx=12, pady=6)
        results = {}

        def period():
            d = parse_date(v["date"].get())
            return calc.month_period(d) if v["period"].get() == self.t("month") else calc.week_period(d)

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
                net = calc.fmt_da(slip["net"]) + (f" ({self.t('debt')})" if slip["net"] < 0 else "")
                rows.append((emp["id"], (emp["name"], calc.fmt_da(slip["gross"]), slip["absence_days"],
                                         calc.fmt_da(slip["absence_deduction"]),
                                         calc.fmt_da(slip["purchases_deduction"]), net)))
            fill_tree(tree, rows)
            period_lbl.config(text=self.t("from_to").format(s, e))
            total_lbl.config(text=f"{self.t('total_net')}: {calc.fmt_da(total)}")

        def save():
            ids = [int(i) for i in tree.selection()] or list(results)
            if not ids:
                raise ValueError("calc_first")
            if not messagebox.askyesno(self.t("payment"), self.t("confirm_payments").format(len(ids))):
                return
            today = date.today().isoformat()
            for emp_id in ids:
                s, e, slip = results[emp_id]
                self.db.add_payment(emp_id, s, e, slip, today)
            messagebox.showinfo("OK", self.t("payment_saved"))

        self.button(v["_box"], "calc", self.safe(compute), 3)
        self.button(v["_box"], "save_payment", self.safe(save), 4)

    # ---------- Historique ----------
    def build_history(self, tab):
        v = self.form(tab, [
            ("emp", "employee", "emp_all"),
            ("month", "month_filter", 12),
        ])
        tree = make_tree(tab, [
            ("period", self.t("period"), 190), ("name", self.t("employee"), 160),
            ("gross", self.t("gross"), 120), ("absded", self.t("abs_short"), 110),
            ("achats", self.t("purchases"), 110), ("net", self.t("net"), 120),
            ("paid", self.t("paid_on"), 110),
        ])
        total_lbl = ttk.Label(tab, text="", font=("TkDefaultFont", 11, "bold"))
        total_lbl.pack(anchor="e", padx=12, pady=6)

        def refresh():
            pays = self.db.payments(self.emp_id(v["emp"]), v["month"].get().strip() or None)
            fill_tree(tree, [(p["id"], (f"{p['period_start']} → {p['period_end']}", p["name"],
                                        calc.fmt_da(p["gross"]), calc.fmt_da(p["absence_deduction"]),
                                        calc.fmt_da(p["purchases_deduction"]), calc.fmt_da(p["net"]),
                                        p["paid_on"])) for p in pays])
            total_lbl.config(text=f"{self.t('total_paid')}: {calc.fmt_da(sum(p['net'] for p in pays))}")

        self.button(v["_box"], "show", self.safe(refresh), 2)
        self.button(v["_box"], "delete", lambda: self.delete_selected(tree, "payments", refresh), 3)
        refresh()

    # ---------- Achats entreprise ----------
    def build_business(self, tab):
        v = self.form(tab, [
            ("date", "date", 12),
            ("amount", "amount_da", 12),
            ("desc", "description", 26),
            ("supplier", "supplier", 18),
        ])
        f = self.form(tab, [("month", "month_filter", 12)])
        tree = make_tree(tab, [
            ("date", self.t("date"), 120), ("amount", self.t("amount"), 150),
            ("desc", self.t("description"), 300), ("supplier", self.t("supplier"), 200),
        ])
        total_lbl = ttk.Label(tab, text="", font=("TkDefaultFont", 11, "bold"))
        total_lbl.pack(anchor="e", padx=12, pady=6)

        def refresh():
            rows = self.db.business_purchases(f["month"].get().strip() or None)
            fill_tree(tree, [(p["id"], (p["date"], calc.fmt_da(p["amount"]), p["description"], p["supplier"]))
                             for p in rows])
            total_lbl.config(text=f"{self.t('total_purchases')}: {calc.fmt_da(sum(p['amount'] for p in rows))}")

        def add():
            self.db.add_business_purchase(parse_date(v["date"].get()).isoformat(),
                                          parse_amount(v["amount"].get()), v["desc"].get(), v["supplier"].get())
            refresh()

        self.button(v["_box"], "add", self.safe(add), 4)
        self.button(f["_box"], "show", self.safe(refresh), 1)
        self.button(f["_box"], "delete", lambda: self.delete_selected(tree, "business_purchases", refresh), 2)
        refresh()


def main():
    App(DB()).mainloop()


if __name__ == "__main__":
    main()
