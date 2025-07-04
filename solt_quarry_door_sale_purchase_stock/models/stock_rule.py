# -*- coding: utf-8 -*-


from odoo import api, fields, models, _


class StockRule(models.Model):
    _inherit = 'stock.rule'

    def _get_stock_move_values(self, product_id, product_qty, product_uom, location_dest_id, name, origin, company_id,
                               values):
        partner = self.partner_address_id or (values.get('group_id', False) and values['group_id'].partner_id)
        if partner:
            product_id = product_id.with_context(lang=partner.lang or self.env.user.lang)
        picking_description = product_id._get_description(self.picking_type_id)
        if values.get('product_description_variants') and values.get('sale_line_id'):
            picking_description += '\n' + values['product_description_variants']
        values = super(StockRule, self)._get_stock_move_values(product_id, product_qty, product_uom, location_dest_id, name, origin, company_id,
                               values)
        if picking_description:
            values['description_picking'] = picking_description

        return values