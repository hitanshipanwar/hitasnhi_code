from odoo import _, api, fields, models

class DoorTypeGlass(models.Model):
    _name = 'door.type.glass'
    
    name = fields.Char(
        string='Nombre'
    )
    price = fields.Float(
        string='Precio'
    )