# Copyright 2020 Ecosoft Co., Ltd (https://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from num2words import num2words
from odoo import models


class WithholdingTaxCert(models.Model):
    _inherit = "withholding.tax.cert"

    def _get_report_base_filename(self):
        self.ensure_one()
        return "WT Certificates - {}".format(self.display_name)

    def _compute_desc_type_other(self, lines, ttype, income_type):
        base_type_other = lines.filtered(
            lambda l: l.wt_cert_income_type in [income_type]
        ).mapped(ttype)
        base_type_other = [x or "" for x in base_type_other]
        desc = ", ".join(base_type_other)
        return desc

    def _group_wt_line(self, lines):
        groups = self.env["withholding.tax.cert.line"].read_group(
            domain=[("id", "in", lines.ids)],
            fields=["wt_cert_income_type", "wt_percent" ,"base", "amount"],
            groupby=["wt_cert_income_type"],
            lazy=False,
        )
        return groups
        

    def month_translate(self, val):
        res = val
        if res == '01':
            return "มกราคม"
        if res == '02':
            return "ภุมภาพันธ์"
        if res == '03':
            return "เมษายน"
        if res == '04':
            return "เมษายน"
        if res == '05':
            return "พฤษภาคม"
        if res == '06':
            return "มิถุนายน"
        if res == '07':
            return "กรกฎาคม"
        if res == '08':
            return "สิงหาคม"
        if res == '09':
            return "กันยายน"
        if res == '10':
            return "ตุลาคม"
        if res == '11':
            return "พฤศจิกายน"
        if res == '12':
            return "ธันวาคม"

    

   
