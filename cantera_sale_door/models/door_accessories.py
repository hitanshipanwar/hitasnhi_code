from odoo import _, api, fields, models

class DoorAccessories(models.Model):
    _name = 'door.accessories'
    
    accessories_id = fields.Many2one(
        'door.accessories.list',
        string='Accesorios'
    )
    amount_accessories = fields.Integer(
        string='Cantidad'
    )
    sequence = fields.Integer()
    acc_id = fields.Many2one(
        'specs.sale',
        string='Accesorios'
    )