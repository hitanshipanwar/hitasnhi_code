from odoo import models


class DoorPosition(models.Model):
    _name = 'door.position'
    _inherit = 'door.abstract'
    _description = 'Door fixed position'