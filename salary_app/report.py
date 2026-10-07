"""Fiche de paie imprimable (HTML)."""
from html import escape

from .calc import fmt_da, fmt_num

STYLE = """
body { font-family: Arial, sans-serif; color: #222; margin: 0; background: #f3f5f8; }
.slip { max-width: 720px; margin: 24px auto; padding: 32px 40px; background: #fff;
        border: 1px solid #dce2ea; border-radius: 8px; }
.company { color: #1F4E79; margin-bottom: 20px; line-height: 1.5; }
.co-name { font-size: 20px; font-weight: bold; }
h1 { font-size: 22px; border-bottom: 2px solid #222; padding-bottom: 8px; }
.info td { padding: 4px 12px 4px 0; }
table.lines { width: 100%; border-collapse: collapse; margin-top: 24px; }
table.lines td { border-bottom: 1px solid #ccc; padding: 10px 6px; }
.num { text-align: right; white-space: nowrap; }
tr.net td { font-weight: bold; font-size: 18px; border-top: 2px solid #222; border-bottom: none; }
.sign { display: flex; justify-content: space-between; margin-top: 64px; }
.sign div { width: 45%; border-top: 1px solid #222; padding-top: 6px; text-align: center; }
.toolbar { text-align: center; margin: 24px; }
.print { padding: 10px 24px; font-size: 15px; background: #2E75B6; color: #fff; border: 0;
         border-radius: 6px; cursor: pointer; }
@media print {
  body { background: #fff; }
  .toolbar { display: none; }
  .slip { border: 0; margin: 0 auto; padding: 0; break-after: page; }
  .slip:last-of-type { break-after: auto; }
}
"""


def company_block(company):
    """En-tête entreprise (nom, adresse, téléphone, NIF) si renseigné."""
    company = company or {}
    if not any(company.values()):
        return ""
    lines = [f"<div class='co-name'>{escape(company.get('company_name', ''))}</div>"]
    for key in ("company_address", "company_phone"):
        if company.get(key):
            lines.append(f"<div>{escape(company[key])}</div>")
    if company.get("company_nif"):
        lines.append(f"<div>NIF : {escape(company['company_nif'])}</div>")
    return f"<div class='company'>{''.join(lines)}</div>"


def payslip_section(t, emp_name, pay_type_label, start, end, slip, company=None):
    """Une fiche de paie (bloc HTML)."""
    lines = [
        (t("gross"), slip["gross"], ""),
        (t("bonuses"), slip.get("bonuses", 0), "+"),
        (f'{t("abs_ded")} ({fmt_num(slip["absence_days"])} {t("days").lower()})', slip["absence_deduction"], "−"),
        (t("purchases"), slip["purchases_deduction"], "−"),
    ]
    rows = "".join(f"<tr><td>{escape(label)}</td><td class='num'>{sign} {fmt_da(amount)}</td></tr>"
                   for label, amount, sign in lines)
    return f"""<section class="slip">
{company_block(company)}
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
</section>"""


def payslips_document(t, sections, title):
    """Page HTML complète: une fiche par page à l'impression."""
    return f"""<!doctype html>
<html><head><meta charset="utf-8"><title>{escape(title)}</title><style>{STYLE}</style></head><body>
<div class="toolbar"><button class="print" onclick="window.print()">{escape(t("print"))}</button></div>
{"".join(sections)}
</body></html>"""


def payslip_html(t, emp_name, pay_type_label, start, end, slip, company=None):
    """t = fonction de traduction (clé -> texte); company = dict des paramètres entreprise.
    Retourne une page HTML complète pour une seule fiche."""
    section = payslip_section(t, emp_name, pay_type_label, start, end, slip, company)
    return payslips_document(t, [section], f"{t('payslip')} - {emp_name}")
