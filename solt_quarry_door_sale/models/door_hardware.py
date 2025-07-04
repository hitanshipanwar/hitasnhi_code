from odoo import _, api, fields, models


class DoorHardware(models.Model):
    _name = 'door.hardware'
    _description = 'Door Hardware'

    hardware_id = fields.Many2one('door.hardware.list', string='Products')
    specs_id = fields.Many2one('specs.sale', string='Specs', ondelete='cascade', index=True, copy=False)
    include_in_spec_price = fields.Boolean('Include in spec price?')
    amount = fields.Integer(string='Quantity', required=True)
    sequence = fields.Integer(default=10)