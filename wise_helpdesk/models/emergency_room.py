from odoo import api, fields, models


class EmergencyRoom(models.Model):
    _name = 'emergency.room'
    _description = 'Emergency Room'

    name = fields.Char(string='Name')
    