"""Apparence de l'application (thème ttk, couleurs, polices)."""
import sys
import tkinter.font as tkfont
from tkinter import ttk

PRIMARY = "#1F4E79"     # bleu foncé (titres, en-têtes de tableau)
SIDEBAR = "#14324F"     # menu latéral
SIDEBAR_HOVER = "#1E4468"
SIDEBAR_TEXT = "#C9D6E4"
ACCENT = "#2E75B6"      # boutons principaux, élément actif
ACCENT_DARK = "#245E93"
BG = "#F3F5F8"          # fond de page
CARD = "#FFFFFF"        # cartes
BORDER = "#DCE2EA"
ROW_ALT = "#F3F7FC"     # lignes alternées
SELECT = "#CFE2F6"      # ligne sélectionnée
TEXT = "#1F2937"
MUTED = "#667085"
DANGER = "#B42318"
WHITE = "#FFFFFF"
GRID = "#E7EBF0"        # grille du graphique

# Couleurs des séries du graphique (validées: daltonisme + contraste sur fond blanc)
SERIES = ("#2a78d6", "#eb6834")

# Icônes (caractères Unicode simples, pas d'images)
ICONS = {
    "add": "＋", "edit": "✎", "delete": "✕", "export": "⬇", "calc": "▶",
    "save_payment": "✔", "payslip": "▤", "show": "⟳", "backup": "⬆", "restore": "⟲",
    "settings": "⚙", "save": "✔", "switch": "⇄",
    "tab_dash": "◫", "tab_emp": "☺", "tab_abs": "✗", "tab_emp_purch": "▣", "tab_bonus": "★",
    "tab_calc": "∑", "tab_hist": "☰", "tab_business": "▤",
}
ACCENT_KEYS = {"add", "calc", "save_payment", "save"}
DANGER_KEYS = {"delete"}

FONT = ("TkDefaultFont", 10)
SCALE = 1.0  # agrandissement de l'écran (Windows 125 %, 150 %...), calculé dans apply()


def px(n):
    """Taille en pixels adaptée à l'agrandissement de l'écran."""
    return int(round(n * SCALE))


def apply(root):
    """Applique le thème à la fenêtre principale."""
    global FONT, SCALE
    SCALE = max(1.0, root.winfo_fpixels("1i") / 96.0)
    base = tkfont.nametofont("TkDefaultFont")
    if sys.platform == "win32":
        family, size = "Segoe UI", 10
    elif sys.platform == "darwin":
        family, size = base.actual("family"), 13
    else:
        family, size = base.actual("family"), 10
    FONT = (family, size)
    for name in ("TkDefaultFont", "TkTextFont", "TkMenuFont", "TkHeadingFont"):
        tkfont.nametofont(name).configure(family=family, size=size)
    root.configure(background=BG)
    root.option_add("*TCombobox*Listbox.font", (family, size))

    s = ttk.Style(root)
    s.theme_use("clam")
    s.configure(".", background=BG, foreground=TEXT, font=(family, size))
    s.configure("TFrame", background=BG)
    s.configure("TLabel", background=BG, foreground=TEXT)
    s.configure("Muted.TLabel", foreground=MUTED)
    s.configure("PageTitle.TLabel", foreground=TEXT, font=(family, size + 8, "bold"))
    s.configure("Period.TLabel", foreground=PRIMARY, font=(family, size + 1, "bold"))
    s.configure("Total.TLabel", foreground=PRIMARY, font=(family, size + 3, "bold"))
    s.configure("TCheckbutton", background=BG)

    # Cartes blanches avec bordure fine
    s.configure("Card.TFrame", background=CARD, borderwidth=1, relief="solid",
                bordercolor=BORDER, lightcolor=BORDER, darkcolor=BORDER)
    s.configure("CardInner.TFrame", background=CARD)
    s.configure("Card.TLabel", background=CARD, foreground=MUTED)
    s.configure("CardTitle.TLabel", background=CARD, foreground=TEXT, font=(family, size + 1, "bold"))
    s.configure("Card.TCheckbutton", background=CARD)
    s.map("Card.TCheckbutton", background=[("active", CARD)])
    s.configure("KpiValue.TLabel", background=CARD, foreground=TEXT, font=(family, size + 7, "bold"))
    s.configure("KpiNeg.TLabel", background=CARD, foreground=DANGER, font=(family, size + 7, "bold"))

    s.configure("TButton", padding=(10, 4), background=WHITE, bordercolor="#C5CEDA")
    s.map("TButton", background=[("active", "#E6EEF8")])
    s.configure("Accent.TButton", background=ACCENT, foreground=WHITE, bordercolor=ACCENT)
    s.map("Accent.TButton", background=[("active", ACCENT_DARK)])
    s.configure("Danger.TButton", foreground=DANGER)
    s.configure("Icon.TButton", padding=(4, 2))

    s.configure("TEntry", padding=4, fieldbackground=WHITE, bordercolor="#C5CEDA")
    s.configure("TCombobox", padding=3, fieldbackground=WHITE, bordercolor="#C5CEDA")
    s.map("TCombobox", fieldbackground=[("readonly", WHITE)])

    # Pages sans onglets visibles (navigation par le menu latéral)
    s.layout("Pages.TNotebook.Tab", [])
    s.configure("Pages.TNotebook", background=BG, borderwidth=0, tabmargins=0)

    line = tkfont.nametofont("TkDefaultFont").metrics("linespace")  # hauteur réelle du texte
    s.configure("Treeview", rowheight=int(line * 1.75), background=WHITE, fieldbackground=WHITE,
                bordercolor=BORDER, lightcolor=BORDER, darkcolor=BORDER)
    s.map("Treeview", background=[("selected", SELECT)], foreground=[("selected", TEXT)])
    s.configure("Treeview.Heading", background=PRIMARY, foreground=WHITE, font=(family, size, "bold"),
                relief="flat", padding=(4, 7))
    s.map("Treeview.Heading", background=[("active", ACCENT)])


def style_tree(tree):
    """Couleurs des lignes: alternées et montants négatifs."""
    tree.tag_configure("odd", background=ROW_ALT)
    tree.tag_configure("neg", foreground=DANGER)


def button_style(key):
    if key in ACCENT_KEYS:
        return "Accent.TButton"
    if key in DANGER_KEYS:
        return "Danger.TButton"
    return "TButton"


def button_text(key, text):
    icon = ICONS.get(key)
    return f"{icon}  {text}" if icon else text
