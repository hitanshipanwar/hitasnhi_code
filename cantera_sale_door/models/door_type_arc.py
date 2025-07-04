from odoo import _, api, fields, models

class DoorTypeArc(models.Model):
    _name = 'door.type.arc'
    
    name = fields.Char(
        string='Nombre'
    )
    price = fields.Float(
        string='Precio'
    )