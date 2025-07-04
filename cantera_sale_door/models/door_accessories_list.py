from odoo import _, api, fields, models

class DoorAccessoriesList(models.Model):
    _name = 'door.accessories.list'
    
    name = fields.Char(
        string='Nombre'
    )
    price = fields.Float(
        string='Precio'
    )