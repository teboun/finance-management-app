"""Fiche de paie imprimable (HTML)."""
from html import escape

from .calc import fmt_da


def payslip_html(t, emp_name, pay_type_label, start, end, slip):
    """t = fonction de traduction (clé -> texte). Retourne une page HTML complète."""
    lines = [
        (t("gross"), slip["gross"], ""),
        (t("bonuses"), slip.get("bonuses", 0), "+"),
        (f'{t("abs_ded")} ({slip["absence_days"]} {t("days").lower()})', slip["absence_deduction"], "−"),
        (t("purchases"), slip["purchases_deduction"], "−"),
    ]
    rows = "".join(f"<tr><td>{escape(label)}</td><td class='num'>{sign} {fmt_da(amount)}</td></tr>"
                   for label, amount, sign in lines)
    return f"""<!doctype html>
<html><head><meta charset="utf-8"><title>{escape(t("payslip"))} - {escape(emp_name)}</title>
<style>
body {{ font-family: Arial, sans-serif; max-width: 720px; margin: 32px auto; color: #222; }}
h1 {{ font-size: 22px; border-bottom: 2px solid #222; padding-bottom: 8px; }}
.info td {{ padding: 4px 12px 4px 0; }}
table.lines {{ width: 100%; border-collapse: collapse; margin-top: 24px; }}
table.lines td {{ border-bottom: 1px solid #ccc; padding: 10px 6px; }}
.num {{ text-align: right; white-space: nowrap; }}
tr.net td {{ font-weight: bold; font-size: 18px; border-top: 2px solid #222; border-bottom: none; }}
.sign {{ display: flex; justify-content: space-between; margin-top: 64px; }}
.sign div {{ width: 45%; border-top: 1px solid #222; padding-top: 6px; text-align: center; }}
.print {{ margin-top: 32px; padding: 8px 16px; font-size: 14px; }}
@media print {{ .print {{ display: none; }} body {{ margin: 0 auto; }} }}
</style></head><body>
<h1>{escape(t("payslip"))}</h1>
<table class="info">
<tr><td><b>{escape(t("employee"))}</b></td><td>{escape(emp_name)}</td></tr>
<tr><td><b>{escape(t("pay_type"))}</b></td><td>{escape(pay_type_label)}</td></tr>
<tr><td><b>{escape(t("period"))}</b></td><td>{escape(t("from_to").format(start, end))}</td></tr>
<tr><td><b>{escape(t("rate"))}</b></td><td>{fmt_da(slip["daily_rate"])}</td></tr>
</table>
<table class="lines">{rows}
<tr class="net"><td>{escape(t("net_pay"))}</td><td class="num">{fmt_da(slip["net"])}</td></tr>
</table>
<div class="sign"><div>{escape(t("sign_employer"))}</div><div>{escape(t("sign_employee"))}</div></div>
<button class="print" onclick="window.print()">{escape(t("print"))}</button>
</body></html>"""
