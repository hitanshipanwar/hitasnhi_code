from odoo import models


class DoorRadius(models.Model):
    _name = 'door.radius'
    _inherit = 'door.abstract'
    _description = 'Door radius'
