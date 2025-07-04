# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2021-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: odoo@cybrosys.com
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

import datetime
from datetime import datetime
from odoo import api, fields, models, _
from datetime import datetime, timedelta


class DeadLineReminder(models.Model):
    _inherit = "helpdesk.ticket"

    task_reminder = fields.Boolean("Reminder")

    @api.model
    def _cron_deadline_reminder(self):
        for task in self.env['helpdesk.ticket'].search(
                [('sla_deadline', '!=', None),
                 ('task_reminder', '=', True), ('user_id', '!=', None)]):
            reminder_date = task.sla_deadline
            yesterday = reminder_date - timedelta(days=2)
            print("==================================", yesterday)
            yesterday_str = yesterday.strftime("%Y-%m-%d")
            today_date = datetime.now().date()
            today_str = today_date.strftime("%Y-%m-%d")

            if yesterday_str == today_str and task:
                template_id = self.env['ir.model.data']._xmlid_lookup(
                    'ticket_deadline_reminder.email_template_edi_deadline_reminder')[2]
                if template_id:
                    print("---------------------------------------")
                    email_template_obj = self.env['mail.template'].browse(
                        template_id)
                    data = {'email_to': task.user_id.email}
                    values = email_template_obj.with_context(data).generate_email(task.id,
                       ['subject', 'body_html', 'email_from', 'email_to',
                        'partner_to', 'email_cc', 'reply_to','scheduled_date'])
                    msg_id = self.env['mail.mail'].create(values)
                    if msg_id:
                        msg_id._send()
        return True