from odoo import models


class DoorBoardType(models.Model):
    _name = 'door.board.type'
    _inherit = 'door.abstract'
    _description = 'Door board type'