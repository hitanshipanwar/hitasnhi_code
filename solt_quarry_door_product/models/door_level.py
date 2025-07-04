from odoo import models


class DoorLevel(models.Model):
    _name = 'door.level'
    _inherit = 'door.abstract'
    _description = 'Door level'
