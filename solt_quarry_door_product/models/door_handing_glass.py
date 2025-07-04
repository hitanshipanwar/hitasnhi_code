from odoo import models


class DoorHandingGlass(models.Model):
    _name = 'door.handing.glass'
    _inherit = 'door.abstract'
    _description = 'Door handing glass'