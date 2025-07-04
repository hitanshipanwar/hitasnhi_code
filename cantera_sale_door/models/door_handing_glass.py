from odoo import _, api, fields, models

class DoorHandingGlass(models.Model):
    _name = 'door.handing.glass'
    
    name = fields.Char(
        string='Nombre'
    )
    price = fields.Float(
        string='Precio'
    )