"""Petit calendrier pour choisir une date (bibliothèque standard uniquement)."""
import calendar
import tkinter as tk
from datetime import date

from . import theme

MONTHS = {
    "en": ["January", "February", "March", "April", "May", "June", "July", "August", "September",
           "October", "November", "December"],
    "fr": ["Janvier", "Février", "Mars", "Avril", "Mai", "Juin", "Juillet", "Août", "Septembre",
           "Octobre", "Novembre", "Décembre"],
}
MONTHS_SHORT = {
    "en": ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
    "fr": ["Janv.", "Févr.", "Mars", "Avr.", "Mai", "Juin", "Juil.", "Août", "Sept.", "Oct.", "Nov.", "Déc."],
}
DAYS = {  # 0 = lundi
    "en": ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"],
    "fr": ["Lu", "Ma", "Me", "Je", "Ve", "Sa", "Di"],
}


def month_grid(year, month, week_start):
    """Semaines du mois: liste de 7 jours (0 = case vide), commençant au jour week_start."""
    return calendar.Calendar(firstweekday=week_start).monthdayscalendar(year, month)


class DatePicker(tk.Toplevel):
    """Fenêtre calendrier sous le widget `anchor`; écrit la date choisie (AAAA-MM-JJ) dans `var`."""

    def __init__(self, anchor, var, lang="en", week_start=calendar.SATURDAY):
        super().__init__(anchor)
        self.var, self.lang, self.week_start = var, lang, week_start
        try:
            self.selected = date.fromisoformat(var.get().strip())
        except ValueError:
            self.selected = date.today()
        self.year, self.month = self.selected.year, self.selected.month
        self.overrideredirect(True)
        self.configure(background=theme.PRIMARY, padx=1, pady=1)
        self.body = tk.Frame(self, background=theme.WHITE, padx=6, pady=6)
        self.body.pack()
        self.geometry(f"+{anchor.winfo_rootx()}+{anchor.winfo_rooty() + anchor.winfo_height()}")
        self.bind("<Escape>", lambda e: self.destroy())
        self.bind("<Button-1>", self._click_outside)
        self.draw()
        self.update_idletasks()
        try:  # les clics hors du calendrier lui sont envoyés -> fermeture
            self.grab_set()
            self.focus_force()
        except tk.TclError:
            pass

    def _click_outside(self, event):
        x, y = self.winfo_rootx(), self.winfo_rooty()
        if not (x <= event.x_root < x + self.winfo_width() and y <= event.y_root < y + self.winfo_height()):
            self.destroy()

    def move(self, step):
        m = self.month - 1 + step
        self.year, self.month = self.year + m // 12, m % 12 + 1
        self.draw()

    def pick(self, day):
        self.var.set(date(self.year, self.month, day).isoformat())
        self.destroy()

    def draw(self):
        for w in self.body.winfo_children():
            w.destroy()
        nav = dict(background=theme.WHITE, foreground=theme.PRIMARY, relief="flat", bd=0, cursor="hand2",
                   activebackground=theme.ROW_ALT, font=("TkDefaultFont", 12, "bold"))
        tk.Button(self.body, text="‹", command=lambda: self.move(-1), **nav).grid(row=0, column=0)
        tk.Label(self.body, text=f"{MONTHS[self.lang][self.month - 1]} {self.year}", background=theme.WHITE,
                 foreground=theme.PRIMARY, font=("TkDefaultFont", 10, "bold")).grid(row=0, column=1, columnspan=5)
        tk.Button(self.body, text="›", command=lambda: self.move(1), **nav).grid(row=0, column=6)
        for i in range(7):
            tk.Label(self.body, text=DAYS[self.lang][(self.week_start + i) % 7], width=3,
                     background=theme.WHITE, foreground=theme.MUTED).grid(row=1, column=i)
        today = date.today()
        for r, week in enumerate(month_grid(self.year, self.month, self.week_start), start=2):
            for c, day in enumerate(week):
                if not day:
                    continue
                d = date(self.year, self.month, day)
                bg, fg = theme.WHITE, theme.TEXT
                if d == self.selected:
                    bg, fg = theme.ACCENT, theme.WHITE
                elif d == today:
                    bg = theme.SELECT
                tk.Button(self.body, text=str(day), width=3, relief="flat", bd=0, highlightthickness=0, cursor="hand2",
                          background=bg, foreground=fg, activebackground=theme.SELECT,
                          command=lambda dd=day: self.pick(dd)).grid(row=r, column=c, padx=1, pady=1)
        tk.Button(self.body, text=today.isoformat(), relief="flat", bd=0, cursor="hand2",
                  background=theme.WHITE, foreground=theme.ACCENT, activebackground=theme.ROW_ALT,
                  command=lambda: (self.var.set(today.isoformat()), self.destroy())
                  ).grid(row=9, column=0, columnspan=7, pady=(4, 0))
