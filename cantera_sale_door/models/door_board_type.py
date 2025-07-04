from odoo import _, api, fields, models

class DoorBoardType(models.Model):
    _name = 'door.board.type'
    
    name = fields.Char(
        string='Nombre'
    )
    price = fields.Float(
        string='Precio'
    )