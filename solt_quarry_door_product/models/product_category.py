# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class ProductCategory(models.Model):
    _inherit = "product.category"

    is_hardware_categ = fields.Boolean('Is Specs Category',
                                       help="This category will be used to identify the products that will be shown in the Specs for Accessories, Special Preparations and Hardwares")

    @api.constrains('is_hardware_categ')
    def _check_is_hardware_categ(self):
        for record in self:
            if record.is_hardware_categ:
                categories = self.env['product.category'].search(
                    [('id', '!=', record.id), ('is_hardware_categ', '=', True), ('parent_id', '=', False)])
                if categories:
                    raise ValidationError(
                        _(f"There is already a category marked as Specs Category."))
