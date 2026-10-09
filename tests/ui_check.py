"""Vérification complète de l'interface: clique sur chaque page comme un utilisateur (58 contrôles).

    python tests/ui_check.py [dossier_de_sortie]

Ouvre la fenêtre quelques secondes (il faut un écran). Code de sortie 0 = tout est bon.
"""
import os, re, sys, tempfile, webbrowser, zipfile
from datetime import date
from tkinter import ttk, messagebox, filedialog
from urllib.parse import urlparse
from urllib.request import url2pathname
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from salary_app.app import App, TEXT
from salary_app.db import DB
try:
    from PIL import ImageGrab  # facultatif: captures d'écran
except ImportError:
    ImageGrab = None


def xlsx_rows(path):
    """Lit la feuille d'un .xlsx simple: nombres -> float, textes -> str."""
    with zipfile.ZipFile(path) as z:
        sheet = z.read("xl/worksheets/sheet1.xml").decode()
    rows = []
    for row in re.findall(r"<row[^>]*>(.*?)</row>", sheet):
        cells = []
        for attrs, body in re.findall(r"<c ([^>]*)>(.*?)</c>", row):
            if 't="inlineStr"' in attrs:
                cells.append(re.search(r"<t[^>]*>(.*?)</t>", body).group(1))
            else:
                cells.append(float(re.search(r"<v>(.*?)</v>", body).group(1)))
        rows.append(cells)
    return rows


OUT = sys.argv[1] if len(sys.argv) > 1 else tempfile.mkdtemp(prefix="salaires_ui_")
os.makedirs(OUT, exist_ok=True)
log, answers, opened = [], [], []
messagebox.showinfo = lambda title, msg, **k: log.append(("info", msg))
messagebox.showerror = lambda title, msg, **k: log.append(("error", msg))
messagebox.askyesno = lambda title, msg, **k: (log.append(("ask", msg)), answers.pop(0) if answers else True)[1]
webbrowser.open = lambda url: opened.append(url)
fails = []
def check(cond, what):
    print(("PASS " if cond else "FAIL ") + what)
    if not cond: fails.append(what)
def last(kind):
    return next((m for k, m in reversed(log) if k == kind), None)

dbfile = os.path.join(OUT, "e2e.db")
if os.path.exists(dbfile): os.remove(dbfile)
db = DB(dbfile)
app = App(db); app.geometry("1280x780+0+0"); app.update()

def deep(w, cls):
    out = []
    for c in w.winfo_children():
        if isinstance(c, cls): out.append(c)
        out += deep(c, cls)
    return out
def page(i):
    app.show_page(i); app.update()
    tab = app.nb.nametowidget(app.nb.tabs()[i])
    return tab.winfo_children()[1]          # body
def card(body): return body.winfo_children()[0]
def field(body, col):
    w = card(body).grid_slaves(row=1, column=col)[0]
    return w if not isinstance(w, ttk.Frame) else deep(w, ttk.Entry)[0]
def setf(body, col, value):
    w = field(body, col)
    if isinstance(w, ttk.Combobox): w.set(value)
    else: w.delete(0, "end"); w.insert(0, value)
def click(body, text):
    btns = [b for b in deep(card(body), ttk.Button) if text in b.cget("text")]
    assert btns, f"button {text}"
    btns[0].invoke(); app.update()
def tree(body): return deep(body, ttk.Treeview)[0]
def rows(body): return [tree(body).item(i)["values"] for i in tree(body).get_children()]
def select(body, row_index):
    t = tree(body); iid = t.get_children()[row_index]; t.selection_set(iid); app.update(); return iid
def shot(name):
    if ImageGrab is None:
        return
    app.update(); app.after(250); app.update()
    x, y = app.winfo_rootx(), app.winfo_rooty()
    ImageGrab.grab(bbox=(x, y, x + app.winfo_width(), y + app.winfo_height())).save(f"{OUT}/{name}.png")
def nerr(): return sum(1 for k, _ in log if k == "error")
T = lambda k: TEXT[k][0]

# ---- Employés
b = page(1)
setf(b, 1, "Monthly"); setf(b, 2, "30000"); click(b, "Add")
check(last("error") == T("name_required"), "employee: empty name rejected")
setf(b, 0, "Ali"); setf(b, 2, "0"); click(b, "Add")
check(last("error") == T("err_positive"), "employee: salary 0 rejected")
setf(b, 2, "abc"); click(b, "Add")
check(last("error") == T("err_amount"), "employee: text salary rejected")
for name, typ, sal in (("Ali", "Monthly", "30000"), ("Karim", "Weekly", "6000"), ("Sofiane", "Daily", "1500"),
                       ("Nadia", "Monthly", "38 000")):
    setf(b, 0, name); setf(b, 1, typ); setf(b, 2, sal); click(b, "Add")
check(len(db.employees()) == 4, "employee: 4 added")
check(field(b, 0).get() == "", "employee: form cleared after add")
iid = next(i for i in tree(b).get_children() if tree(b).item(i)["values"][0] == "Nadia")
tree(b).selection_set(iid); app.update()
check(field(b, 0).get() == "Nadia" and field(b, 2).get() == "38000", "employee: select loads form")
setf(b, 2, "40000"); click(b, "Save changes")
check(db.employee(int(iid))["base_amount"] == 40000, "employee: edit saved")
tree(b).selection_set(iid); app.update()
[c for c in deep(card(b), ttk.Checkbutton)][0].invoke(); click(b, "Save changes")
check(db.employee(int(iid))["active"] == 0, "employee: deactivated")
tree(b).selection_remove(tree(b).selection()); click(b, "Save changes")
check(last("error") == T("select_one"), "employee: edit without selection rejected")

# ---- Absences
b = page(2)
check(set(field(b, 0)["values"]) == {"1 - Ali", "2 - Karim", "3 - Sofiane"}, "absences: inactive Nadia hidden from list")
setf(b, 0, "1 - Ali"); setf(b, 1, "2026-09-10"); setf(b, 2, "0"); click(b, "Add")
check(last("error") == T("err_days"), "absences: 0 days rejected")
setf(b, 1, "2026-02-30"); setf(b, 2, "2"); click(b, "Add")
check(last("error") == T("err_date"), "absences: invalid date rejected")
setf(b, 1, "2026-09-10"); click(b, "Add")
setf(b, 0, "3 - Sofiane"); setf(b, 1, "2026-09-20"); setf(b, 2, "1"); click(b, "Add")
setf(b, 0, "2 - Karim"); setf(b, 1, "2026-09-21"); setf(b, 2, "1"); click(b, "Add")
check(len(db.absences()) == 3, "absences: 3 added")
iid = select(b, 0)  # Karim (date la plus récente)
check(field(b, 0).get() == "2 - Karim", "absences: select loads employee")
setf(b, 2, "0,5"); click(b, "Save changes")
check(db.get("absences", int(iid))["days"] == 0.5, "absences: edit to 0.5 day")
check(rows(b)[0][2] in ("0,5", 0.5), f"absences: shows 0,5 (got {rows(b)[0][2]!r})")
select(b, 0); answers.append(False); click(b, "Delete")
check(len(db.absences()) == 3, "absences: delete cancelled keeps row")
select(b, 0); click(b, "Delete")
check(len(db.absences()) == 2, "absences: delete removes row")

# ---- Achats employés
b = page(3)
setf(b, 0, "1 - Ali"); setf(b, 1, "2026-09-12"); setf(b, 2, "-5"); click(b, "Add")
check(last("error") == T("err_positive"), "purchases: negative rejected")
setf(b, 2, "1500"); setf(b, 3, "advance"); click(b, "Add")
setf(b, 0, "2 - Karim"); setf(b, 1, "2026-09-14"); setf(b, 2, "800"); setf(b, 3, "sugar"); click(b, "Add")
iid = select(b, 0); setf(b, 2, "900"); click(b, "Save changes")
check(db.purchases_total(2, "2026-09-01", "2026-09-30") == 900, "purchases: edit saved")

# ---- Primes & heures sup
b = page(4)
setf(b, 0, "2 - Karim"); setf(b, 1, "2026-09-20"); setf(b, 2, "Bonus"); setf(b, 3, "3000"); click(b, "Add")
setf(b, 0, "1 - Ali"); setf(b, 1, "2026-09-19"); setf(b, 2, "Overtime"); setf(b, 3, "6"); click(b, "Add")
check(round(db.bonuses_total(1, "2026-09-01", "2026-09-30"), 2) == 1557.69, "overtime: 6 h = 1557.69 DA")
n_before = len(db.bonuses()); answers.append(False)
setf(b, 3, "4"); setf(b, 1, "2026-09-22"); click(b, "Add")
check("10" in (last("ask") or "") and len(db.bonuses()) == n_before, "overtime: >8 h/week warns, No cancels")
check(field(b, 3).get() == "4", "overtime: cancelled entry keeps form values")
setf(b, 1, "2026-09-26"); click(b, "Add")  # semaine suivante (commence samedi 26): pas d'alerte
check(len(db.bonuses()) == n_before + 1 and "10" in (last("ask") or ""), "overtime: next week no new warning")
iid = next(i for i in tree(b).get_children() if tree(b).item(i)["values"][2] == "Overtime" and "26" in tree(b).item(i)["values"][0])
tree(b).selection_set(iid); app.update(); setf(b, 3, "2"); click(b, "Save changes")
check(db.get("bonuses", int(iid))["amount"] == 519.23, "overtime: edit recomputes amount")

# ---- Calcul
b = page(5)
setf(b, 2, "2026-09-15"); click(b, "Calculate")
r = {row[0]: row for row in rows(b)}
check(set(r) == {"Ali", "Karim", "Sofiane"}, "calc: active employees only")
check(r["Ali"][1] == "30 000,00 DA" and r["Ali"][2] == "2 076,92 DA" and r["Ali"][6] == "28 576,92 DA",
      f"calc: Ali 30000+(1557.69+519.23)-2000-1500 = 28576.92 ({r['Ali'][6]})")
check(r["Karim"][6] == "27 814,29 DA", f"calc: Karim 25714.29+3000-0-900 = 27814.29 ({r['Karim'][6]})")
check(r["Sofiane"][1] == "39 000,00 DA" and r["Sofiane"][6] == "37 500,00 DA", "calc: Sofiane 26 days - 1")
check(all(row[7] == T("not_paid") for row in rows(b)), "calc: status not paid")
shot("e2e_calc_before")
click(b, "Save payment")
check(len(db.payments()) == 3 and all(row[7] == T("paid") for row in rows(b)), "calc: 3 payments saved, status paid")
# modification après paiement puis nouvel enregistrement
db.add_employee_purchase(1, "2026-09-25", 500, "late")
iid = next(i for i in tree(b).get_children() if tree(b).item(i)["values"][0] == "Ali")
tree(b).selection_set(iid); app.update(); click(b, "Save payment")
check("already" in (last("ask") or ""), "calc: re-saving warns already paid")
pays = db.payments(emp_id=1)
check(len(pays) == 1 and pays[0]["net"] == 28076.92, f"calc: payment replaced with fresh data ({pays[0]['net']})")
check(len(db.payments()) == 3, "calc: only selected employee re-saved")
tree(b).selection_remove(tree(b).selection()); click(b, "Payslip")
html = open(url2pathname(urlparse(opened[-1]).path), encoding="utf-8").read()
check(html.count('<section class="slip">') == 3, "payslip: one document with 3 payslips")
filedialog.asksaveasfilename = lambda **k: f"{OUT}/calc.xlsx"
click(b, "Export Excel")
data = xlsx_rows(f"{OUT}/calc.xlsx")
check(data[0][0] == "Employee" and len(data) == 4 and isinstance(data[1][6], float), "export: xlsx with numbers")
tree(b).search_var.set("kar"); app.update()
check([row[0] for row in rows(b)] == ["Karim"], "search: filters rows")
click(b, "Export Excel")
check(len(xlsx_rows(f"{OUT}/calc.xlsx")) == 2, "export: exports filtered rows only")
tree(b).search_var.set("")

# ---- Historique
b = page(6)
setf(b, 1, "2026-13"); click(b, "Show")
check(last("error") == T("err_month"), "history: invalid month rejected")
setf(b, 1, "2026-09"); click(b, "Show")
check(len(rows(b)) == 3, "history: 3 payments for 2026-09")
setf(b, 1, ""); setf(b, 0, "1 - Ali"); click(b, "Show")
check(len(rows(b)) == 1, "history: filter by employee")

# ---- Achats entreprise
b = page(7)
for d, a, desc in (("2026-09-03", "45000", "Stock"), ("2026-08-10", "30000", "Rent"), ("2026-07-02", "12000", "Tools")):
    setf(b, 0, d); setf(b, 1, a); setf(b, 2, desc); click(b, "Add")
t7 = tree(b); mentry = [e for e in deep(t7.head, ttk.Entry) if e.winfo_width() and e is not deep(t7.head, ttk.Entry)[0]][0]
mentry.delete(0, "end"); mentry.insert(0, "2026-09"); [x for x in deep(t7.head, ttk.Button) if "Show" in x.cget("text")][0].invoke(); app.update()
check(len(rows(b)) == 1 and "45 000,00" in deep(b, ttk.Label)[-1].cget("text"), "business: month filter + total")
mentry.delete(0, "end"); [x for x in deep(t7.head, ttk.Button) if "Show" in x.cget("text")][0].invoke(); app.update()
check(len(rows(b)) == 3, "business: all months")

# ---- Tableau de bord
b = page(0)
app.update()
vals = {k: v[0].cget("text") for k, v in b.tiles.items()}
print("   dashboard (current month):", vals)
for _ in range(1):  # aller en septembre 2026
    pass
today = date.today()
steps = (today.year - 2026) * 12 + today.month - 9
nav_btns = [w for w in deep(b.head, ttk.Button)]
for _ in range(steps): nav_btns[0].invoke()
app.update()
vals = {k: v[0].cget("text") for k, v in b.tiles.items()}
print("   dashboard (Sep 2026):", vals)
check(vals["kpi_emp"] == "3", "dashboard: 3 active employees")
check(vals["kpi_paid"] == "93 391,21 DA", f"dashboard: salaries paid 28076.92+27814.29+37500 ({vals['kpi_paid']})")
check(vals["kpi_topay"] == "93 391,21 DA", "dashboard: to-pay estimate matches calc")
check(vals["kpi_bonus"] == "5 076,92 DA" and vals["kpi_purch"] == "2 900,00 DA", "dashboard: bonuses + purchases")
check(vals["kpi_business"] == "45 000,00 DA", "dashboard: business purchases")
check(b.chart.series[1][2][-3:] == [12000, 30000, 45000], "dashboard: chart last months business")
shot("e2e_dashboard")

# ---- Paramètres
win = app.open_settings(); app.update()
es = deep(win, ttk.Entry)
for e, val in zip(es, ["Boutique El Baraka", "12 rue Didouche Mourad, Alger", "0550 12 34 56", "000116001234567"]):
    e.delete(0, "end"); e.insert(0, val)
[x for x in deep(win, ttk.Button) if "Save" in x.cget("text")][0].invoke(); app.update()
check(db.get_setting("company_name") == "Boutique El Baraka" and app.current_page == 0, "settings: saved, page kept")

# ---- Sauvegarde / restauration
filedialog.asksaveasfilename = lambda **k: f"{OUT}/backup test.db"
app.backup()
db.add_employee("Temp", "daily", 1000)
bad = f"{OUT}/not_a_backup.db"; open(bad, "w").write("hello" * 300)
filedialog.askopenfilename = lambda **k: bad
app.safe(app.restore)(); app.update()
check(last("error") == T("invalid_backup") and len(db.employees()) == 5, "restore: invalid file rejected, data intact")
filedialog.askopenfilename = lambda **k: f"{OUT}/backup test.db"
app.restore(); app.update()
check([e["name"] for e in db.employees()] == ["Ali", "Karim", "Nadia", "Sofiane"], "restore: backup restored")

# ---- Langue + débordement
def clipped():
    out = []
    right = app.winfo_rootx() + app.winfo_width()
    for i in range(len(app.PAGES)):
        body = page(i)
        for w in deep(body, ttk.Widget):
            if w.winfo_ismapped() and w.winfo_rootx() + w.winfo_width() > right + 1:
                out.append((i, w.cget("text") if "text" in w.keys() else w.winfo_class()))
    return out
for size in ("1280x780", "1120x680"):
    for lang in ("en", "fr"):
        app.lang = lang; app.geometry(size + "+0+0"); app.build(); app.update()
        c = clipped()
        check(not c, f"layout {size} {lang}: nothing cut off {c[:3]}")
app.lang = "en"; app.geometry("1280x780+0+0"); app.build(); app.update()
app.show_page(5); app.switch_lang(); app.update()
check(app.current_page == 5 and app.lang == "fr", "language switch keeps current page")
b = page(5); setf(b, 2, "2026-09-15"); click(b, "Calculer"); shot("e2e_calc_fr")
b = page(2); select(b, 0); shot("e2e_absences_fr")
app.switch_lang(); b = page(0)
for _ in range(steps): [w for w in deep(b.head, ttk.Button)][0].invoke()
app.update()
# info-bulle du graphique
ch = b.chart
tag = "m5_1"; x0, y0, x1, y1 = ch.bbox(tag)
ch.event_generate("<Motion>", x=int((x0 + x1) / 2), y=int(y1 - 5)); app.update()
check(bool(ch.find_withtag("tip")), "chart: tooltip on hover")
shot("e2e_dashboard_hover")
app.destroy()
print(f"\n{len(fails)} failure(s)", fails)
sys.exit(1 if fails else 0)
