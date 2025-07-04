# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.
from odoo import models, fields, _


class StockPicking(models.Model):
    """
    Inherited to connect the picking with WooCommerce.
    @author: Maulik Barad on Date 14-Nov-2019.
    Migrated by Maulik Barad on Date 07-Oct-2021.
    """
    _inherit = "stock.picking"

    updated_in_woo = fields.Boolean(default=False)
    is_woo_delivery_order = fields.Boolean("WooCommerce Delivery Order")
    woo_instance_id = fields.Many2one("woo.instance.ept", "Woo Instance")
    canceled_in_woo = fields.Boolean("Cancelled In woo", default=False)

    def send_to_shipper(self):
        self.ensure_one()
        if self.carrier_id.send_shipping(self):
            res = self.carrier_id.send_shipping(self)[0]
            if self.carrier_id.free_over and self.sale_id and self.sale_id._compute_amount_total_without_delivery() >= self.carrier_id.amount:
                res['exact_price'] = 0.0
            self.carrier_price = res['exact_price'] * (1.0 + (self.carrier_id.margin / 100.0))
            if res['tracking_number']:
                previous_pickings = self.env['stock.picking']
                previous_moves = self.move_lines.move_orig_ids
                while previous_moves:
                    previous_pickings |= previous_moves.picking_id
                    previous_moves = previous_moves.move_orig_ids
                without_tracking = previous_pickings.filtered(lambda p: not p.carrier_tracking_ref)
                (self + without_tracking).carrier_tracking_ref = res['tracking_number']
                for p in previous_pickings - without_tracking:
                    p.carrier_tracking_ref += "," + res['tracking_number']
        order_currency = self.sale_id.currency_id or self.company_id.currency_id
        msg = _(
            "Shipment sent to carrier %(carrier_name)s for shipping with tracking number %(ref)s<br/>Cost: %(price).2f %(currency)s",
            carrier_name=self.carrier_id.name,
            ref=self.carrier_tracking_ref,
            price=self.carrier_price,
            currency=order_currency.name
        )
        self.message_post(body=msg)
        self._add_delivery_cost_to_so()