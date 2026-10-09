"""Application de gestion des salaires (English / Français).

Lancer: python -m salary_app.app
"""
import math
import os
import re
import subprocess
import sys
import tempfile
import tkinter as tk
import traceback
import webbrowser
from datetime import date
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from . import __version__, calc, theme
from .chart import BarChart
from .datepicker import MONTHS_SHORT, DatePicker
from .db import DB, DB_NAME, default_db_path
from .report import payslip_section, payslips_document
from .xlsx import write_xlsx

LANGS = ("en", "fr")

# clé -> (English, Français)
TEXT = {
    "title": ("Salary management", "Gestion des salaires"),
    "subtitle": ("Salaries, absences, purchases and bonuses", "Salaires, absences, achats et primes"),
    "switch": ("Français", "English"),
    "tab_dash": ("Dashboard", "Tableau de bord"),
    "tab_dash_sub": ("Overview of the selected month", "Vue d'ensemble du mois choisi"),
    "tab_emp": ("Employees", "Employés"),
    "tab_emp_sub": ("Add employees and their salary. Select a line to edit it.",
                    "Ajoutez les employés et leur salaire. Sélectionnez une ligne pour la modifier."),
    "tab_abs": ("Absences", "Absences"),
    "tab_abs_sub": ("Absent days are deducted at the daily rate.", "Les jours d'absence sont retenus au taux journalier."),
    "tab_emp_purch": ("Employee purchases", "Achats employés"),
    "tab_emp_purch_sub": ("Items and cash advances, deducted from the salary of the same period.",
                          "Articles et avances, déduits du salaire de la même période."),
    "tab_bonus": ("Bonuses & overtime", "Primes & heures sup"),
    "tab_bonus_sub": ("Overtime is paid +50% of the hourly rate (Law 90-11).",
                      "Les heures sup sont payées +50 % du taux horaire (loi 90-11)."),
    "tab_calc": ("Salary calculation", "Calcul salaire"),
    "tab_calc_sub": ("Calculate, save payments and print payslips. Select lines to act on some employees only.",
                     "Calculez, enregistrez les paiements et imprimez les fiches. Sélectionnez des lignes pour "
                     "n'agir que sur certains employés."),
    "tab_hist": ("History", "Historique"),
    "tab_hist_sub": ("Saved salary payments.", "Paiements de salaire enregistrés."),
    "tab_business": ("Business purchases", "Achats entreprise"),
    "tab_business_sub": ("Purchases of the business (not linked to salaries).",
                         "Achats de l'entreprise (sans lien avec les salaires)."),
    "monthly": ("Monthly", "Mensuel"),
    "weekly": ("Weekly", "Hebdomadaire"),
    "daily": ("Daily", "Journalier"),
    "month": ("Month", "Mois"),
    "week": ("Week", "Semaine"),
    "all": ("All", "Tous"),
    "error": ("Error", "Erreur"),
    "warning": ("Warning", "Attention"),
    "err_date": ("Invalid date (use YYYY-MM-DD or DD/MM/YYYY)", "Date invalide (AAAA-MM-JJ ou JJ/MM/AAAA)"),
    "err_amount": ("Invalid number", "Nombre invalide"),
    "err_positive": ("The amount must be greater than 0", "Le montant doit être supérieur à 0"),
    "err_days": ("Absent days must be between 0 and 31 (e.g. 1 or 0.5)",
                 "Les jours d'absence doivent être entre 0 et 31 (ex. 1 ou 0,5)"),
    "err_month": ("Invalid month (use YYYY-MM or MM/YYYY)", "Mois invalide (AAAA-MM ou MM/AAAA)"),
    "invalid_backup": ("This file is not a valid backup", "Ce fichier n'est pas une sauvegarde valide"),
    "choose_emp": ("Choose an employee", "Choisir un employé"),
    "select_one": ("Select one line in the table first", "Sélectionnez d'abord une ligne du tableau"),
    "name_required": ("Name is required", "Nom obligatoire"),
    "delete_title": ("Delete", "Supprimer"),
    "delete_confirm": ("Delete the selected line(s)?", "Supprimer la/les ligne(s) ?"),
    "name": ("Name", "Nom"),
    "pay_type": ("Pay type", "Type de paie"),
    "salary_da": ("Salary (DA)", "Salaire (DA)"),
    "salary": ("Salary", "Salaire"),
    "type": ("Type", "Type"),
    "rate": ("Daily rate", "Taux jour"),
    "hour_rate": ("Hourly rate", "Taux horaire"),
    "active": ("Active", "Actif"),
    "yes": ("Yes", "Oui"),
    "no": ("No", "Non"),
    "add": ("Add", "Ajouter"),
    "edit": ("Save changes", "Enregistrer les modifications"),
    "delete": ("Delete", "Supprimer"),
    "clear": ("Clear", "Effacer"),
    "employee": ("Employee", "Employé"),
    "date": ("Date", "Date"),
    "days": ("Days", "Jours"),
    "note": ("Note", "Remarque"),
    "amount_da": ("Amount (DA)", "Montant (DA)"),
    "amount": ("Amount", "Montant"),
    "item_advance": ("Item / advance", "Article / avance"),
    "description": ("Description", "Description"),
    "bonus": ("Bonus", "Prime"),
    "overtime": ("Overtime", "Heures sup"),
    "bonuses": ("Bonuses", "Primes"),
    "hours": ("Hours", "Heures"),
    "amount_or_hours": ("DA or hours", "DA ou heures"),
    "overtime_cap": ("This makes {} h of overtime this week. The legal limit is 8 h per week. Continue?",
                     "Cela fait {} h supplémentaires cette semaine. La limite légale est de 8 h par semaine. "
                     "Continuer ?"),
    "period": ("Period", "Période"),
    "date_in_period": ("Date in period", "Date dans la période"),
    "gross": ("Gross", "Brut"),
    "abs_days": ("Absent days", "Jours abs."),
    "abs_ded": ("Absence deduction", "Retenue abs."),
    "purchases": ("Purchases", "Achats"),
    "net_pay": ("Net to pay", "Net à payer"),
    "status": ("Status", "Statut"),
    "paid": ("✔ Paid", "✔ Payé"),
    "not_paid": ("Not paid", "Non payé"),
    "debt": ("owed", "reste dû"),
    "from_to": ("From {} to {}", "Du {} au {}"),
    "total_net": ("Total net", "Total net"),
    "calc": ("Calculate", "Calculer"),
    "save_payment": ("Save payment", "Enregistrer paiement"),
    "calc_first": ("Calculate first", "Calculer d'abord"),
    "payment": ("Payment", "Paiement"),
    "confirm_payments": ("Save {} payment(s)?", "Enregistrer {} paiement(s) ?"),
    "already_paid": ("{} of these employees already have a saved payment for this period. "
                     "It will be replaced by the new calculation. Continue?",
                     "{} de ces employés ont déjà un paiement enregistré pour cette période. "
                     "Il sera remplacé par le nouveau calcul. Continuer ?"),
    "payment_saved": ("{} payment(s) saved", "{} paiement(s) enregistré(s)"),
    "payslip": ("Payslip", "Fiche de paie"),
    "payslips": ("Payslips", "Fiches de paie"),
    "print": ("Print", "Imprimer"),
    "sign_employer": ("Employer signature", "Signature de l'employeur"),
    "sign_employee": ("Employee signature", "Signature de l'employé"),
    "month_filter": ("Month (YYYY-MM, empty = all)", "Mois (AAAA-MM, vide = tout)"),
    "show": ("Show", "Afficher"),
    "abs_short": ("Absences", "Abs."),
    "net": ("Net", "Net"),
    "paid_on": ("Paid on", "Payé le"),
    "total_paid": ("Total paid", "Total payé"),
    "supplier": ("Supplier", "Fournisseur"),
    "total_purchases": ("Total purchases", "Total achats"),
    "export": ("Export Excel", "Exporter Excel"),
    "no_data": ("Nothing to export", "Rien à exporter"),
    "saved_to": ("Saved to:\n{}", "Enregistré dans :\n{}"),
    "search": ("Search", "Rechercher"),
    "rows": ("{} line(s)", "{} ligne(s)"),
    "backup": ("Backup", "Sauvegarder"),
    "restore": ("Restore", "Restaurer"),
    "restore_confirm": ("Replace ALL current data with this backup?",
                        "Remplacer TOUTES les données actuelles par cette sauvegarde ?"),
    "restore_done": ("Data restored", "Données restaurées"),
    "settings": ("Settings", "Paramètres"),
    "company": ("Company", "Entreprise"),
    "company_name": ("Company name", "Nom de l'entreprise"),
    "company_address": ("Address", "Adresse"),
    "company_phone": ("Phone", "Téléphone"),
    "company_nif": ("Tax ID (NIF)", "NIF"),
    "company_hint": ("Shown on payslips.", "Affiché sur les fiches de paie."),
    "data_file": ("Data file", "Fichier de données"),
    "data_hint": ("All your data is in this file. Use Backup regularly (e.g. to a USB key).",
                  "Toutes vos données sont dans ce fichier. Utilisez Sauvegarder régulièrement (ex. clé USB)."),
    "open_folder": ("Open folder", "Ouvrir le dossier"),
    "save": ("Save", "Enregistrer"),
    "cancel": ("Cancel", "Annuler"),
    "kpi_emp": ("Active employees", "Employés actifs"),
    "kpi_emp_cap": ("{} absence day(s) this month", "{} jour(s) d'absence ce mois"),
    "kpi_topay": ("Salaries to pay", "Salaires à payer"),
    "kpi_topay_cap": ("Estimated net, all active employees", "Net estimé, tous les employés actifs"),
    "kpi_paid": ("Salaries paid", "Salaires payés"),
    "kpi_paid_cap": ("{} payment(s) saved", "{} paiement(s) enregistré(s)"),
    "kpi_bonus": ("Bonuses & overtime", "Primes & heures sup"),
    "kpi_purch": ("Employee purchases", "Achats employés"),
    "kpi_business": ("Business purchases", "Achats entreprise"),
    "kpi_month_cap": ("This month", "Ce mois"),
    "chart_empty": ("No salaries paid or business purchases in these months yet",
                    "Aucun salaire payé ni achat entreprise sur ces mois pour l'instant"),
    "chart_title": ("Salaries paid and business purchases — last 6 months",
                    "Salaires payés et achats entreprise — 6 derniers mois"),
}

COMPANY_KEYS = ("company_name", "company_address", "company_phone", "company_nif")


def parse_date(text):
    """AAAA-MM-JJ, ou JJ/MM/AAAA et JJ-MM-AAAA (format courant en Algérie)."""
    text = text.strip()
    m = re.fullmatch(r"(\d{1,2})[/.-](\d{1,2})[/.-](\d{4})", text)
    try:
        if m:
            return date(int(m.group(3)), int(m.group(2)), int(m.group(1)))
        if re.fullmatch(r"\d{4}-\d{2}-\d{2}", text):
            return date.fromisoformat(text)
    except ValueError:
        pass
    raise ValueError("err_date")


def parse_amount(text):
    """Nombre saisi: '30000', '30 000', '30.000' ou '30,000' (= trente mille), '1500,50', '30.000,50'."""
    s = text.strip().replace(" ", "").replace("\u00a0", "").replace("\u202f", "")
    if "," in s and "." in s:  # le dernier séparateur est la virgule décimale
        dec = "," if s.rfind(",") > s.rfind(".") else "."
        s = s.replace("." if dec == "," else ",", "").replace(dec, ".")
    elif re.fullmatch(r"-?[1-9]\d{0,2}([.,]\d{3})+", s):  # séparateurs de milliers
        s = s.replace(".", "").replace(",", "")
    else:
        s = s.replace(",", ".")
    if not re.fullmatch(r"-?(\d+\.?\d*|\.\d+)", s):
        raise ValueError("err_amount")
    value = float(s)
    if not math.isfinite(value):
        raise ValueError("err_amount")
    return value


def parse_positive(text):
    value = parse_amount(text)
    if value <= 0:
        raise ValueError("err_positive")
    return value


def parse_days(text):
    value = parse_amount(text)
    if not 0 < value <= 31:
        raise ValueError("err_days")
    return value


def parse_month(text):
    """'' -> None (tout), '2026-09' -> '2026-09'."""
    text = text.strip()
    if not text:
        return None
    m = re.fullmatch(r"(0?[1-9]|1[0-2])[/.-](\d{4})", text)  # aussi MM/AAAA
    if m:
        return f"{m.group(2)}-{int(m.group(1)):02d}"
    if not re.fullmatch(r"\d{4}-(0[1-9]|1[0-2])", text):
        raise ValueError("err_month")
    return text


def shift_month(d, step):
    m = d.month - 1 + step
    return date(d.year + m // 12, m % 12 + 1, 1)


def apply_filter(tree):
    """Affiche les lignes qui contiennent le texte recherché (lignes alternées, compteur)."""
    q = tree.search_var.get().strip().lower() if hasattr(tree, "search_var") else ""
    tree.delete(*tree.get_children())
    visible = [r for r in tree.all_rows if not q or q in " ".join(map(str, r[1])).lower()]
    for n, (iid, shown, tags, _) in enumerate(visible):
        tree.insert("", "end", iid=str(iid), values=shown, tags=tags + (("odd",) if n % 2 else ()))
    tree.raw_rows = [r[3] for r in visible]
    if hasattr(tree, "count_lbl"):
        tree.count_lbl.config(text=tree.count_fmt.format(len(visible)))


def money(*cols):
    """Colonnes à afficher en DA."""
    return {c: calc.fmt_da for c in cols}


def fill_tree(tree, rows, fmt=None, neg_col=None):
    """rows = [(iid, valeurs brutes)]; fmt = {colonne: fonction d'affichage}.
    Les valeurs brutes sont gardées pour l'export Excel."""
    fmt = fmt or {}
    tree.all_rows = []
    for iid, values in rows:
        shown = [fmt[i](v) if i in fmt else v for i, v in enumerate(values)]
        tags = ("neg",) if neg_col is not None and values[neg_col] < 0 else ()
        tree.all_rows.append((iid, shown, tags, list(values)))
    apply_filter(tree)


class Cancelled(Exception):
    """L'utilisateur a annulé une action (ce n'est pas une erreur)."""


def open_folder(path):
    """Ouvre le dossier contenant `path` dans l'explorateur de fichiers."""
    folder = os.path.dirname(os.path.abspath(path))
    if sys.platform == "win32":
        os.startfile(folder)
    else:
        subprocess.Popen(["open" if sys.platform == "darwin" else "xdg-open", folder])


def safe_filename(text):
    return re.sub(r"[^\w-]+", "_", text).strip("_") or "fiche"


class App(tk.Tk):
    def __init__(self, db):
        super().__init__()
        self.db = db
        self.lang = db.get_setting("lang", "en")
        theme.apply(self)
        icon = Path(__file__).resolve().parent / "assets" / "icon.png"
        if icon.exists():
            try:
                self._icon = tk.PhotoImage(file=str(icon))
                self.iconphoto(True, self._icon)
            except tk.TclError:
                pass
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        w, h = min(theme.px(1280), sw - 40), min(theme.px(780), sh - 80)
        self.geometry(f"{w}x{h}+{max(0, (sw - w) // 2)}+{max(0, (sh - h) // 3)}")
        self.minsize(min(theme.px(1120), sw - 40), min(theme.px(640), sh - 80))
        self.root_frame = None
        self.current_page = 0
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

    # ---------- structure: menu latéral + pages ----------
    PAGES = ("tab_dash", "tab_emp", "tab_abs", "tab_emp_purch", "tab_bonus", "tab_calc", "tab_hist",
             "tab_business")

    def build(self):
        """(Re)construit toute l'interface dans la langue courante."""
        if self.root_frame:
            self.root_frame.destroy()
        self.title(f"{self.t('title')} v{__version__}")
        self.emp_combos, self.on_show, self.nav = [], {}, []
        self.root_frame = ttk.Frame(self)
        self.root_frame.pack(fill="both", expand=True)
        self.build_sidebar()

        main = ttk.Frame(self.root_frame)
        main.pack(side="left", fill="both", expand=True)
        self.nb = ttk.Notebook(main, style="Pages.TNotebook")
        self.nb.pack(fill="both", expand=True)
        builders = (self.build_dashboard, self.build_employees, self.build_absences, self.build_emp_purchases,
                    self.build_bonuses, self.build_calc, self.build_history, self.build_business)
        for i, (key, builder) in enumerate(zip(self.PAGES, builders)):
            tab = ttk.Frame(self.nb)
            self.nb.add(tab, text=self.t(key))
            self._page = i
            builder(self.page(tab, key))
        self.show_page(self.current_page)

    def build_sidebar(self):
        side = tk.Frame(self.root_frame, background=theme.SIDEBAR, width=theme.px(236))
        side.pack(side="left", fill="y")
        side.pack_propagate(False)
        family, size = theme.FONT
        company = self.db.get_setting("company_name", "")
        tk.Label(side, text=company or self.t("title"), background=theme.SIDEBAR, foreground=theme.WHITE,
                 font=(family, size + 4, "bold"), wraplength=theme.px(200), justify="left", anchor="w"
                 ).pack(fill="x", padx=20, pady=(22, 0))
        tk.Label(side, text=f"{self.t('title')} v{__version__}" if company else self.t("subtitle"),
                 background=theme.SIDEBAR, foreground=theme.SIDEBAR_TEXT, font=(family, size - 1),
                 wraplength=theme.px(200), justify="left", anchor="w").pack(fill="x", padx=20, pady=(2, 18))

        def item(parent, key, command, small=False):
            lbl = tk.Label(parent, text=f"{theme.ICONS.get(key, '')}   {self.t(key)}", anchor="w",
                           background=theme.SIDEBAR, foreground=theme.SIDEBAR_TEXT, cursor="hand2",
                           font=(family, size - (1 if small else 0)), padx=14, pady=6 if small else 9)
            lbl.pack(fill="x", padx=10, pady=1)
            lbl.bind("<Button-1>", lambda e: command())
            lbl.bind("<Enter>", lambda e: lbl.cget("background") == theme.ACCENT or
                     lbl.configure(background=theme.SIDEBAR_HOVER))
            lbl.bind("<Leave>", lambda e: lbl.cget("background") == theme.ACCENT or
                     lbl.configure(background=theme.SIDEBAR))
            return lbl

        for i, key in enumerate(self.PAGES):
            self.nav.append(item(side, key, lambda i=i: self.show_page(i)))

        tools = tk.Frame(side, background=theme.SIDEBAR)
        tools.pack(side="bottom", fill="x", pady=14)
        for key, cmd in (("settings", self.open_settings), ("backup", self.safe(self.backup)),
                         ("restore", self.safe(self.restore)), ("switch", self.switch_lang)):
            item(tools, key, cmd, small=True)

    def show_page(self, i):
        self.current_page = i
        self.nb.select(i)
        for n, lbl in enumerate(self.nav):
            active = n == i
            lbl.configure(background=theme.ACCENT if active else theme.SIDEBAR,
                          foreground=theme.WHITE if active else theme.SIDEBAR_TEXT)
        self.refresh_emp_combos()
        if i in self.on_show:
            self.safe(self.on_show[i])()

    def page(self, tab, key):
        """En-tête de page (titre + sous-titre); retourne le cadre du contenu."""
        head = ttk.Frame(tab, padding=(24, 18, 24, 6))
        head.pack(fill="x")
        ttk.Label(head, text=self.t(key), style="PageTitle.TLabel").pack(anchor="w")
        ttk.Label(head, text=self.t(f"{key}_sub"), style="Muted.TLabel").pack(anchor="w", pady=(2, 0))
        body = ttk.Frame(tab, padding=(24, 8, 24, 18))
        body.pack(fill="both", expand=True)
        body.head = head
        return body

    def show_hook(self, fn):
        """Fonction appelée chaque fois que la page en construction est affichée."""
        self.on_show[self._page] = fn

    # ---------- helpers ----------
    def form(self, parent, fields):
        """Carte de saisie. fields = [(clé, label, type)]. Retourne dict de variables (+ '_box', '_defaults')."""
        box = ttk.Frame(parent, style="Card.TFrame", padding=(16, 12))
        box.pack(fill="x", pady=(0, 12))
        vars_, defaults = {}, {}
        for col, (key, label, kind) in enumerate(fields):
            ttk.Label(box, text=self.t(label), style="Card.TLabel").grid(row=0, column=col, sticky="w", padx=4)
            var = tk.StringVar()
            if kind in ("emp", "emp_all"):
                w = ttk.Combobox(box, textvariable=var, state="readonly", width=22)
                self.emp_combos.append((w, kind == "emp_all"))
                if kind == "emp_all":
                    var.set(self.t("all"))
            elif isinstance(kind, tuple):
                w = ttk.Combobox(box, textvariable=var, values=kind, state="readonly", width=16)
                var.set(kind[0])
            elif key == "date":
                w = ttk.Frame(box, style="CardInner.TFrame")
                ttk.Entry(w, textvariable=var, width=kind or 12).pack(side="left")
                pick = ttk.Button(w, text="▦", width=3, style="Icon.TButton")
                pick.configure(command=lambda b=pick, v=var: DatePicker(b, v, self.lang, calc.WEEK_START))
                pick.pack(side="left", padx=(2, 0))
                var.set(date.today().isoformat())
            else:
                w = ttk.Entry(box, textvariable=var, width=kind or 16)
                if key == "month":
                    var.set(date.today().strftime("%Y-%m"))
            last = col == len(fields) - 1 and isinstance(w, ttk.Entry)
            w.grid(row=1, column=col, sticky="ew" if last else "w", padx=4)
            if last:  # le dernier champ texte s'élargit avec la fenêtre
                box.columnconfigure(col, weight=1)
            vars_[key] = var
            defaults[key] = var.get()
        vars_["_box"], vars_["_defaults"] = box, defaults
        return vars_

    def reset(self, v, keys=None):
        for key in keys or v["_defaults"]:
            if key == "date":
                v[key].set(date.today().isoformat())
            else:
                v[key].set(v["_defaults"][key])

    def button(self, box, key, cmd):
        """Ajoute un bouton dans la barre d'actions de la carte."""
        bar = getattr(box, "actions", None)
        if bar is None:
            bar = box.actions = ttk.Frame(box, style="CardInner.TFrame")
            bar.grid(row=2, column=0, columnspan=20, sticky="w", pady=(10, 0))
        btn = ttk.Button(bar, text=theme.button_text(key, self.t(key)), command=cmd, style=theme.button_style(key))
        btn.pack(side="left", padx=4)
        return btn

    def export_button(self, box, tree, name):
        self.button(box, "export", self.safe(lambda: self.export_tree(tree, name)))

    def make_tree(self, parent, columns, height=12):
        """Carte avec tableau, recherche et compteur. columns = [(id, titre, largeur, 'e' si montant)]."""
        card = ttk.Frame(parent, style="Card.TFrame", padding=1)
        card.pack(fill="both", expand=True)
        head = ttk.Frame(card, style="CardInner.TFrame", padding=(12, 8))
        head.pack(fill="x")
        count = ttk.Label(head, text="", style="Card.TLabel")
        count.pack(side="left")
        search_var = tk.StringVar()
        ttk.Entry(head, textvariable=search_var, width=24).pack(side="right")
        ttk.Label(head, text=f"⌕ {self.t('search')}", style="Card.TLabel").pack(side="right", padx=(0, 6))
        frame = ttk.Frame(card, style="CardInner.TFrame")
        frame.pack(fill="both", expand=True)
        tree = ttk.Treeview(frame, columns=[c[0] for c in columns], show="headings", height=height)
        for cid, title, width, *anchor in columns:
            tree.heading(cid, text=title, anchor=anchor[0] if anchor else "center")
            tree.column(cid, width=width, anchor=anchor[0] if anchor else "center")
        theme.style_tree(tree)
        tree.all_rows, tree.raw_rows = [], []
        tree.search_var, tree.count_lbl, tree.count_fmt = search_var, count, self.t("rows")
        tree.head = head
        search_var.trace_add("write", lambda *a: apply_filter(tree))
        sb = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=sb.set)
        tree.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")
        return tree

    def refresh_emp_combos(self):
        names = [f"{e['id']} - {e['name']}" for e in self.db.employees(only_active=True)]
        for combo, with_all in self.emp_combos:
            combo["values"] = ([self.t("all")] if with_all else []) + names

    def emp_label(self, emp_id):
        emp = self.db.employee(emp_id)
        return f"{emp['id']} - {emp['name']}" if emp else ""

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
            except (ValueError, OSError) as err:
                msg = str(err)
                messagebox.showerror(self.t("error"), self.t(msg) if msg in TEXT else msg)
        return run

    def delete_selected(self, tree, table, refresh):
        sel = tree.selection()
        if not sel:
            raise ValueError("select_one")
        if messagebox.askyesno(self.t("delete_title"), self.t("delete_confirm")):
            for iid in sel:
                self.db.delete(table, int(iid))
            refresh()

    def require_emp(self, var):
        emp_id = self.emp_id(var)
        if emp_id is None:
            raise ValueError("choose_emp")
        return emp_id

    def crud(self, v, tree, table, refresh, add, update, load, export_name, after_add=()):
        """Boutons Ajouter / Enregistrer les modifications / Supprimer / Effacer / Export
        + chargement de la ligne sélectionnée dans le formulaire."""
        def selected_id():
            sel = tree.selection()
            if len(sel) != 1:
                raise ValueError("select_one")
            return int(sel[0])

        def on_select(_):
            sel = tree.selection()
            if len(sel) == 1:
                row = self.db.employee(int(sel[0])) if table == "employees" else self.db.get(table, int(sel[0]))
                if row:
                    load(row)

        def do_add():
            try:
                add()
            except Cancelled:
                return
            refresh()
            self.reset(v, after_add)

        def do_update():
            row_id = selected_id()
            try:
                update(row_id)
            except Cancelled:
                return
            refresh()
            if tree.exists(str(row_id)):
                tree.selection_set(str(row_id))

        def clear():
            tree.selection_remove(tree.selection())
            self.reset(v)

        tree.bind("<<TreeviewSelect>>", on_select)
        box = v["_box"]
        self.button(box, "add", self.safe(do_add))
        self.button(box, "edit", self.safe(do_update))
        if table != "employees":
            self.button(box, "delete", self.safe(lambda: self.delete_selected(tree, table, refresh)))
        self.button(box, "clear", clear)
        self.export_button(box, tree, export_name)

    # ---------- Export / sauvegarde ----------
    def export_tree(self, tree, name):
        if not tree.raw_rows:
            raise ValueError("no_data")
        path = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel", "*.xlsx")],
                                            initialfile=f"{safe_filename(name)}_{date.today().isoformat()}.xlsx")
        if not path:
            return
        headers = [tree.heading(c)["text"] for c in tree["columns"]]
        write_xlsx(path, headers, tree.raw_rows, sheet_name=name)
        messagebox.showinfo("OK", self.t("saved_to").format(path))

    def backup(self):
        path = filedialog.asksaveasfilename(defaultextension=".db", filetypes=[("Backup", "*.db")],
                                            initialfile=f"salaires_backup_{date.today().isoformat()}.db")
        if path:
            self.db.backup_to(path)
            messagebox.showinfo("OK", self.t("saved_to").format(path))

    def restore(self):
        path = filedialog.askopenfilename(filetypes=[("Backup", "*.db")])
        if path and messagebox.askyesno(self.t("restore"), self.t("restore_confirm")):
            self.db.restore_from(path)
            self.lang = self.db.get_setting("lang", self.lang)
            self.build()
            messagebox.showinfo("OK", self.t("restore_done"))

    # ---------- Paramètres entreprise ----------
    def company(self):
        return {k: self.db.get_setting(k, "") for k in COMPANY_KEYS}

    def open_settings(self):
        win = tk.Toplevel(self)
        win.title(self.t("settings"))
        win.configure(background=theme.BG)
        win.transient(self)
        win.resizable(False, False)
        frame = ttk.Frame(win, padding=20)
        frame.pack(fill="both", expand=True)
        ttk.Label(frame, text=self.t("company"), style="Period.TLabel").grid(row=0, column=0, columnspan=2,
                                                                              sticky="w")
        ttk.Label(frame, text=self.t("company_hint"), style="Muted.TLabel").grid(row=1, column=0, columnspan=2,
                                                                                  sticky="w", pady=(0, 10))
        vars_ = {}
        for r, key in enumerate(COMPANY_KEYS, start=2):
            ttk.Label(frame, text=self.t(key)).grid(row=r, column=0, sticky="w", pady=4, padx=(0, 12))
            vars_[key] = tk.StringVar(value=self.db.get_setting(key, ""))
            ttk.Entry(frame, textvariable=vars_[key], width=40).grid(row=r, column=1, pady=4)

        def save():
            for key, var in vars_.items():
                self.db.set_setting(key, var.get().strip())
            win.destroy()
            self.build()

        r = len(COMPANY_KEYS) + 2
        ttk.Separator(frame).grid(row=r, column=0, columnspan=2, sticky="ew", pady=14)
        ttk.Label(frame, text=self.t("data_file"), style="Period.TLabel").grid(row=r + 1, column=0, columnspan=2,
                                                                                sticky="w")
        ttk.Label(frame, text=self.t("data_hint"), style="Muted.TLabel", wraplength=theme.px(460)).grid(
            row=r + 2, column=0, columnspan=2, sticky="w")
        path_var = tk.StringVar(value=os.path.abspath(self.db.path) if self.db.path != ":memory:" else self.db.path)
        win.path_var = path_var  # garder une référence, sinon le champ s'affiche vide
        path_entry = ttk.Entry(frame, textvariable=path_var, state="readonly", width=40)
        path_entry.grid(row=r + 3, column=1, pady=6, sticky="ew")
        path_entry.bind("<Configure>", lambda e: path_entry.xview_moveto(1))  # montrer la fin du chemin
        ttk.Button(frame, text=self.t("open_folder"), command=self.safe(lambda: open_folder(self.db.path))).grid(
            row=r + 3, column=0, sticky="w", pady=6)

        buttons = ttk.Frame(frame)
        buttons.grid(row=r + 4, column=0, columnspan=2, sticky="e", pady=(14, 0))
        ttk.Button(buttons, text=self.t("cancel"), command=win.destroy).pack(side="right", padx=(6, 0))
        ttk.Button(buttons, text=theme.button_text("save", self.t("save")), command=save,
                   style="Accent.TButton").pack(side="right")
        win.grab_set()
        return win

    # ---------- Calculs partagés ----------
    def compute_slips(self, start, end, emp_id=None):
        """[(employé, fiche)] pour la période; tous les employés actifs si emp_id est None."""
        s, e = start.isoformat(), end.isoformat()
        emps = [self.db.employee(emp_id)] if emp_id else self.db.employees(only_active=True)
        return [(emp, calc.compute_payslip(emp["pay_type"], emp["base_amount"],
                                           self.db.absence_days(emp["id"], s, e),
                                           self.db.purchases_total(emp["id"], s, e), start, end,
                                           bonuses_total=self.db.bonuses_total(emp["id"], s, e)))
                for emp in emps if emp]

    # ---------- Tableau de bord ----------
    def build_dashboard(self, body):
        nav = ttk.Frame(body.head)
        nav.place(relx=1.0, x=-24, y=22, anchor="ne")
        month_lbl = ttk.Label(nav, text="", style="Period.TLabel", width=14, anchor="center")
        state = {"month": date.today().replace(day=1)}
        ttk.Button(nav, text="‹", width=3, command=lambda: move(-1)).pack(side="left")
        month_lbl.pack(side="left", padx=6)
        ttk.Button(nav, text="›", width=3, command=lambda: move(1)).pack(side="left")

        grid = ttk.Frame(body)
        grid.pack(fill="x")
        tiles = {}
        for n, key in enumerate(("kpi_emp", "kpi_topay", "kpi_paid", "kpi_bonus", "kpi_purch", "kpi_business")):
            card = ttk.Frame(grid, style="Card.TFrame", padding=(16, 12))
            card.grid(row=n // 3, column=n % 3, sticky="nsew", padx=(0 if n % 3 == 0 else 6, 0 if n % 3 == 2 else 6),
                      pady=(0, 12))
            ttk.Label(card, text=self.t(key), style="Card.TLabel").pack(anchor="w")
            value = ttk.Label(card, text="", style="KpiValue.TLabel")
            value.pack(anchor="w", pady=(4, 0))
            caption = ttk.Label(card, text="", style="Card.TLabel")
            caption.pack(anchor="w")
            tiles[key] = (value, caption)
        for c in range(3):
            grid.columnconfigure(c, weight=1, uniform="kpi")

        chart_card = ttk.Frame(body, style="Card.TFrame", padding=(16, 12))
        chart_card.pack(fill="both", expand=True)
        ttk.Label(chart_card, text=self.t("chart_title"), style="CardTitle.TLabel").pack(anchor="w")
        chart = BarChart(chart_card)
        chart.pack(fill="both", expand=True, pady=(6, 0))
        body.tiles, body.chart = tiles, chart

        def set_tile(key, value, caption="", negative=False):
            tiles[key][0].configure(text=value, style="KpiNeg.TLabel" if negative else "KpiValue.TLabel")
            tiles[key][1].configure(text=caption)

        def refresh():
            m = state["month"]
            key = m.strftime("%Y-%m")
            month_lbl.configure(text=f"{MONTHS_SHORT[self.lang][m.month - 1]} {m.year}")
            start, end = calc.month_period(m)
            to_pay = sum(slip["net"] for _, slip in self.compute_slips(start, end))
            month_cap = self.t("kpi_month_cap")
            set_tile("kpi_emp", str(len(self.db.employees(only_active=True))),
                     self.t("kpi_emp_cap").format(calc.fmt_num(self.db.month_sum("absences", key))))
            set_tile("kpi_topay", calc.fmt_da(to_pay), self.t("kpi_topay_cap"), negative=to_pay < 0)
            set_tile("kpi_paid", calc.fmt_da(self.db.month_sum("payments", key)),
                     self.t("kpi_paid_cap").format(len(self.db.payments(month=key))))
            set_tile("kpi_bonus", calc.fmt_da(self.db.month_sum("bonuses", key)), month_cap)
            set_tile("kpi_purch", calc.fmt_da(self.db.month_sum("employee_purchases", key)), month_cap)
            set_tile("kpi_business", calc.fmt_da(self.db.month_sum("business_purchases", key)), month_cap)
            months = [shift_month(m, -k) for k in range(5, -1, -1)]
            labels = [f"{MONTHS_SHORT[self.lang][d.month - 1]} {str(d.year)[2:]}" for d in months]
            keys = [d.strftime("%Y-%m") for d in months]
            chart.set_data(labels, [
                (self.t("kpi_paid"), theme.SERIES[0], [self.db.month_sum("payments", k) for k in keys]),
                (self.t("kpi_business"), theme.SERIES[1], [self.db.month_sum("business_purchases", k) for k in keys]),
            ], empty_text=self.t("chart_empty"))

        def move(step):
            state["month"] = shift_month(state["month"], step)
            refresh()

        body.refresh = refresh
        self.show_hook(refresh)

    # ---------- Employés ----------
    def build_employees(self, body):
        v = self.form(body, [
            ("name", "name", 26),
            ("pay_type", "pay_type", tuple(self.t(p) for p in calc.PAY_TYPES)),
            ("base", "salary_da", 14),
        ])
        v["active"] = tk.IntVar(value=1)
        ttk.Checkbutton(v["_box"], text=self.t("active"), variable=v["active"], style="Card.TCheckbutton"
                        ).grid(row=1, column=3, padx=8)
        tree = self.make_tree(body, [
            ("name", self.t("name"), 200), ("type", self.t("type"), 130),
            ("base", self.t("salary"), 140, "e"), ("rate", self.t("rate"), 130, "e"),
            ("hrate", self.t("hour_rate"), 130, "e"), ("active", self.t("active"), 80),
        ])

        def refresh():
            rows = []
            for e in self.db.employees():
                p, b = e["pay_type"], e["base_amount"]
                rows.append((e["id"], (e["name"], self.pay_label(p), b, round(calc.daily_rate(p, b), 2),
                                       round(calc.hourly_rate(p, b), 2),
                                       self.t("yes") if e["active"] else self.t("no"))))
            fill_tree(tree, rows, money(2, 3, 4))
            self.refresh_emp_combos()

        def values():
            name = v["name"].get().strip()
            if not name:
                raise ValueError("name_required")
            return name, self.pay_from_label(v["pay_type"].get()), parse_positive(v["base"].get())

        def load(e):
            v["name"].set(e["name"])
            v["pay_type"].set(self.pay_label(e["pay_type"]))
            v["base"].set(calc.fmt_num(e["base_amount"]))
            v["active"].set(e["active"])

        v["_defaults"]["active"] = 1
        self.crud(v, tree, "employees", refresh,
                  add=lambda: self.db.add_employee(*values()),
                  update=lambda row_id: self.db.update_employee(row_id, *values(), active=v["active"].get()),
                  load=load, export_name=self.t("tab_emp"), after_add=("name", "base"))
        refresh()
        self.show_hook(refresh)

    # ---------- Absences ----------
    def build_absences(self, body):
        v = self.form(body, [
            ("emp", "employee", "emp"),
            ("date", "date", 12),
            ("days", "days", 6),
            ("note", "note", 30),
        ])
        v["days"].set("1")
        v["_defaults"]["days"] = "1"
        tree = self.make_tree(body, [
            ("date", self.t("date"), 120), ("name", self.t("employee"), 220),
            ("days", self.t("days"), 90), ("note", self.t("note"), 320),
        ])

        def refresh():
            fill_tree(tree, [(a["id"], (a["date"], a["name"], a["days"], a["note"])) for a in self.db.absences()],
                      {2: calc.fmt_num})

        def values():
            return (self.require_emp(v["emp"]), parse_date(v["date"].get()).isoformat(),
                    parse_days(v["days"].get()), v["note"].get().strip())

        def load(a):
            v["emp"].set(self.emp_label(a["employee_id"]))
            v["date"].set(a["date"])
            v["days"].set(calc.fmt_num(a["days"]))
            v["note"].set(a["note"] or "")

        self.crud(v, tree, "absences", refresh,
                  add=lambda: self.db.add_absence(*values()),
                  update=lambda row_id: self.db.update_absence(row_id, *values()),
                  load=load, export_name=self.t("tab_abs"), after_add=("days", "note"))
        refresh()
        self.show_hook(refresh)

    # ---------- Achats employés ----------
    def build_emp_purchases(self, body):
        v = self.form(body, [
            ("emp", "employee", "emp"),
            ("date", "date", 12),
            ("amount", "amount_da", 12),
            ("desc", "item_advance", 30),
        ])
        tree = self.make_tree(body, [
            ("date", self.t("date"), 120), ("name", self.t("employee"), 220),
            ("amount", self.t("amount"), 150, "e"), ("desc", self.t("description"), 320),
        ])

        def refresh():
            fill_tree(tree, [(p["id"], (p["date"], p["name"], p["amount"], p["description"]))
                             for p in self.db.employee_purchases()], money(2))

        def values():
            return (self.require_emp(v["emp"]), parse_date(v["date"].get()).isoformat(),
                    parse_positive(v["amount"].get()), v["desc"].get().strip())

        def load(p):
            v["emp"].set(self.emp_label(p["employee_id"]))
            v["date"].set(p["date"])
            v["amount"].set(calc.fmt_num(p["amount"]))
            v["desc"].set(p["description"] or "")

        self.crud(v, tree, "employee_purchases", refresh,
                  add=lambda: self.db.add_employee_purchase(*values()),
                  update=lambda row_id: self.db.update_employee_purchase(row_id, *values()),
                  load=load, export_name=self.t("tab_emp_purch"), after_add=("amount", "desc"))
        refresh()
        self.show_hook(refresh)

    # ---------- Primes & heures sup ----------
    def build_bonuses(self, body):
        v = self.form(body, [
            ("emp", "employee", "emp"),
            ("date", "date", 12),
            ("kind", "type", (self.t("bonus"), self.t("overtime"))),
            ("value", "amount_or_hours", 10),
            ("note", "note", 10),
        ])
        tree = self.make_tree(body, [
            ("date", self.t("date"), 110), ("name", self.t("employee"), 200),
            ("kind", self.t("type"), 120), ("hours", self.t("hours"), 80),
            ("amount", self.t("amount"), 140, "e"), ("note", self.t("note"), 250),
        ])

        def refresh():
            fill_tree(tree, [(b["id"], (b["date"], b["name"], self.t(b["kind"]),
                                        calc.fmt_num(b["hours"]) if b["kind"] == "overtime" else "",
                                        b["amount"], b["note"])) for b in self.db.bonuses()], money(4))

        def values(row_id=None):
            emp_id = self.require_emp(v["emp"])
            day = parse_date(v["date"].get())
            value = parse_positive(v["value"].get())
            note = v["note"].get().strip()
            if v["kind"].get() != self.t("overtime"):
                return emp_id, day.isoformat(), "bonus", value, 0, note
            start, end = calc.week_period(day)
            week_hours = self.db.overtime_hours(emp_id, start.isoformat(), end.isoformat(), row_id) + value
            if week_hours > calc.MAX_OVERTIME_PER_WEEK and not messagebox.askyesno(
                    self.t("warning"), self.t("overtime_cap").format(calc.fmt_num(week_hours))):
                raise Cancelled()
            emp = self.db.employee(emp_id)
            return (emp_id, day.isoformat(), "overtime", calc.overtime_amount(emp["pay_type"], emp["base_amount"], value),
                    value, note)

        def load(b):
            v["emp"].set(self.emp_label(b["employee_id"]))
            v["date"].set(b["date"])
            v["kind"].set(self.t(b["kind"]))
            v["value"].set(calc.fmt_num(b["hours"] if b["kind"] == "overtime" else b["amount"]))
            v["note"].set(b["note"] or "")

        self.crud(v, tree, "bonuses", refresh,
                  add=lambda: self.db.add_bonus(*values()),
                  update=lambda row_id: self.db.update_bonus(row_id, *values(row_id)), load=load,
                  export_name=self.t("tab_bonus"), after_add=("value", "note"))
        refresh()
        self.show_hook(refresh)

    # ---------- Calcul ----------
    def build_calc(self, body):
        v = self.form(body, [
            ("emp", "employee", "emp_all"),
            ("period", "period", (self.t("month"), self.t("week"))),
            ("date", "date_in_period", 12),
        ])
        period_lbl = ttk.Label(body.head, text="", style="Period.TLabel")
        period_lbl.pack(anchor="w", pady=(6, 0))
        tree = self.make_tree(body, [
            ("name", self.t("employee"), 150), ("gross", self.t("gross"), 115, "e"),
            ("bonus", self.t("bonuses"), 105, "e"), ("abs", self.t("abs_days"), 85),
            ("absded", self.t("abs_ded"), 125, "e"), ("achats", self.t("purchases"), 115, "e"),
            ("net", self.t("net_pay"), 165, "e"), ("status", self.t("status"), 90),
        ])
        total_lbl = ttk.Label(body, text="", style="Total.TLabel")
        total_lbl.pack(anchor="e", pady=(8, 0))
        results = {}

        def period():
            d = parse_date(v["date"].get())
            return calc.month_period(d) if v["period"].get() == self.t("month") else calc.week_period(d)

        def net_fmt(n):
            return calc.fmt_da(n) + (f" ({self.t('debt')})" if n < 0 else "")

        def compute():
            start, end = period()
            s, e = start.isoformat(), end.isoformat()
            results.clear()
            rows, total = [], 0
            for emp, slip in self.compute_slips(start, end, self.emp_id(v["emp"])):
                results[emp["id"]] = (s, e, slip, emp)
                total += slip["net"]
                status = self.t("paid") if self.db.paid_ids(emp["id"], s, e) else self.t("not_paid")
                rows.append((emp["id"], (emp["name"], slip["gross"], slip["bonuses"], slip["absence_days"],
                                         slip["absence_deduction"], slip["purchases_deduction"], slip["net"],
                                         status)))
            fmt = money(1, 2, 4, 5)
            fmt[3], fmt[6] = calc.fmt_num, net_fmt
            fill_tree(tree, rows, fmt, neg_col=6)
            period_lbl.config(text=self.t("from_to").format(s, e))
            total_lbl.config(text=f"{self.t('total_net')}: {calc.fmt_da(total)}")

        def selected_ids():
            """Employés sélectionnés (ou tous), après un nouveau calcul avec les données à jour."""
            chosen = [int(i) for i in tree.selection()]
            compute()
            ids = [i for i in chosen if i in results] or list(results)
            if not ids:
                raise ValueError("calc_first")
            if chosen:
                tree.selection_set([str(i) for i in ids if tree.exists(str(i))])
            return ids

        def save():
            ids = selected_ids()
            already = sum(1 for i in ids if self.db.paid_ids(i, results[i][0], results[i][1]))
            question = (self.t("already_paid").format(already) if already
                        else self.t("confirm_payments").format(len(ids)))
            if not messagebox.askyesno(self.t("payment"), question):
                return
            today = date.today().isoformat()
            for emp_id in ids:
                s, e, slip, _ = results[emp_id]
                self.db.save_payment(emp_id, s, e, slip, today)
            compute()
            messagebox.showinfo("OK", self.t("payment_saved").format(len(ids)))

        def payslips():
            ids = selected_ids()
            company = self.company()
            sections = []
            for emp_id in ids:
                s, e, slip, emp = results[emp_id]
                sections.append(payslip_section(self.t, emp["name"], self.pay_label(emp["pay_type"]), s, e, slip,
                                                company))
            s = results[ids[0]][0]
            name = (f"{self.t('payslip')}_{results[ids[0]][3]['name']}" if len(ids) == 1
                    else self.t("payslips"))
            folder = Path(tempfile.gettempdir()) / "fiches_de_paie"
            folder.mkdir(exist_ok=True)
            path = folder / f"{safe_filename(name)}_{s}.html"
            path.write_text(payslips_document(self.t, sections, f"{self.t('payslips')} {s}"), encoding="utf-8")
            webbrowser.open(path.as_uri())

        self.button(v["_box"], "calc", self.safe(compute))
        self.button(v["_box"], "save_payment", self.safe(save))
        self.button(v["_box"], "payslip", self.safe(payslips))
        self.export_button(v["_box"], tree, self.t("tab_calc"))
        body.compute = compute
        self.show_hook(lambda: results and compute())

    # ---------- Historique ----------
    def build_history(self, body):
        v = self.form(body, [
            ("emp", "employee", "emp_all"),
            ("month", "month_filter", 12),
        ])
        tree = self.make_tree(body, [
            ("period", self.t("period"), 190), ("name", self.t("employee"), 150),
            ("gross", self.t("gross"), 115, "e"), ("bonus", self.t("bonuses"), 105, "e"),
            ("absded", self.t("abs_short"), 105, "e"), ("achats", self.t("purchases"), 105, "e"),
            ("net", self.t("net"), 120, "e"), ("paid", self.t("paid_on"), 100),
        ])
        total_lbl = ttk.Label(body, text="", style="Total.TLabel")
        total_lbl.pack(anchor="e", pady=(8, 0))

        def refresh():
            pays = self.db.payments(self.emp_id(v["emp"]), parse_month(v["month"].get()))
            fill_tree(tree, [(p["id"], (f"{p['period_start']} → {p['period_end']}", p["name"], p["gross"],
                                        p["bonuses"], p["absence_deduction"], p["purchases_deduction"],
                                        p["net"], p["paid_on"])) for p in pays],
                      money(2, 3, 4, 5, 6), neg_col=6)
            total_lbl.config(text=f"{self.t('total_paid')}: {calc.fmt_da(sum(p['net'] for p in pays))}")

        self.button(v["_box"], "show", self.safe(refresh))
        self.button(v["_box"], "delete", self.safe(lambda: self.delete_selected(tree, "payments", refresh)))
        self.export_button(v["_box"], tree, self.t("tab_hist"))
        refresh()
        self.show_hook(refresh)

    # ---------- Achats entreprise ----------
    def build_business(self, body):
        v = self.form(body, [
            ("date", "date", 12),
            ("amount", "amount_da", 12),
            ("desc", "description", 30),
            ("supplier", "supplier", 20),
        ])
        tree = self.make_tree(body, [
            ("date", self.t("date"), 120), ("amount", self.t("amount"), 150, "e"),
            ("desc", self.t("description"), 320), ("supplier", self.t("supplier"), 200),
        ])
        month_var = tk.StringVar(value=date.today().strftime("%Y-%m"))
        ttk.Label(tree.head, text=self.t("month_filter"), style="Card.TLabel").pack(side="left", padx=(24, 6))
        month_entry = ttk.Entry(tree.head, textvariable=month_var, width=10)
        month_entry.pack(side="left")
        ttk.Button(tree.head, text=theme.button_text("show", self.t("show")),
                   command=self.safe(lambda: refresh())).pack(side="left", padx=6)
        month_entry.bind("<Return>", lambda e: self.safe(refresh)())
        total_lbl = ttk.Label(body, text="", style="Total.TLabel")
        total_lbl.pack(anchor="e", pady=(8, 0))

        def refresh():
            rows = self.db.business_purchases(parse_month(month_var.get()))
            fill_tree(tree, [(p["id"], (p["date"], p["amount"], p["description"], p["supplier"]))
                             for p in rows], money(1))
            total_lbl.config(text=f"{self.t('total_purchases')}: {calc.fmt_da(sum(p['amount'] for p in rows))}")

        def values():
            return (parse_date(v["date"].get()).isoformat(), parse_positive(v["amount"].get()),
                    v["desc"].get().strip(), v["supplier"].get().strip())

        def load(p):
            v["date"].set(p["date"])
            v["amount"].set(calc.fmt_num(p["amount"]))
            v["desc"].set(p["description"] or "")
            v["supplier"].set(p["supplier"] or "")

        self.crud(v, tree, "business_purchases", refresh,
                  add=lambda: self.db.add_business_purchase(*values()),
                  update=lambda row_id: self.db.update_business_purchase(row_id, *values()),
                  load=load, export_name=self.t("tab_business"), after_add=("amount", "desc"))
        refresh()
        self.show_hook(refresh)


def selftest(out_path):
    """Vérification rapide que le programme s'ouvre et calcule juste (sert à tester Salaires.exe).
    Écrit le résultat dans out_path; retourne 0 si tout va bien."""
    lines, problems = [], []
    messagebox.showerror = lambda title, msg, **k: problems.append(msg)
    messagebox.showinfo = lambda title, msg, **k: lines.append(f"info: {msg}")
    messagebox.askyesno = lambda title, msg, **k: True
    folder = tempfile.mkdtemp(prefix="salaires_selftest_")
    try:
        db = DB(os.path.join(folder, DB_NAME))
        emp = db.add_employee("Test", "monthly", 30000)
        db.add_absence(emp, "2026-09-10", 1)
        db.add_bonus(emp, "2026-09-12", "overtime", calc.overtime_amount("monthly", 30000, 2), hours=2)
        app = App(db)
        for i in range(len(app.PAGES)):
            app.show_page(i)
            app.update()
        app.switch_lang()
        app.update()
        net = app.compute_slips(date(2026, 9, 1), date(2026, 9, 30))[0][1]["net"]
        lines.append(f"net Sep 2026: {net}")
        if net != 29519.23:
            problems.append(f"wrong net {net} (expected 29519.23)")
        write_xlsx(os.path.join(folder, "check.xlsx"), ["a", "b"], [["x", 1.5]])
        slip = app.compute_slips(date(2026, 9, 1), date(2026, 9, 30))[0][1]
        html = payslips_document(app.t, [payslip_section(app.t, "Test", "x", "a", "b", slip)], "t")
        if "29 519,23 DA" not in html:
            problems.append("payslip amount missing")
        lines.append(f"icon loaded: {bool(getattr(app, '_icon', None))}")
        app.destroy()
        lines.append(f"python {sys.version.split()[0]}, tk {tk.TkVersion}, frozen={getattr(sys, 'frozen', False)}")
        lines.append(f"data file location: {default_db_path()}")
    except Exception:
        problems.append(traceback.format_exc())
    lines.append("SELFTEST " + ("OK" if not problems else "FAILED"))
    lines += [f"problem: {p}" for p in problems]
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    return 1 if problems else 0


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if sys.platform == "win32":
        try:  # texte net sur les écrans haute résolution
            import ctypes
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except (AttributeError, OSError):
            pass
    if argv[:1] == ["--selftest"]:
        sys.exit(selftest(os.path.abspath(argv[1] if len(argv) > 1 else "selftest.txt")))
    try:
        app = App(DB())
    except Exception as err:  # lancé sans console (Lancer.bat): montrer l'erreur au lieu de rien
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("Salaires", f"{type(err).__name__}: {err}")
        raise
    app.report_callback_exception = lambda exc, val, tb: messagebox.showerror(
        "Salaires", f"{exc.__name__}: {val}")
    app.mainloop()


if __name__ == "__main__":
    main()
