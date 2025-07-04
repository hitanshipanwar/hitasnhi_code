from odoo import _, api, fields, models

class DoorDesign(models.Model):
    _name = 'door.design'
    
    name = fields.Char(
        string='Nombre'
    )
    price = fields.Float(
        string='Precio'
    )