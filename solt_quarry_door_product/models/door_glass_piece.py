from odoo import models


class DoorGlassPiece(models.Model):
    _name = 'door.glass.piece'
    _inherit = 'door.abstract'
    _description = 'Door glass piece'