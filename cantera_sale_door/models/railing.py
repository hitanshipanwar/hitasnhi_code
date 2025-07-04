from odoo import _, api, fields, models

class Railing(models.Model):
    _name = 'railing'
    
    name = fields.Char(
        string='Nombre'
    )
    price = fields.Float(
        string='Precio'
    )