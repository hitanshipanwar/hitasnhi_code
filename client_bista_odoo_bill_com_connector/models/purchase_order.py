# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    # This function is overrided because wanted to make a relation based on the Vendor Reference.
    # @api.depends('order_line.invoice_lines.move_id')
    # def _compute_invoice(self):
    #     account_move_obj = self.env['account.move']
    #     for order in self:
    #         invoices = order.mapped('order_line.invoice_lines.move_id')
    #         po_name = order.name
    #         if po_name and order.partner_id:
    #             cr = order._cr
    #             cr.execute("""SELECT id from account_move move where move.invoice_origin='%s' and move.partner_id=%s""" % (po_name, order.partner_id.id))
    #             invoice_exists = list(filter(None, map(lambda x: x[0], cr.fetchall())))
    #             if invoice_exists:
    #                 invoices |= account_move_obj.sudo().browse(invoice_exists)
    #         order.invoice_ids = invoices
    #         order.invoice_count = len(invoices)

    # This function is to update Currency Exchange rate when Invoice is created from the PO.
    def _prepare_invoice(self):
        res = super(PurchaseOrder, self)._prepare_invoice()
        if res:
            company_id = res.get('company_id', False)
            company_id_brw = self.env['res.company'].sudo().browse(company_id)
            company_currency_id = company_id_brw.currency_id.id
            bill_currency = res.get('currency_id', False)
            if bill_currency and company_currency_id != bill_currency:
                bill_currency_brw = self.env['res.currency'].sudo().browse(bill_currency)
                company_rec = bill_currency_brw.rate_ids.filtered(lambda l: l.company_id == company_id_brw)
                if company_rec:
                    currency_exchange_rate = bill_currency_brw.rate
                else:
                    currency_exchange_rate = 1.00
                res.update({'currency_exchange_rate': currency_exchange_rate})
        return res
