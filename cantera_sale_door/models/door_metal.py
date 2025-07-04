from odoo import _, api, fields, models

class DoorMetal(models.Model):
    _name = 'door.metal'
    
    name = fields.Char(
        string='Nombre'
    )
    price = fields.Float(
        string='Precio'
    )