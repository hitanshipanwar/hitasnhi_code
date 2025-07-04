# -*- coding: utf-8 -*-

from odoo import fields, models


class DoorFamily(models.Model):
    _name = 'door.family'
    _inherit = 'door.abstract'
    _description = 'Door family'

    pricelist_ids = fields.Many2many('product.pricelist', 'product_family_pricelist_rel', 'family_id', 'pricelist_id', string="Pricelist", required=True)
    product_attribute_id = fields.Many2one('product.attribute', 'Attribute', required=True)
    door_family_field_line_ids = fields.One2many('door.family.field.line', 'door_family_id', string='Fields')


class DoorFamilyFieldLines(models.Model):
    _name = 'door.family.field.line'
    _description = 'Door family fields configuration'

    door_family_id = fields.Many2one('door.family', 'Door family', ondelete='cascade')
    cost_price_field = fields.Boolean('Is cost field',
                                      help='When checking the field, it will be used to calculate the cost of the Specs')
    sale_price_field = fields.Boolean('Is sale price field',
                                      help='When checking the field, it will be used to calculate the sale price of the Specs')