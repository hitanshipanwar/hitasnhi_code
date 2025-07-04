# -*- coding: utf-8 -*-

from odoo import fields, models


class ProductAttributeValue(models.Model):
    _inherit = 'product.attribute.value'

    family_product_id = fields.Many2one('door.family', 'Product family', domain="[('product_attribute_id', '=', attribute_id)]")
    config_id = fields.Many2one('door.configuration', 'Setup', domain="[('product_attribute_id', '=', attribute_id)]")