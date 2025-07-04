# -*- coding: utf-8 -*-

from odoo import fields, models, api


class ProductLabelLayout(models.TransientModel):
    _inherit = 'product.label.layout'


    print_format = fields.Selection(selection_add=[
        ('4x7_english', '4 X 7 English'),
        ('4x7_thai', '4 X 7 Thai')],
        ondelete={'4x7_english': 'set default','4x7_thai': 'set default'}
    )

    def _prepare_report_data(self):
        result = super(ProductLabelLayout, self)._prepare_report_data()
        if self.print_format == '4x7_english':
            data = list(result)
            data[1].update({'is_thai' : False})
            data[0] = 'crm_design.report_product_template_shelf_talker'
            result = tuple(data)
        elif self.print_format == '4x7_thai':
            data = list(result)
            data[1].update({'is_thai' : True})
            data[0] = 'crm_design.report_product_template_shelf_talker'
            result = tuple(data)
        return result