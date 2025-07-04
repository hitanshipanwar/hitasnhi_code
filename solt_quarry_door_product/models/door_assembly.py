from odoo import api, fields, models


class DoorAssembly(models.Model):
    _name = 'door.assembly'
    _inherit = 'door.abstract'
    _description = 'Door assembly'