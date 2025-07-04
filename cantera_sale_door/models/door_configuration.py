from odoo import _, api, fields, models

class DoorConfiguration(models.Model):
    _name = 'door.configuration'
    
    name = fields.Char(
        string='Nombre'
    )
    price = fields.Float(
        string='Precio'
    )