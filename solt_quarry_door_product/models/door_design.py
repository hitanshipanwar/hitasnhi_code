from odoo import models


class DoorDesign(models.Model):
    _name = 'door.design'
    _inherit = 'door.abstract'
    _description = 'Door design'