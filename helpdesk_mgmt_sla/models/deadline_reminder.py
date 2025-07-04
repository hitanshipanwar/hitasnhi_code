# -*- coding: utf-8 -*-

import datetime
from datetime import datetime
from odoo import api, fields, models, _
from datetime import datetime, timedelta


class DeadLineReminder(models.Model):
    _inherit = "helpdesk.ticket"

    ticket_reminder = fields.Boolean("Reminder", default=True)

    @api.model
    def _cron_deadline_reminder(self):
        for ticket in self.env['helpdesk.ticket'].search(
                [('sla_deadline', '!=', None),
                 ('ticket_reminder', '=', True), ('user_id', '!=', None)]):
            reminder_date = ticket.sla_deadline
            yesterday = reminder_date - timedelta(days=2)
            yesterday_str = yesterday.strftime("%Y-%m-%d")
            today_date = datetime.now().date()
            today_str = today_date.strftime("%Y-%m-%d")

            if yesterday_str == today_str and ticket:
                template_id = self.env['ir.model.data']._xmlid_lookup(
                    'helpdesk_mgmt_sla.email_template_edi_deadline_reminder')[2]
                if template_id:
                    email_template_obj = self.env['mail.template'].browse(
                        template_id)
                    data = {'email_to': ticket.user_id.email}
                    values = email_template_obj.with_context(data).generate_email(ticket.id,
                       ['subject', 'body_html', 'email_from', 'email_to',
                        'partner_to', 'email_cc', 'reply_to','scheduled_date'])
                    msg_id = self.env['mail.mail'].create(values)
                    if msg_id:
                        msg_id._send()
        return True