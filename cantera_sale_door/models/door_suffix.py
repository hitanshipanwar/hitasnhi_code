from odoo import _, api, fields, models

class DoorSuffix(models.Model):
    _name = 'door.suffix'
    
    name = fields.Char(
        string='Nombre'
    )
    price = fields.Float(
        string='Precio'
    )