# -*- coding: utf-8 -*-

from odoo import models, fields, api


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.model_create_multi
    def create(self, vals_list):
        context = self.env.context.copy()
        context.update({'not_update_specs_version': True})
        orders = super(SaleOrder, self.with_context({k: v for k, v in context.items()})).create(vals_list)

        # link the specs with their respective line
        for order in orders:
            if order.specs_sale_ids:
                for line in order.order_line:
                    specs_id = order.specs_sale_ids.filtered(lambda s: s.name == line.sale_specs_name and s.state != 'cancel')
                    line.sale_specs_id = specs_id and specs_id.id or False

        return orders
