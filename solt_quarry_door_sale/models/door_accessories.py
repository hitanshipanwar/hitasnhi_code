from odoo import _, api, fields, models


class DoorAccessories(models.Model):
    _name = 'door.accessories'
    _description = 'Door Accessories'
    
    accessories_id = fields.Many2one('door.accessories.list', string='Accessories')
    amount_accessories = fields.Integer(string='Quantity')
    sequence = fields.Integer()
    specs_id = fields.Many2one('specs.sale', string='Specs', ondelete='cascade', index=True, copy=False)