from odoo import _, api, fields, models

class DoorRadius(models.Model):
    _name = 'door.radius'
    
    name = fields.Char(
        string='Nombre'
    )
    price = fields.Float(
        string='Precio'
    )