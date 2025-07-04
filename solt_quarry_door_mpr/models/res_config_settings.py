# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    create_draft_mo = fields.Boolean(string='Create MO in draft', readonly=False, related='company_id.create_draft_mo')

    @api.model
    def set_values(self):
        self.env.company.write({
            'create_draft_mo': self.create_draft_mo or self.env.company.create_draft_mo,
        })
        super(ResConfigSettings, self).set_values()

