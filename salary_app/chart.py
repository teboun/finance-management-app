"""Graphique en barres groupées (tk.Canvas, sans dépendance)."""
import math
import tkinter as tk

from . import theme
from .calc import fmt_da


def nice_ceiling(value):
    """Arrondit vers le haut à 1, 2, 2,5 ou 5 × 10^n (graduations lisibles)."""
    if value <= 0:
        return 1
    exp = 10 ** math.floor(math.log10(value))
    for m in (1, 2, 2.5, 5, 10):
        if value <= m * exp + 1e-9:
            return m * exp
    return 10 * exp


def fmt_short(value):
    """120000 -> '120 k', 1500000 -> '1,5 M'."""
    for div, unit in ((1e6, "M"), (1e3, "k")):
        if abs(value) >= div:
            return f"{value / div:.1f}".rstrip("0").rstrip(".").replace(".", ",") + f" {unit}"
    return f"{value:g}"


class BarChart(tk.Canvas):
    """Barres groupées: une couleur par série, légende, grille discrète, info-bulle au survol."""

    LEFT, RIGHT, TOP, BOTTOM = 64, 16, 40, 30

    def __init__(self, parent, height=270):
        super().__init__(parent, height=height, background=theme.CARD, highlightthickness=0)
        self.labels, self.series = [], []
        self.bind("<Configure>", lambda e: self.draw())

    def set_data(self, labels, series):
        """labels = noms des groupes; series = [(nom, couleur, [valeurs])]."""
        self.labels, self.series = labels, series
        self.draw()

    def draw(self):
        self.delete("all")
        w, h = self.winfo_width(), self.winfo_height()
        if w < 50 or not self.labels:
            return
        font = theme.FONT
        small = (font[0], max(font[1] - 1, 8))
        left, right, top, bottom = self.LEFT, w - self.RIGHT, self.TOP, h - self.BOTTOM
        ymax = nice_ceiling(max([max(0, v) for _, _, vals in self.series for v in vals] or [0]))

        def y(v):
            return bottom - (max(0, v) / ymax) * (bottom - top)

        n, k = len(self.labels), len(self.series)
        gw = (right - left) / n
        bw = max(6, min(26, gw * 0.7 / k - 2))
        gap = 2

        # zones de survol (plus grandes que les barres), sous la grille
        hits = []
        for i in range(n):
            x0 = left + gw * i + (gw - (bw * k + gap * (k - 1))) / 2
            for j in range(k):
                bx = x0 + j * (bw + gap)
                tag = f"m{i}_{j}"
                self.create_rectangle(bx - gap / 2, top, bx + bw + gap / 2, bottom, fill=theme.CARD,
                                      outline="", tags=(tag,))
                hits.append((tag, i, j, bx))

        # grille + axe
        for step in range(5):
            v = ymax * step / 4
            yy = y(v)
            self.create_line(left, yy, right, yy, fill=theme.GRID if step else theme.BORDER)
            self.create_text(left - 8, yy, text=fmt_short(v), anchor="e", fill=theme.MUTED, font=small)

        # barres
        for tag, i, j, bx in hits:
            name, color, vals = self.series[j]
            v = vals[i]
            if v > 0:
                self.create_rectangle(bx, y(v), bx + bw, bottom, fill=color, outline="", tags=(tag,))
            self.tag_bind(tag, "<Enter>", lambda e, i=i, j=j, bx=bx: self.tooltip(i, j, bx + bw / 2))
            self.tag_bind(tag, "<Leave>", lambda e: self.delete("tip"))

        # libellés des mois
        for i, label in enumerate(self.labels):
            self.create_text(left + gw * (i + 0.5), bottom + 14, text=label, fill=theme.MUTED, font=small)

        # légende
        lx = left
        for name, color, _ in self.series:
            self.create_rectangle(lx, 14, lx + 10, 24, fill=color, outline="")
            t = self.create_text(lx + 16, 19, text=name, anchor="w", fill=theme.TEXT, font=small)
            lx = self.bbox(t)[2] + 18

    def tooltip(self, i, j, cx):
        self.delete("tip")
        name, color, vals = self.series[j]
        text = f"{self.labels[i]} · {name}\n{fmt_da(vals[i])}"
        t = self.create_text(0, 0, text=text, anchor="nw", fill=theme.WHITE, font=theme.FONT, tags=("tip",))
        x0, y0, x1, y1 = self.bbox(t)
        tw, th = x1 - x0 + 16, y1 - y0 + 10
        x = min(max(cx - tw / 2, 4), self.winfo_width() - tw - 4)
        yy = self.TOP - 4
        bg = self.create_rectangle(x, yy, x + tw, yy + th, fill=theme.TEXT, outline="", tags=("tip",))
        self.coords(t, x + 8, yy + 5)
        self.tag_raise(t, bg)
