from odoo import _, api, fields, models

class DoorPosition(models.Model):
    _name = 'door.position'
    
    name = fields.Char(
        string='Nombre'
    )
    price = fields.Float(
        string='Precio'
    )