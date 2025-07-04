# Copyright 2020 Ecosoft Co., Ltd (https://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)
from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools import float_compare

class AccountPaymentRegister(models.TransientModel):
    _inherit = "account.payment.register"

    wt_tax_id = fields.Many2one(
        comodel_name="account.withholding.tax",
        string="Withholding Tax",
        help="Optional hidden field to keep wt_tax. Useful for case 1 tax only",
    )
    wt_amount_base = fields.Monetary(
        string="Withholding Base",
        help="Based amount for the tax amount",
    )

    payment_difference_handling = fields.Selection(
        string="Payment Difference Handling",
        selection=[('open', 'Keep open'), ('reconcile', 'Mark as fully paid'), ('reconcile_multi_deduct', 'Mark invoice as fully paid (multi deduct)')],
        compute='_compute_payment_difference_handling',
        store=True,
        readonly=False,
    )
    deduct_residual = fields.Monetary(
        string="Remainings", compute="_compute_deduct_residual"
    )
    deduction_ids = fields.One2many(
        comodel_name="account.payment.deduction",
        inverse_name="payment_id",
        string="Deductions",
        copy=False,
        help="Sum of deduction amount(s) must equal to the payment difference",
    )
    is_multiple = fields.Boolean('Is Multiple', compute="_compute_amount")

    def action_create_payments(self):
        if self.payment_difference_handling == "reconcile_multi_deduct":
            self = self.with_context(
                skip_account_move_synchronization=True,
                dont_redirect_to_payments=True,
            )
        return super().action_create_payments()

    @api.constrains("deduction_ids", "payment_difference_handling")
    def _check_deduction_amount(self):
        prec_digits = self.env.user.company_id.currency_id.decimal_places
        for rec in self:
            if rec.payment_difference_handling == "reconcile_multi_deduct":
                if (
                    float_compare(
                        rec.payment_difference,
                        abs(sum(rec.deduction_ids.mapped("amount"))),
                        precision_digits=prec_digits,
                    )
                    != 0
                ):
                    raise UserError(
                        _("The total deduction should be %s") % rec.payment_difference
                    )

    @api.depends("payment_difference", "deduction_ids")
    def _compute_deduct_residual(self):
        for rec in self:
            rec.deduct_residual = rec.payment_difference - sum(
                rec.deduction_ids.mapped("amount")
            )

    def _create_payment_vals_from_wizard(self, batch_result):
        payment_vals = super()._create_payment_vals_from_wizard(batch_result)
        # Check case auto and manual withholding tax
        if self.payment_difference_handling == "reconcile" and self.wt_tax_id:
            payment_vals.update({"wt_tax_id": self.wt_tax_id.id})

        if (
            self.payment_difference
            and self.payment_difference_handling == "reconcile_multi_deduct"
        ):
            payment_vals["write_off_line_vals"] = [
                self._prepare_deduct_move_line(deduct)
                for deduct in self.deduction_ids.filtered(lambda l: not l._open)
            ]


        if (
            self.payment_difference
            and self.payment_difference_handling == "open"
        ):
            if self.deduction_ids:
                payment_vals["write_off_line_vals"] = [
                    self._prepare_deduct_move_line(deduct)
                    for deduct in self.deduction_ids.filtered(lambda l: not l._open)
                ]
        return payment_vals

    def _prepare_deduct_move_line(self, deduct):
        active_ids = self._context.get("active_ids", [])
        invoices = self.env["account.move"].browse(active_ids)
        move_type = ''
        if 'in_invoice' in invoices.mapped('move_type'):
            move_type = 'in_invoice'
        return {
            "name": deduct.name,
            "amount_currency": deduct.amount if move_type == 'in_invoice' else abs(deduct.amount),
            "account_id": deduct.account_id.id,
            "wt_tax_id": deduct.wt_tax_id.id,
            'balance': deduct.amount if move_type == 'in_invoice' else abs(deduct.amount),
        }

    @api.onchange("payment_difference_handling")
    def _onchange_payment_difference_handling(self):
        if not self.payment_difference_handling == "reconcile_multi_deduct":
            return
        if self._context.get("active_model") == "account.move":
            active_ids = self._context.get("active_ids", [])
            invoices = self.env["account.move"].browse(active_ids)
            inv_lines = invoices.mapped("invoice_line_ids").filtered("wt_tax_id")
            if inv_lines:
                deductions = [(5, 0, 0)]
                for line in inv_lines:
                    deduct = {
                        "wt_tax_id": line.wt_tax_id.id,
                        "account_id": line.wt_tax_id.account_id.id,
                        "name": line.wt_tax_id.display_name,
                        "amount": line.wt_tax_id.amount / 100 * line.price_subtotal,
                    }
                    deductions.append((0, 0, deduct))
                self.deduction_ids = deductions

    @api.onchange("wt_tax_id", "wt_amount_base")
    def _onchange_wt_tax_id(self):
        if self.wt_tax_id and self.wt_amount_base:
            amount_wt = self.wt_tax_id.amount / 100 * self.wt_amount_base
            self.amount = self.source_amount_currency - abs(amount_wt)
            self.writeoff_account_id = self.wt_tax_id.account_id
            self.writeoff_label = self.wt_tax_id.display_name
    # def _create_payment_vals_from_wizard(self,batch_result):
    #     payment_vals = super()._create_payment_vals_from_wizard(batch_result)
    #     # Check case auto and manual withholding tax
    #     if self.payment_difference_handling == "reconcile" and self.wt_tax_id:
    #         payment_vals.update({"wt_tax_id": self.wt_tax_id.id})
    #     return payment_vals

    def _update_payment_register(self, amount_base, amount_wt, inv_lines):
        self.ensure_one()
        if inv_lines[0].move_id.move_type == 'out_invoice':
            self.amount -= abs(amount_wt)
        else:
            self.amount += amount_wt

        self.wt_amount_base = amount_base
        self.payment_difference_handling = "reconcile"
        wt_tax = inv_lines.mapped("wt_tax_id")
        if wt_tax and len(wt_tax) == 1:
            self.wt_tax_id = wt_tax
            self.writeoff_account_id = self.wt_tax_id.account_id
            self.writeoff_label = self.wt_tax_id.display_name
        return True

    @api.depends(
        "source_amount",
        "source_amount_currency",
        "source_currency_id",
        "company_id",
        "currency_id",
        "payment_date",
    )
    def _compute_amount(self):
        res = super()._compute_amount()
        # Get the sum withholding tax amount from invoice line
        if self._context.get("active_model") == "account.move":
            active_ids = self._context.get("active_ids", [])
            invoices = self.env["account.move"].browse(active_ids)
            move_lines = invoices.mapped("line_ids").filtered("wt_tax_id")
            if not move_lines:
                return res
            # Case WHT only, ensure only 1 wizard
            self.ensure_one()
            amount_base, amount_wt = move_lines._get_wt_amount(
                self.currency_id, self.payment_date
            )
            if amount_wt:
                self._update_payment_register(amount_base, amount_wt, move_lines)
            if len(move_lines) > 1:
                self.is_multiple = True
            else:
                self.is_multiple = False
        return res

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        if self._context.get("active_model") == "account.move":
            active_ids = self._context.get("active_ids", False)
            move_ids = self.env["account.move"].browse(active_ids)
            partner_ids = move_ids.mapped("partner_id")
            wt_tax_line = move_ids.line_ids.filtered("wt_tax_id")
            if len(partner_ids) > 1 and wt_tax_line:
                raise UserError(
                    _(
                        "You can't register a payment for invoices "
                        "(with withholding tax) belong to multiple partners."
                    )
                )
            res["group_payment"] = True
        return res

    def _create_payments(self):
        self.ensure_one()
        if self.wt_tax_id and not self.group_payment:
            raise UserError(
                _(
                    "Please check Group Payments when dealing "
                    "with multiple invoices that has withholding tax."
                )
            )
        return super()._create_payments()
