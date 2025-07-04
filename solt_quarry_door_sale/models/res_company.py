# -*- coding: utf-8 -*-

from odoo import api, exceptions, fields, models, _


class ResCompany(models.Model):
    _inherit = 'res.company'

    specs_sale_company_id = fields.Many2one('res.company', string="Company for Specs sale",
        readonly=False)
    specs_cost_company_id = fields.Many2one('res.company', string="Company for Specs cost",
                                            readonly=False)
    specs_deadbolt_categ_id = fields.Many2one('product.category', string="Deadbolt categ")