from odoo import _, api, fields, models

class DoorGlassPiece(models.Model):
    _name = 'door.glass.piece'
    
    name = fields.Char(
        string='Nombre'
    )
    price = fields.Float(
        string='Precio'
    )