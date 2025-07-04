# -*- coding: utf-8 -*-

from odoo import models, fields, api


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def _action_confirm(self):
        res = super(SaleOrder, self)._action_confirm()
        # check if lines has spec
        for order in self:
            if order.company_id == self.env.company.specs_sale_company_id:
                order = order.with_company(order.company_id)
                line_with_spec_ids = order.order_line.filtered(lambda l: l.sale_specs_id)
                for line in line_with_spec_ids:
                    sale_specs_id = line.sale_specs_id
                    if not sale_specs_id.specs_glass_line_ids and not sale_specs_id.specs_hardware_line_ids:
                        continue
                    if line.sale_specs_id.specs_glass_line_ids:
                        line._create_purchase_order_by_spec()
                    if not line.product_template_id.product_spec_ok and sale_specs_id.specs_hardware_line_ids:
                        line._create_purchase_order_hardware_by_spec()
        return res
