from odoo import _, api, fields, models

class DoorAssembly(models.Model):
    _name = 'door.assembly'
    
    name = fields.Char(
        string='Nombre'
    )
    price = fields.Float(
        string='Precio'
    )