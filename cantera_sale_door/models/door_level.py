from odoo import _, api, fields, models

class DoorLevel(models.Model):
    _name = 'door.level'
    
    name = fields.Char(
        string='Nombre'
    )
    price = fields.Float(
        string='Precio'
    )