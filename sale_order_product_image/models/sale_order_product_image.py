from odoo import models, fields, exceptions, api, _
from odoo.exceptions import UserError, ValidationError


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    product_image = fields.Binary(string="Image", related='product_id.image_1920', readonly=True)

    @api.onchange('product_id')
    def _onchange_product_id_image(self):
        for line in self:
            if line.product_id:
                line.product_image = line.product_id.image_1920
            else:
                line.product_image = False