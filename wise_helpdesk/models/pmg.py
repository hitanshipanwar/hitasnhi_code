from odoo import api, fields, models


class PMG(models.Model):
    _name = 'pmg'
    _description = 'PMG'

    name = fields.Char(string='Name')
    company_id = fields.Many2one("res.company", string="Company")
    old_id = fields.Char(string="Old ID")
