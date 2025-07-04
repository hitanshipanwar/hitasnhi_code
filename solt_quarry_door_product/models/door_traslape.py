from odoo import fields, models


class DoorTraslapeInt(models.Model):
    _name = 'door.traslape'
    _inherit = 'door.abstract'
    _description = 'Door overlap'

    type = fields.Selection([('internal', 'Internal'), ('external', 'External')], 'Type', default='internal')

