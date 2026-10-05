"""Apparence de l'application (thème ttk, couleurs, polices)."""
import sys
import tkinter.font as tkfont
from tkinter import ttk

PRIMARY = "#1F4E79"     # bleu foncé (bandeau, en-têtes)
ACCENT = "#2E75B6"      # boutons principaux
ACCENT_DARK = "#245E93"
BG = "#F4F6F9"          # fond
ROW_ALT = "#EEF3FA"     # lignes alternées
SELECT = "#CFE2F6"      # ligne sélectionnée
TEXT = "#1F2937"
MUTED = "#5B6575"
DANGER = "#B42318"
WHITE = "#FFFFFF"

# Icônes (caractères Unicode simples, pas d'images)
ICONS = {
    "add": "＋", "edit": "✎", "delete": "✕", "export": "⬇", "calc": "▶",
    "save_payment": "✔", "payslip": "▤", "show": "⟳", "backup": "⬆", "restore": "⟲",
    "settings": "⚙", "save": "✔",
}
ACCENT_KEYS = {"add", "calc", "save_payment", "save"}
DANGER_KEYS = {"delete"}


def apply(root):
    """Applique le thème à la fenêtre principale."""
    base = tkfont.nametofont("TkDefaultFont")
    if sys.platform == "win32":
        family, size = "Segoe UI", 10
    elif sys.platform == "darwin":
        family, size = base.actual("family"), 13
    else:
        family, size = base.actual("family"), 10
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
    s.configure("Period.TLabel", foreground=PRIMARY, font=(family, size + 1, "bold"))
    s.configure("Total.TLabel", foreground=PRIMARY, font=(family, size + 3, "bold"))
    s.configure("TCheckbutton", background=BG)

    s.configure("Header.TFrame", background=PRIMARY)
    s.configure("Header.TLabel", background=PRIMARY, foreground=WHITE, font=(family, size + 6, "bold"))
    s.configure("HeaderSub.TLabel", background=PRIMARY, foreground="#C9D9EC", font=(family, size))
    s.configure("Header.TButton", background=ACCENT, foreground=WHITE, borderwidth=0, padding=(10, 4))
    s.map("Header.TButton", background=[("active", ACCENT_DARK)])

    s.configure("TButton", padding=(10, 4), background=WHITE, bordercolor="#C5CEDA")
    s.map("TButton", background=[("active", "#E6EEF8")])
    s.configure("Accent.TButton", background=ACCENT, foreground=WHITE, bordercolor=ACCENT)
    s.map("Accent.TButton", background=[("active", ACCENT_DARK)])
    s.configure("Danger.TButton", foreground=DANGER)
    s.configure("Icon.TButton", padding=(4, 2))

    s.configure("TEntry", padding=4, fieldbackground=WHITE)
    s.configure("TCombobox", padding=3, fieldbackground=WHITE)
    s.map("TCombobox", fieldbackground=[("readonly", WHITE)])

    s.configure("TNotebook", background=BG, borderwidth=0, tabmargins=(8, 6, 8, 0))
    s.configure("TNotebook.Tab", padding=(14, 6), background="#DDE4ED", foreground=MUTED)
    s.map("TNotebook.Tab", background=[("selected", WHITE)], foreground=[("selected", PRIMARY)])

    s.configure("Treeview", rowheight=int(size * 2.6), background=WHITE, fieldbackground=WHITE,
                bordercolor="#D5DCE5")
    s.map("Treeview", background=[("selected", SELECT)], foreground=[("selected", TEXT)])
    s.configure("Treeview.Heading", background=PRIMARY, foreground=WHITE, font=(family, size, "bold"),
                relief="flat", padding=(4, 6))
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
