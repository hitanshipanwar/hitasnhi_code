from odoo import models


class DoorSuffix(models.Model):
    _name = 'door.suffix'
    _inherit = 'door.abstract'
    _description = 'Door suffix'