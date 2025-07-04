from odoo import api, fields, models


class PCP(models.Model):
    _name = 'pcp'
    _description = 'PCP'

    name = fields.Char(string='Name')
    pcp_npi = fields.Char(string="PCP NPI")
    company_id = fields.Many2one("res.company", string="Company")
    old_id = fields.Char(string="Old ID")
    