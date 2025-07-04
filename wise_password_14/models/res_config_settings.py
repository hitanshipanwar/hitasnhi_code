from odoo import api, fields, models, _
from odoo.exceptions import UserError


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    pwd_min_len = fields.Integer(string='Minimum Length (Set to 0 to disable)',
        default=0, config_parameter='wise.pwd_min_len')
    pwd_num_days_till_reset = fields.Integer(string='The number of days a password will be valid for (Set to 0 to disable)',
        default=0, config_parameter='wise.pwd_num_days_till_reset')
    pwd_num_days_till_reminder = fields.Integer(string='The number of days before password expiration to remind the user to change their password (Set to 0 to disable)',
        default=0, config_parameter='wise.pwd_num_days_till_reminder')
    pwd_num_stored = fields.Integer(string='The number of new passwords that must be set until an old password can be reused (Set to 0 to disable)',
        default=0, config_parameter='wise.pwd_num_stored')
    pwd_include_num = fields.Boolean(string='Must include at least one number', 
        default=False, config_parameter="wise.pwd_include_num")
    pwd_include_upper = fields.Boolean(string='Must include at least one uppercase letter',
        default=False, config_parameter='wise.pwd_include_upper')
    pwd_include_lower = fields.Boolean(string='Must include at least one lowercase letter',
        default=False, config_parameter='wise.pwd_include_lower')
    pwd_include_special = fields.Boolean(string='Must include at least one special character',
        default=False, config_parameter='wise.pwd_include_special')

    @api.constrains('pwd_min_len')
    def _constrain_pwd_min_len(self):
        for rec in self:
            if rec.pwd_min_len < 0:
                raise UserError(_('Minimum Length must be greater than or equal to 0'))

    @api.constrains('pwd_num_days_till_reset')
    def _constrain_pwd_num_days_till_reset(self):
        for rec in self:
            if rec.pwd_num_days_till_reset < 0:
                raise UserError(_('The number of days a password will be valid for must be greater than or equal to 0'))
    
    @api.constrains('pwd_num_days_till_reminder')
    def _constrain_pwd_num_days_till_reminder(self):
        for rec in self:
            if rec.pwd_num_days_till_reminder < 0:
                raise UserError(_('The number of days before password expiration to remind the user to change their password must be greater than or equal to 0'))
            if rec.pwd_num_days_till_reminder > rec.pwd_num_days_till_reset:
                raise UserError(_('The number of days before password expiration to start reminding users to reset their password cannot be greater than the number of days a password is valid for'))

    @api.constrains('pwd_num_stored')
    def _constrain_pwd_num_stored(self):
        for rec in self:
            if rec.pwd_num_stored < 0:
                raise UserError(_('Password History must be greater than or equal to 0'))
    
