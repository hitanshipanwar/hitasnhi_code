from odoo import fields, models


class DoorTypeGlass(models.Model):
    _name = 'door.type.glass'
    _inherit = 'door.abstract'
    _description = 'Door type of glass'

    type = fields.Selection([
        ('door', 'For door'),
        ('transom', 'For transom'),
        ('sidelight', 'For sidelight')
    ], 'Type', default='door')
