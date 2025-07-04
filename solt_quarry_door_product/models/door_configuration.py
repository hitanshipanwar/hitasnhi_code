from random import randint
from odoo import _, api, fields, models


class DoorConfiguration(models.Model):
    _name = 'door.configuration'
    _inherit = 'door.abstract'
    _description = 'Setup'

    def _default_color(self):
        return randint(1, 11)
    
    name = fields.Char(
        string='Name'
    )
    color = fields.Integer('Color Index', default=_default_color)
    product_attribute_id = fields.Many2one('product.attribute', 'Attribute', required=True)