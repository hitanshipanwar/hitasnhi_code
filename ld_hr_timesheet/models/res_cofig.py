# -*- coding: utf-8 -*-

from odoo import api, fields, models


class TimesheetEmailConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    timesheet_reminder_subject = fields.Char(string='Subject')
    timesheet_reminder_body = fields.Html(string='Body')

    def set_values(self):
        super(TimesheetEmailConfigSettings, self).set_values()
        set_param = self.env['ir.config_parameter'].set_param
        set_param('timesheet_reminder_subject', self.timesheet_reminder_subject)
        set_param('timesheet_reminder_body', self.timesheet_reminder_body)


    @api.model
    def get_values(self):
        res = super(TimesheetEmailConfigSettings, self).get_values()
        get_param = self.env['ir.config_parameter'].sudo().get_param
        res.update(
            timesheet_reminder_subject=get_param('timesheet_reminder_subject', default=''),
            timesheet_reminder_body=get_param('timesheet_reminder_body', default=''),
        )
        return res

