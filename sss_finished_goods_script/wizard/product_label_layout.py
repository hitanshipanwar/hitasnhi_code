# -*- coding: utf-8 -*-

from odoo import fields, models, api


class ProductLabelLayout(models.TransientModel):
    _inherit = 'product.label.layout'

    def _prepare_report_data(self):
        result = super(ProductLabelLayout, self)._prepare_report_data()
        if self._context.get('active_model') == 'stock.move':
            data = list(result)
            data[0] = 'sss_finished_goods_script.report_product_template_shelf_talker_stock_move'
            result = tuple(data)
        return result
