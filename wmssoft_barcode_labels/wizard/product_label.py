from odoo import fields, models


class ProductLabelLayout(models.TransientModel):
    _inherit = 'product.label.layout'

    print_format = fields.Selection(selection_add=[('2x7', '2 x 7')], ondelete={'2x7': 'set default'})