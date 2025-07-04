from odoo import fields, models


class DoorHandle(models.Model):
    _name = 'door.handle'
    _inherit = 'door.abstract'
    _description = 'Door handle'

    type = fields.Selection([
        ('internal_active', 'Internal Active Handle'),
        ('external_active', 'External Active Handle'),
        ('internal_inactive', 'Internal Inactive Handle'),
        ('external_inactive', 'External Inactive Handle'),
    ], 'Type', default='internal_active')