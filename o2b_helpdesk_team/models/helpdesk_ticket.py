# -*- coding: utf-8 -*-
##########################################################################
# Author      : O2b Technologies Pvt. Ltd.(<www.o2btechnologies.com>)
# Copyright(c): 2016-Present O2b Technologies Pvt. Ltd.
# All Rights Reserved.
#
# This program is copyright property of the author mentioned above.
# You can`t redistribute it and/or modify it.
#
##########################################################################
import math
import ast
import base64
import re
from dateutil.relativedelta import relativedelta
from random import randint

from odoo import api, Command, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import AccessError
from odoo.osv import expression
from odoo.addons.iap.tools import iap_tools
from odoo.addons.web.controllers.utils import clean_action
from odoo.exceptions import UserError
from odoo.tools import email_re

from datetime import date, datetime, timedelta
from passlib.utils.binary import ab64_decode
from odoo.exceptions import UserError, AccessDenied
from odoo.addons.auth_signup.models.res_partner import SignupError, now
import logging

_logger = logging.getLogger(__name__)

class HelpdeskTeam(models.Model):
    _inherit = "helpdesk.team"

    member_ids = fields.Many2many('res.users', string='Team Members', domain=lambda self: self._default_domain_member_ids(),
        default=lambda self: self.env.user, required=False)

    def write(self, vals):
        old_member_ids = False
        added_member = []
        deleted_member = []

        old_message_followers_ids = False
        added_message_followers = []
        deleted_message_followers = []
        if 'member_ids' in vals:
            old_member_ids = self.member_ids
            old_message_followers_ids = self.message_partner_ids
            user_ids = vals.get('member_ids')[0][2]
            team_id = self.id
            Users = self.env['res.users']
        elif 'message_partner_ids' in vals:
            old_message_followers_ids = self.message_partner_ids
            old_member_ids = self.member_ids
        active_model = False

        if 'active_model' in self._context:
            active_model = self._context.get('active_model', 'helpdesk.team')

        res = super(HelpdeskTeam, self).write(vals)

        for rec in self:
            if ('message_partner_ids' in vals or 'member_ids' in vals) and active_model != 'res.users':
                if not old_member_ids and 'message_partner_ids' not in vals:
                    added_member.append("<b>Team member updated</b><br/>" +  " <b>None</b> " + "<b>⟶</b>" + ", ".join([member.name for member in rec.member_ids]))
                    rec._message_log(body=added_member[0])
                    added_message_member_new = "<b>Team member added</b><br/>" +  " " + ", ".join([member.name for member in rec.member_ids])
                    rec._message_log(body=added_message_member_new)
                    if len(rec.member_ids) > len(old_member_ids) and old_member_ids:
                        added_message_followers.append("<b>Followers updated</b><br/>" +  " " + ", ".join([old_member.name for old_member in old_member_ids]) + "<b>⟶</b>" + ", ".join([member.name for member in rec.member_ids]))
                        rec._message_log(body=added_message_followers[0])
                        rem_val = rec.member_ids - old_member_ids
                        if rem_val:
                            added_message_followers_new = "<b>Follower added</b><br/>" +  " " + ", ".join([member.name for member in rem_val])
                            rec._message_log(body=added_message_followers_new)
                    elif len(rec.member_ids) > len(old_member_ids) and not old_member_ids:
                        added_message_followers.append("<b>Followers updated</b><br/>" +  " " + ", ".join([old_member.name for old_member in old_member_ids]) +  " <b>None</b> " + "<b>⟶</b>" + ", ".join([member.name for member in rec.member_ids]))
                        rec._message_log(body=added_message_followers[0])
                        added_message_followers_new = "<b>Follower added</b><br/>" +  " " + ", ".join([member.name for member in rec.member_ids])
                        rec._message_log(body=added_message_followers_new)
                elif len(rec.member_ids) > len(old_member_ids):
                    added_member.append("<b>Team member updated</b><br/>" +  " " + ", ".join([old_member.name for old_member in old_member_ids]) + "<b>⟶</b>" + ", ".join([member.name for member in rec.member_ids]))
                    rec._message_log(body=added_member[0])
                    rem_val_team = rec.member_ids - old_member_ids
                    if rem_val_team:
                        added_message_member_new = "<b>Team member added</b><br/>" +  " " + ", ".join([member.name for member in rem_val_team])
                        rec._message_log(body=added_message_member_new)
                    added_message_followers.append("<b>Followers updated</b><br/>" +  " " + ", ".join([old_member.name for old_member in old_member_ids]) + "<b>⟶</b>" + ", ".join([member.name for member in rec.member_ids]))
                    rec._message_log(body=added_message_followers[0])
                    rem_val = rec.member_ids - old_member_ids
                    if rem_val:
                        added_message_followers_new = "<b>Follower added</b><br/>" +  " " + ", ".join([member.name for member in rem_val])
                        rec._message_log(body=added_message_followers_new)
                elif rec.member_ids and old_member_ids and (len(rec.member_ids) < len(old_member_ids)):
                    deleted_member.append("<b>Team member updated</b><br/>" +  " " + ", ".join([old_member.name for old_member in old_member_ids]) + "<b>⟶</b>" + ", ".join([member.name for member in rec.member_ids]))
                    rec._message_log(body=deleted_member[0])
                    rem_val = old_member_ids - rec.member_ids
                    if rem_val:
                        deleted_message_member_new = "<b>Team member removed</b><br/>" +  " " + ", ".join([member.name for member in rem_val])
                        rec._message_log(body=deleted_message_member_new)
                    # deleted_message_followers.append("<b>updated</b><br/>" +  " " + ", ".join([old_member.name for old_member in old_member_ids]) + "<b>⟶</b>" + ", ".join([member.name for member in rec.member_ids]))
                    # rec._message_log(body=deleted_message_followers[0])
                elif rec.member_ids and old_member_ids and rec.member_ids != old_member_ids and (len(rec.member_ids) == len(old_member_ids)):
                    added_team_member = rec.member_ids.filtered(lambda member: member not in old_member_ids)
                    deleted_team_member = old_member_ids.filtered(lambda member: member not in rec.member_ids)

                    deleted_member.append("<b>Team member updated</b><br/>" +  " " + ", ".join([old_member.name for old_member in old_member_ids]) + "<b>⟶</b>" + ", ".join([member.name for member in rec.member_ids]))
                    rec._message_log(body=deleted_member[0])
                    deleted_message_member_new = "<b>Team member removed</b><br/>" +  " " + ", ".join([member.name for member in deleted_team_member])
                    rec._message_log(body=deleted_message_member_new)
                    added_message_member_new = "<b>Team member added</b><br/>" +  " " + ", ".join([member.name for member in added_team_member])
                    rec._message_log(body=added_message_member_new)

                    added_message_followers.append("<b>Followers updated</b><br/>" +  " " + ", ".join([old_member.name for old_member in old_member_ids]) + "<b>⟶</b>" + ", ".join([member.name for member in rec.member_ids]))
                    rec._message_log(body=added_message_followers[0])
                    deleted_message_followers_new = "<b>Followers removed</b><br/>" +  " " + ", ".join([member.name for member in deleted_team_member])
                    rec._message_log(body=deleted_message_followers_new)
                    added_message_followers_new = "<b>Follower added</b><br/>" +  " " + ", ".join([member.name for member in added_team_member])
                    rec._message_log(body=added_message_followers_new)

                elif not rec.member_ids and old_member_ids:
                    deleted_member.append("<b>Team member updated</b><br/>" +  " " + ", ".join([old_member.name for old_member in old_member_ids]) + "<b>⟶</b>" + "<b>None</b>")
                    rec._message_log(body=deleted_member[0])
                    deleted_message_member_new = "<b>Team member removed</b><br/>" +  " " + ", ".join([member.name for member in old_member_ids])
                    rec._message_log(body=deleted_message_member_new)
                # elif len(rec.message_partner_ids) > len(old_message_followers_ids):
                #     added_message_followers.append("<b>Followers updated</b><br/>" +  " " + ", ".join([old_follower.name for old_follower in old_message_followers_ids]) + "<b>⟶</b>" + ", ".join([member.name for member in self.message_partner_ids]))
                #     rec._message_log(body=added_message_followers[0])
                # elif len(rec.message_partner_ids) > len(old_message_followers_ids) and rec.message_partner_ids and old_message_followers_ids:
                #     added_message_followers.append("<b>Followers updated</b><br/>" +  " " + ", ".join([old_follower.name for old_follower in old_message_followers_ids]) + "<b>⟶</b>" + ", ".join([member.name for member in rec.message_partner_ids]))
                #     rec._message_log(body=added_message_followers[0])
                elif 'member_ids' not in vals and rec.message_partner_ids and old_message_followers_ids and (len(rec.message_partner_ids) < len(old_message_followers_ids)):
                    deleted_message_followers.append("<b>Followers updated</b><br/>" +  " " + ", ".join([old_follower.name for old_follower in old_message_followers_ids]) + "<b>⟶</b>" + ", ".join([member.name for member in rec.message_partner_ids]))
                    rec._message_log(body=deleted_message_followers[0])
                    rem_val = old_message_followers_ids - rec.message_partner_ids
                    if rem_val:
                        deleted_message_followers_new = "<b>Followers removed</b><br/>" +  " " + ", ".join([member.name for member in rem_val])
                        rec._message_log(body=deleted_message_followers_new)
                elif not rec.message_partner_ids and old_message_followers_ids:
                    deleted_message_followers.append("<b>Followers updated</b><br/>" +  " " + ", ".join([old_follower.name for old_follower in old_message_followers_ids]) + "<b>⟶</b>" + "<b>None</b>")
                    rec._message_log(body=deleted_message_followers[0])
                    deleted_message_followers_new = "<b>Followers removed</b><br/>" +  " " + ", ".join([member.name for member in old_message_followers_ids])
                    rec._message_log(body=deleted_message_followers_new)
            elif 'message_partner_ids' in vals and 'member_ids' not in vals and active_model == 'res.users':
                if not old_message_followers_ids and rec.message_partner_ids:
                    added_message_followers.append("<b>Followers updated</b><br/>" +  " <b>None</b> " + "<b>⟶</b>" + ", ".join([follower.name for follower in rec.message_partner_ids]))
                    rec._message_log(body=added_message_followers[0])
                    added_message_followers_new = "<b>Follower added</b><br/>" +  " " + ", ".join([member.name for member in rec.message_partner_ids])
                    rec._message_log(body=added_message_followers_new)
                    added_member.append("<b>Team member updated</b><br/>" +  " <b>None</b> " + "<b>⟶</b>" + ", ".join([follower.name for follower in rec.message_partner_ids]))
                    rec._message_log(body=added_member[0])
                    added_message_member_new = "<b>Team member added</b><br/>" +  " " + ", ".join([member.name for member in rec.message_partner_ids])
                    rec._message_log(body=added_message_member_new)
                elif len(rec.message_partner_ids) > len(old_message_followers_ids):
                    added_message_followers.append("<b>Followers updated</b><br/>" +  " " + ", ".join([old_follower.name for old_follower in old_message_followers_ids]) + "<b>⟶</b>" + ", ".join([member.name for member in rec.message_partner_ids]))
                    rec._message_log(body=added_message_followers[0])
                    rem_val = rec.message_partner_ids - old_message_followers_ids
                    if rem_val:
                        added_message_followers_new = "<b>Follower added</b><br/>" +  " " + ", ".join([member.name for member in rem_val])
                        rec._message_log(body=added_message_followers_new)
                    added_member.append("<b>Team member updated</b><br/>" +  " " + ", ".join([old_follower.name for old_follower in old_message_followers_ids]) + "<b>⟶</b>" + ", ".join([member.name for member in rec.message_partner_ids]))
                    rec._message_log(body=added_member[0])
                    if rem_val:
                        added_message_member_new = "<b>Team member added</b><br/>" +  " " + ", ".join([member.name for member in rem_val])
                        rec._message_log(body=added_message_member_new)
                # elif len(rec.message_partner_ids) == len(old_message_followers_ids) and (rec.message_partner_ids == old_message_followers_ids):
                #     added_message_followers.append("<b>Followers updated</b><br/>" +  " " + ", ".join([old_follower.name for old_follower in old_message_followers_ids]) + "<b>⟶</b>" + ", ".join([member.name for member in rec.message_partner_ids]))
                #     rec._message_log(body=added_message_followers[0])
                #     added_member.append("<b>Team member updated</b><br/>" +  " " + ", ".join([old_follower.name for old_follower in old_message_followers_ids]) + "<b>⟶</b>" + ", ".join([member.name for member in rec.message_partner_ids]))
                #     rec._message_log(body=added_member[0])
                elif rec.message_partner_ids and old_message_followers_ids and (len(rec.message_partner_ids) < len(old_message_followers_ids)):
                    deleted_message_followers.append("<b>Followers updated</b><br/>" +  " " + ", ".join([old_follower.name for old_follower in old_message_followers_ids]) + "<b>⟶</b>" + ", ".join([member.name for member in rec.message_partner_ids]))
                    rec._message_log(body=deleted_message_followers[0])
                    rem_val = old_message_followers_ids - rec.message_partner_ids
                    if rem_val:
                        deleted_message_followers_new = "<b>Followers removed</b><br/>" +  " " + ", ".join([member.name for member in rem_val])
                        rec._message_log(body=deleted_message_followers_new)
                    deleted_member.append("<b>Team member updated</b><br/>" +  " " + ", ".join([old_follower.name for old_follower in old_message_followers_ids]) + "<b>⟶</b>" + ", ".join([member.name for member in rec.message_partner_ids]))
                    rec._message_log(body=deleted_member[0])
                    if rem_val:
                        deleted_message_member_new = "<b>Team member removed</b><br/>" +  " " + ", ".join([member.name for member in rem_val])
                        rec._message_log(body=deleted_message_member_new)
                elif not rec.message_partner_ids and old_message_followers_ids:
                    deleted_message_followers.append("<b>Followers updated</b><br/>" +  " " + ", ".join([old_follower.name for old_follower in old_message_followers_ids]) + "<b>⟶</b>" + "<b>None</b>")
                    rec._message_log(body=deleted_message_followers[0])
                    deleted_message_followers_new = "<b>Followers removed</b><br/>" +  " " + ", ".join([member.name for member in old_message_followers_ids])
                    rec._message_log(body=deleted_message_followers_new)
                    deleted_member.append("<b>Team member updated</b><br/>" +  " " + ", ".join([old_follower.name for old_follower in old_message_followers_ids]) + "<b>⟶</b>" + "<b>None</b>")
                    rec._message_log(body=deleted_member[0])
                    deleted_message_member_new = "<b>Team member removed</b><br/>" +  " " + ", ".join([member.name for member in old_message_followers_ids])
                    rec._message_log(body=deleted_message_member_new)
        return res

class MailMessage(models.Model):
    _inherit = 'mail.message'

    allow_email = fields.Boolean('Allow Email')

class MailMail(models.Model):
    _inherit = 'mail.mail'

    allow_email = fields.Boolean('Allow Email')

    @api.model_create_multi
    def create(self, values_list):
        records = super(MailMail, self).create(values_list)
        for rec in records:
            if not rec.mail_message_id.allow_email and not rec.allow_email:
                rec.state = 'cancel'
                # rec.failure_type = 'mail_smtp'
            else:
                rec.allow_email = True
        return records

class MailComposer(models.Model):
    _inherit = 'mail.template'

    allow_email = fields.Boolean('Allow Email')

class MailComposer(models.TransientModel):
    _inherit = 'mail.compose.message'

    allow_email = fields.Boolean('Allow Email')

    def get_mail_values(self, res_ids):
        """Generate the values that will be used by send_mail to create mail_messages
        or mail_mails. """
        self.ensure_one()
        results = dict.fromkeys(res_ids, False)
        rendered_values = {}
        mass_mail_mode = self.composition_mode == 'mass_mail'

        # render all template-based value at once
        if mass_mail_mode and self.model:
            rendered_values = self.render_message(res_ids)
        # compute alias-based reply-to in batch
        reply_to_value = dict.fromkeys(res_ids, None)
        if mass_mail_mode and not self.reply_to_force_new:
            records = self.env[self.model].browse(res_ids)
            reply_to_value = records._notify_get_reply_to(default=False)
            # when having no specific reply-to, fetch rendered email_from value
            for res_id, reply_to in reply_to_value.items():
                if not reply_to:
                    reply_to_value[res_id] = rendered_values.get(res_id, {}).get('email_from', False)

        for res_id in res_ids:
            # static wizard (mail.message) values
            mail_values = {
                'subject': self.subject,
                'body': self.body or '',
                'parent_id': self.parent_id and self.parent_id.id,
                'partner_ids': [partner.id for partner in self.partner_ids],
                'attachment_ids': [attach.id for attach in self.attachment_ids],
                'author_id': self.author_id.id,
                'email_from': self.email_from,
                'record_name': self.record_name,
                'reply_to_force_new': self.reply_to_force_new,
                'mail_server_id': self.mail_server_id.id,
                'mail_activity_type_id': self.mail_activity_type_id.id,
                'message_type': 'email' if mass_mail_mode else self.message_type,
                'allow_email': self.template_id.allow_email
            }

            # mass mailing: rendering override wizard static values
            if mass_mail_mode and self.model:
                record = self.env[self.model].browse(res_id)
                mail_values['headers'] = repr(record._notify_by_email_get_headers())
                # keep a copy unless specifically requested, reset record name (avoid browsing records)
                mail_values.update(is_notification=not self.auto_delete_message, model=self.model, res_id=res_id, record_name=False)
                # auto deletion of mail_mail
                if self.auto_delete or self.template_id.auto_delete:
                    mail_values['auto_delete'] = True
                # rendered values using template
                email_dict = rendered_values[res_id]
                mail_values['partner_ids'] += email_dict.pop('partner_ids', [])
                mail_values.update(email_dict)
                if not self.reply_to_force_new:
                    mail_values.pop('reply_to')
                    if reply_to_value.get(res_id):
                        mail_values['reply_to'] = reply_to_value[res_id]
                if self.reply_to_force_new and not mail_values.get('reply_to'):
                    mail_values['reply_to'] = mail_values['email_from']
                # mail_mail values: body -> body_html, partner_ids -> recipient_ids
                mail_values['body_html'] = mail_values.get('body', '')
                mail_values['recipient_ids'] = [Command.link(id) for id in mail_values.pop('partner_ids', [])]

                # process attachments: should not be encoded before being processed by message_post / mail_mail create
                mail_values['attachments'] = [(name, base64.b64decode(enc_cont)) for name, enc_cont in email_dict.pop('attachments', list())]
                attachment_ids = []
                for attach_id in mail_values.pop('attachment_ids'):
                    new_attach_id = self.env['ir.attachment'].browse(attach_id).copy({'res_model': self._name, 'res_id': self.id})
                    attachment_ids.append(new_attach_id.id)
                attachment_ids.reverse()
                mail_values['attachment_ids'] = self.env['mail.thread'].with_context(attached_to=record)._message_post_process_attachments(
                    mail_values.pop('attachments', []),
                    attachment_ids,
                    {'model': 'mail.message', 'res_id': 0}
                )['attachment_ids']

            results[res_id] = mail_values

        results = self._process_state(results)
        return results

class ResUsers(models.Model):
    _inherit = 'res.users'


    helpdesk_team_ids = fields.Many2many('helpdesk.team',string="Helpdesk Team Member")


    '''
    (Overridden) from wise_password_14 by appending parameter allow_email, Send email only if allow_email is true.
    '''
    def action_reset_password(self):
        self.ensure_one()
        if not self.date_password_changed:
            _logger.info('Admin has not yet created a password for new user, not sending email')
            return

        """ create signup token for each user, and send their signup url by email """
        create_mode = bool(self.env.context.get('create_user'))
        template = None
        signup_type = None
        email_template = None
        if create_mode:
            signup_type = 'set'
            email_template = 'wise_password_14.set_password_email'
        else:
            signup_type = 'reset'
            email_template = 'auth_signup.reset_password_email'

        template = self.env.ref(email_template, raise_if_not_found=False)
        if not template:
            _logger.warn(_('The proper email template could not be found'))

        ''' no time limit for initial invitation, only for reset password '''
        expiration = False if create_mode else now(days=+1)
        odoo_bot = self.env.ref('base.user_root')

        self.mapped('partner_id').signup_prepare(signup_type=signup_type, expiration=expiration)

        email_values = {
            'email_cc': False,
            'auto_delete': True,
            'message_type': 'user_notification',
            'recipient_ids': [],
            'partner_ids': [],
            'scheduled_date': False,
            'email_from': odoo_bot.email,
            'allow_email': template.allow_email
        }
        assert template._name == 'mail.template'

        for user in self:
            if not user.email:
                raise UserError(_("Cannot send email: user %s has no email address.", user.name))
            email_values['email_to'] = user.email
            # TDE FIXME: make this template technical (qweb)
            with self.env.cr.savepoint():
                force_send = not(self.env.context.get('import_file', False))
                template.send_mail(user.id, force_send=force_send, raise_exception=True, email_values=email_values)
            _logger.info("Password reset email sent for user <%s> to <%s>", user.login, user.email)


class RazonDesafiliacionOption(models.Model):
    _name = 'razon.desafiliacion.option'
    _description = 'Razón Desafiliación Options'

    name = fields.Char("Name", required=True)
    active = fields.Boolean("Active", default=True)  # Optional, to archive options without deleting


class HelpdeskTicketsRazon(models.Model):
    _inherit = 'helpdesk.ticket'

    razon_desafiliacions = fields.Many2one(
        'razon.desafiliacion.option',
        string="Razón Desafiliación"
    )

    disenrollment_date = fields.Date('Disenrollment Date' , store=True)