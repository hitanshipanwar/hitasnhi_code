# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    module_solt_quarry_door_specs_project = fields.Boolean(string='Card Request from Project')
    module_solt_quarry_door_specs_helpdesk = fields.Boolean(string='Card Request from Helpdesk')
    specs_sale_company_id = fields.Many2one('res.company', string="Company for Specs sale",
        readonly=False, related='company_id.specs_sale_company_id')
    specs_cost_company_id = fields.Many2one('res.company', string="Company for Specs cost",
                                            readonly=False, related='company_id.specs_cost_company_id')
    specs_deadbolt_categ_id = fields.Many2one('product.category', string="Deadbolt categ",
                                            readonly=False, related='company_id.specs_deadbolt_categ_id')

    @api.model
    def set_values(self):
        self.env.company.write({
            'specs_sale_company_id': self.specs_sale_company_id or self.env.company.specs_sale_company_id,
            'specs_cost_company_id': self.specs_cost_company_id or self.env.company.specs_cost_company_id,
            'specs_deadbolt_categ_id': self.specs_deadbolt_categ_id or self.env.company.specs_deadbolt_categ_id,
        })
        super(ResConfigSettings, self).set_values()

