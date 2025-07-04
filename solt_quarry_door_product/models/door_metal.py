from odoo import models


class DoorMetal(models.Model):
    _name = 'door.metal'
    _inherit = 'door.abstract'
    _description = 'Door metal'