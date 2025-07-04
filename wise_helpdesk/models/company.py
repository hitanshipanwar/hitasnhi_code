from odoo import api, fields, models


class Company(models.Model):
    _inherit = 'res.company'

    old_id = fields.Char(string="Old ID")
    