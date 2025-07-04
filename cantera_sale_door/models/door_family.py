from odoo import _, api, fields, models

class DoorFamily(models.Model):
    _name = 'door.family'
    
    name = fields.Char(
        string='Nombre'
    )
    price = fields.Float(
        string='Precio'
    )