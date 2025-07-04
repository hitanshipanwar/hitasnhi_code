# -*- coding: utf-8 -*-

from odoo import fields, models, api ,_


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    module_account_accountant = fields.Boolean(string='Account Accountant')
    module_l10n_fr_hr_payroll = fields.Boolean(string='French Payroll')
    module_l10n_be_hr_payroll = fields.Boolean(string='Belgium Payroll')
    module_l10n_in_hr_payroll = fields.Boolean(string='Indian Payroll')
    monthly_leave = fields.Integer(string='Monthly Leave',default=1)

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        config_parameter = self.env['ir.config_parameter'].sudo()
        monthly_leave = config_parameter.get_param('hr_payroll_community.monthly_leave')
        res.update(monthly_leave=int(monthly_leave))
        return res

    def set_values(self):
        res = super(ResConfigSettings, self).set_values()
        config_parameter = self.env['ir.config_parameter'].sudo()
        config_parameter.set_param("hr_payroll_community.monthly_leave", self.monthly_leave)
        return res