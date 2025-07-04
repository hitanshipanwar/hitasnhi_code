# -*- coding: utf-8 -*-

from odoo import models, fields, api


class AccountMove(models.Model):
    _inherit = 'account.move'

    can_hide_register_payment_btn = fields.Boolean(compute="_compute_can_show_register_payment_btn",
                                         help="Can show Register Payment button")

    @api.depends_context('uid')
    def _compute_can_show_register_payment_btn(self):
        for record in self:
            record = record.with_company(record.company_id)
            record.can_hide_register_payment_btn = bool(
                self.user_has_groups('solt_quarry_hide_register_payment_button_invoice.group_quarry_hide_register_payment_btn_invoice'))

