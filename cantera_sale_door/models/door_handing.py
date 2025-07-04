from odoo import _, api, fields, models

class DoorHanding(models.Model):
    _name = 'door.handing'
    
    name = fields.Char(
        string='Nombre'
    )
    price = fields.Float(
        string='Precio'
    )