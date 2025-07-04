from odoo import api, fields, models


class Holidays(models.Model):
    _inherit = "hr.leave"
    _description = "Time Off"

    is_payable = fields.Boolean('Is Payable')

