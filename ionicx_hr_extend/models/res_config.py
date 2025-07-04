# -*- coding: utf-8 -*-

from odoo import models, fields, api

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    past_timesheet = fields.Boolean(string="Can not Update Past Timesheet")

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        params = self.env['ir.config_parameter'].sudo()
        past_timesheet = params.get_param('past_timesheet',
                                                 default=False)
        res.update(past_timesheet=past_timesheet)
        return res

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        self.env['ir.config_parameter'].sudo().set_param(
            "past_timesheet",
            self.past_timesheet)
