# -*- coding: utf-8 -*-


from odoo import models, fields, api
from odoo.exceptions import UserError


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    show_button_update_price = fields.Boolean(compute="_compute_show_button_update_price_order")
    is_update_cost_by_specs = fields.Boolean()

    @api.depends('order_line', 'order_line.show_button_update_price')
    def _compute_show_button_update_price_order(self):
        for order in self:
            order.show_button_update_price = True if any(line.show_button_update_price for line in order.order_line) and order.state in ['draft', 'sent'] else False

    def action_update_cost_by_specs(self):
        self.ensure_one()
        sale_order_ids = self._get_sale_orders()
        origin_split = self.origin.split(',')
        for origin in origin_split:
            origin = origin.strip()
            sale_order_id = sale_order_ids.filtered(lambda s: s.state == 'sale' and s.name == origin)
            for line in self.order_line:
                line.action_update_line_cost_by_specs(sale_order_id)
        if origin_split:
            self.is_update_cost_by_specs = True

    def button_confirm(self):
        for order in self:
            if not order.is_update_cost_by_specs and order.show_button_update_price:
                raise UserError("You must update the price on the lines first. Click the button Update price from Specs;")
        return super(PurchaseOrder, self).button_confirm()
