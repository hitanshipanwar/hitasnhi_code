from odoo import _, api, fields, models

class DoorTraslapeInt(models.Model):
    _name = 'door.traslape'
    
    name = fields.Char(
        string='Nombre'
    )
    price = fields.Float(
        string='Precio'
    )