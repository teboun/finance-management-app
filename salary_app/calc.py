"""Calculs de salaire (sans interface, testable)."""
import calendar
from datetime import date, timedelta

# Paramètres modifiables
DAYS_PER_MONTH = 30      # salaire mensuel / 30 = taux journalier
DAYS_PER_WEEK = 6        # salaire hebdomadaire / 6 = taux journalier
DAY_OFF = 4              # jour de repos (0=lundi ... 4=vendredi)
WEEK_START = 5           # début de semaine (5=samedi)
HOURS_PER_WEEK = 40      # durée légale (loi 90-11)
HOURS_PER_DAY = 8
OVERTIME_RATE = 1.5      # heures sup majorées d'au moins 50 %
MAX_OVERTIME_PER_WEEK = HOURS_PER_WEEK * 0.2  # 20 % de la durée légale = 8 h

PAY_TYPES = ("monthly", "weekly", "daily")


def daily_rate(pay_type, base):
    """Taux journalier selon le type de paie."""
    if pay_type == "monthly":
        return base / DAYS_PER_MONTH
    if pay_type == "weekly":
        return base / DAYS_PER_WEEK
    if pay_type == "daily":
        return base
    raise ValueError(f"type de paie inconnu: {pay_type}")


def hourly_rate(pay_type, base):
    """Taux horaire: mensuel / 173,33 h, hebdo / 40 h, journalier / 8 h."""
    if pay_type == "monthly":
        return base / (HOURS_PER_WEEK * 52 / 12)
    if pay_type == "weekly":
        return base / HOURS_PER_WEEK
    if pay_type == "daily":
        return base / HOURS_PER_DAY
    raise ValueError(f"type de paie inconnu: {pay_type}")


def overtime_amount(pay_type, base, hours):
    """Montant des heures supplémentaires."""
    return round(hours * hourly_rate(pay_type, base) * OVERTIME_RATE, 2)


def month_period(d):
    """(premier jour, dernier jour) du mois de la date d."""
    last = calendar.monthrange(d.year, d.month)[1]
    return date(d.year, d.month, 1), date(d.year, d.month, last)


def week_period(d):
    """(début, fin) de la semaine contenant d (commence le samedi)."""
    start = d - timedelta(days=(d.weekday() - WEEK_START) % 7)
    return start, start + timedelta(days=6)


def working_days(start, end):
    """Nombre de jours travaillés entre start et end inclus (hors jour de repos)."""
    n, d = 0, start
    while d <= end:
        if d.weekday() != DAY_OFF:
            n += 1
        d += timedelta(days=1)
    return n


def period_gross(pay_type, base, start, end):
    """Salaire brut pour la période [start, end]."""
    days = (end - start).days + 1
    if pay_type == "monthly":
        if (start, end) == month_period(start):
            return base
        return base / DAYS_PER_MONTH * days
    if pay_type == "weekly":
        if days == 7:
            return base
        return base / 7 * days
    if pay_type == "daily":
        return base * working_days(start, end)
    raise ValueError(f"type de paie inconnu: {pay_type}")


def compute_payslip(pay_type, base, absence_days, purchases_total, start, end, bonuses_total=0):
    """Retourne le détail du salaire pour la période."""
    gross = period_gross(pay_type, base, start, end)
    absence_deduction = absence_days * daily_rate(pay_type, base)
    net = gross + bonuses_total - absence_deduction - purchases_total
    return {
        "gross": round(gross, 2),
        "bonuses": round(bonuses_total, 2),
        "daily_rate": round(daily_rate(pay_type, base), 2),
        "absence_days": absence_days,
        "absence_deduction": round(absence_deduction, 2),
        "purchases_deduction": round(purchases_total, 2),
        "net": round(net, 2),
    }


def fmt_num(value):
    """2.0 -> '2', 1.5 -> '1,5' (jours, heures)."""
    value = round(float(value or 0), 2)
    return str(int(value)) if value == int(value) else f"{value:g}".replace(".", ",")


def fmt_da(amount):
    """12345.5 -> '12 345,50 DA'"""
    amount = round(amount, 2) + 0.0  # évite "-0,00"
    s = f"{amount:,.2f}".replace(",", " ").replace(".", ",")
    return f"{s} DA"
