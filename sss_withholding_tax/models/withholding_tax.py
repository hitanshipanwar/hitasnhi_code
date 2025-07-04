from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class AccountWithholdingTax(models.Model):
    _name = "account.withholding.tax"
    _description = "Account Withholding Tax"

    name = fields.Char(required=True)
    thai_name = fields.Char(string="Thai Name")
    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Company"
    )
    account_id = fields.Many2one(
        comodel_name="account.account",
        string="Withholding Tax Account",
        domain="[('wt_account', '=', True), '|', ('company_id', '=', company_id), ('company_id', '=', False)]",
        required=True,
        ondelete="restrict",
    )
    amount = fields.Float(
        string="Amount",
    )
    wt_type = fields.Char(
        string="WT Type"
    )

    @api.constrains("account_id")
    def _check_account_id(self):
        for rec in self:
            if rec.account_id and not rec.account_id.wt_account:
                raise ValidationError(_("Selected account is not for withholding tax"))