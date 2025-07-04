from odoo import fields, models


class DoorHanding(models.Model):
    _name = 'door.handing'
    _inherit = 'door.abstract'
    _description = 'Door handing'