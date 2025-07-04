from odoo import models


class DoorForge(models.Model):
    _name = 'door.forge'
    _inherit = 'door.abstract'
    _description = 'Door Forging'