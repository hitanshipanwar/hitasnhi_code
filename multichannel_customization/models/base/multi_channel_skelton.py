# -*- coding: utf-8 -*-
##############################################################################
# Copyright (c) 2015-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
# See LICENSE file for full copyright and licensing details.
# License URL : <https://store.webkul.com/license.html/>
##############################################################################
from odoo import api, models
from logging import getLogger
_logger = getLogger(__name__)

class MultiChannelSkeleton(models.TransientModel):
    _inherit = 'multi.channel.skeleton'

    def _SetOdooOrderState(self, order_id, channel_id, feed_order_state='', payment_method=False, **kwargs):
        if channel_id.channel == 'shopify' and feed_order_state in ['Refunded', 'Canceled']:
            status_message = ''
            status = True
            if channel_id and order_id and order_id.order_line:
                ###### Create Return Delivery  #####
                if not order_id.state == 'sale':
                    resp = self._ConfirmOrderAndCreateInvoice(order_id, channel_id, payment_method, 'sale', True, 'paid', True, **kwargs)
                    status_message += resp.get('status_message')

                return_items = self._get_return_item_vals(order_id.origin)
                if order_id.state == 'sale' and order_id.picking_ids:
                    for picking_obj in order_id.picking_ids.filtered(lambda picking: picking.picking_type_code == 'outgoing' and not picking.return_ids.ids):
                        if picking_obj.state == 'cancel':
                            continue
                        if picking_obj.state not in ['done']:
                            self.set_order_shipped(order_id.id)

                        if picking_obj.state == 'done':
                            stock_return_picking = self.env['stock.return.picking']
                            stock_return_picking_obj = stock_return_picking.with_context(active_id=picking_obj.id).create({'picking_id': picking_obj.id})
                            stock_return_picking_obj._compute_moves_locations()
                            
                            if return_items:
                                for res in stock_return_picking_obj.product_return_moves:
                                    refund_products = [int(p_id) for p_id in return_items.keys()]
                                    if res.product_id.id in refund_products:
                                        res.quantity = return_items[res.product_id.id]
                                    else:
                                        res.quantity = 0

                            return_picking_res = stock_return_picking_obj.create_returns()
                            new_picking_obj = self.env['stock.picking'].browse(return_picking_res['res_id'])
                            new_picking_obj.action_assign()
                            for pack in new_picking_obj.move_line_ids:
                                if pack.quantity_product_uom > 0:
                                    pack.write({'quantity': pack.quantity_product_uom})
                                else:
                                    pack.unlink()
                            new_picking_obj.button_validate()
                            status_message += "==> Delivery Returned"

                ###### Create Credit memo/Refund  #####
                if order_id.state == 'sale' and order_id.invoice_ids:
                    invoice_id = 0
                    journal_id = 0
                    for invoice_obj in order_id.invoice_ids.filtered(lambda r: r.move_type == 'out_invoice' and r.payment_state in ['in_payment', 'paid']):
                        if invoice_obj.state == 'posted' and order_id.name == invoice_obj.invoice_origin:
                            invoice_id = invoice_obj.id
                            if invoice_obj.invoice_line_ids:
                                invoice_line = invoice_obj.invoice_line_ids[0]
                                journal_id = self.get_journal_id(invoice_obj)

                    paid_status = order_id.invoice_status
                    if invoice_id and paid_status == 'invoiced':
                        # Creating draft invoice refund
                        reversal_journal_id = self.env['account.move'].browse(invoice_id).journal_id.id
                        move_reversal = self.env['account.move.reversal'].with_context(
                            active_model="account.move", active_ids=[invoice_id]).create({
                                'journal_id': reversal_journal_id
                            })
                        reversal = move_reversal.reverse_moves()
                        refund_invoice_id = reversal['res_id']
                        refund_invoice = self.env['account.move'].browse(refund_invoice_id)
                        if return_items:
                            refund_products = [int(p_id) for p_id in return_items.keys()]
                            for invoice_line in refund_invoice.invoice_line_ids:
                                product_id = invoice_line.product_id.id
                                if product_id in refund_products:
                                    invoice_line.write({'quantity':return_items[product_id]})
                                else:
                                    invoice_line.unlink()
                        refund_invoice._compute_amount()
                        refund_invoice.action_post()

                        # Abhishek
                        # register_payments_model = self.env['account.payment.register'].with_context(active_model='account.move', active_ids=[refund_invoice_id])
                        # register_payments = register_payments_model.create({'journal_id': journal_id})
                        # register_payments.action_create_payments()

                        status_message+= "==> Refunded successfully"
                    else:
                        status = False
                        status_message += "</b> You Cannot refund an Unpaid Order."

            
                # ########## Cancel Entire Order ######
                if status and feed_order_state == 'Canceled':
                    res = self._cancel_order(order_id, channel_id)
                    status_message+=res.get('status_message')
            return status_message
        else:
            return super()._SetOdooOrderState(order_id, channel_id, feed_order_state, payment_method, **kwargs)
        
    def _get_return_item_vals(self, order_origin):
        feed_obj = self.env['order.feed']
        order_feed = feed_obj.search([('name', '=', order_origin)], limit=1)
        return_items = dict()
        if not order_feed.refund_json:
            return return_items
        for ref in eval(order_feed.refund_json):
            refund_line = ref.get('refund_line_items')
            if refund_line:
                return_items = {line.get('line_item',{}).get('variant_id') : line.get('line_item').get('quantity') for line in refund_line if line.get('line_item', {})}
        new_return_items = dict()
        if return_items:
            prod_obj = self.env['channel.product.mappings']
            prod_rec = prod_obj.search([('store_variant_id', 'in', list(return_items))])
            for rec in prod_rec:
                new_return_items[rec.product_name.id] = return_items.get(int(rec.store_variant_id))
        return new_return_items if new_return_items else {}
    

    def get_journal_id(self, invoice_obj):
        pay_term_line_ids  = invoice_obj.line_ids.filtered(lambda line: line.account_id.account_type in ('asset_receivable', 'liability_payable'))
        partials = pay_term_line_ids.mapped('matched_debit_ids') + pay_term_line_ids.mapped('matched_credit_ids')
        for partial in partials:
            counterpart_lines = partial.debit_move_id + partial.credit_move_id
            counterpart_line = counterpart_lines.filtered(lambda line: line not in invoice_obj.line_ids)
            if counterpart_line.journal_id:
                return counterpart_line.journal_id.id
