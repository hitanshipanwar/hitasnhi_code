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
from odoo import api, fields, models, _, exceptions, tools
from odoo.tools.misc import formatLang
from odoo.addons.base.models.res_users import check_identity
from datetime import datetime
from odoo.http import request
import re
from bs4 import BeautifulSoup

@api.model
def _lang_get(self):
	return self.env['res.lang'].get_installed()

class ResUsers(models.Model):
	_name = 'res.users'
	_inherit = ['res.users','mail.thread', 'mail.activity.mixin']

	user_offline = fields.Char(string="User Status", tracking=True)

	groups_id = fields.Many2many('res.groups', 'res_groups_users_rel', 'uid', 'gid', string='Groups', default=lambda s: s._default_groups(), tracking=False)
	
	partner_id = fields.Many2one('res.partner', required=True, ondelete='restrict', auto_join=True, index=True,
		string='Related Partner', help='Partner-related data of the user', tracking=True)
	login = fields.Char(required=True, help="Used to log into the system", tracking=True)
	password = fields.Char(
		compute='_compute_password', inverse='_set_password', copy=False,
		help="Keep empty if you don't want the user to be able to connect on the system.", tracking=True)
	new_password = fields.Char(string='Set Password',
		compute='_compute_password', inverse='_set_new_password',
		help="Specify a value only when creating a user or if you're "\
			 "changing the user's password, otherwise leave empty. After "\
			 "a change of password, the user has to login again.", tracking=True)
	signature = fields.Html(string="Email Signature", compute='_compute_signature', readonly=False, store=True)
	is_login_custom = fields.Boolean(string="Loging", tracking=True)
	active = fields.Boolean(default=True, tracking=True)
	active_partner = fields.Boolean(related='partner_id.active', readonly=True, string="Partner is Active", tracking=True)
	action_id = fields.Many2one('ir.actions.actions', string='Home Action',
		help="If specified, this action will be opened at log on for this user, in addition to the standard menu.", tracking=True)
	log_ids = fields.One2many('res.users.log', 'create_uid', string='User log entries')
	login_date = fields.Datetime(related='log_ids.create_date', string='Latest authentication', readonly=False, )
	share = fields.Boolean(compute='_compute_share', compute_sudo=True, string='Share User', store=True,
		 help="External user with limited access, created only for the purpose of sharing data.", tracking=True)
	companies_count = fields.Integer(compute='_compute_companies_count', string="Number of Companies", tracking=True)
	tz_offset = fields.Char(compute='_compute_tz_offset', string='Timezone offset')
	# res_users_settings_ids = fields.One2many('res.users.settings', 'user_id')
	# Provide a target for relateds that is not a x2Many field.
	res_users_settings_id = fields.Many2one('res.users.settings', string="Settings", compute='_compute_res_users_settings_id', search='_search_res_users_settings_id', tracking=True)

	# Special behavior for this field: res.company.search() will only return the companies
	# available to the current user (should be the user's companies?), when the user_preference
	# context is set.
	company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.company.id,
		help='The default company for this user.',tracking=True, context={'user_preference': True})
	company_ids = fields.Many2many('res.company', 'res_company_users_rel', 'user_id', 'cid',
		string='Companies', default=lambda self: self.env.company.ids)

	# overridden inherited fields to bypass access rights, in case you have
	# access to the user but not its corresponding partner
	name = fields.Char(related='partner_id.name', inherited=True, readonly=False, tracking=True)
	email = fields.Char(related='partner_id.email', inherited=True, readonly=False, tracking=False)

	accesses_count = fields.Integer('# Access Rights', help='Number of access rights that apply to the current user',
									compute='_compute_accesses_count', compute_sudo=True)
	rules_count = fields.Integer('# Record Rules', help='Number of record rules that apply to the current user',
								 compute='_compute_accesses_count', compute_sudo=True)
	groups_count = fields.Integer('# Groups', help='Number of groups that apply to the current user',
								  compute='_compute_accesses_count', compute_sudo=True)

	lang = fields.Selection(_lang_get, string='Language',
							help="All the emails and documents sent to this contact will be translated in this language.", tracking=True)

	odoobot_state = fields.Selection(selection_add=[
	   ('onboarding_canned', 'Onboarding canned'),
	],tracking=True, ondelete={'onboarding_canned': lambda users: users.write({'odoobot_state': 'disabled'})})


	notification_type = fields.Selection([
	   ('email', 'Handle by Emails'),
	   ('inbox', 'Handle in Odoo')],
	   'Notification',tracking=True, required=True, default='email',
	   compute='_compute_notification_type', inverse='_inverse_notification_type', store=True,
	   help="Policy on how to handle Chatter notifications:\n"
		   "- Handle by Emails: notifications are sent to your email address\n"
		   "- Handle in Odoo: notifications appear in your Odoo Inbox")


	oauth_provider_id = fields.Many2one('auth.oauth.provider', string='OAuth Provider', tracking=True)
	oauth_uid = fields.Char(string='OAuth User ID', help="Oauth Provider user_id", copy=False, tracking=True)
	oauth_access_token = fields.Char(string='OAuth Access Token', readonly=True, copy=False, tracking=True)

	state = fields.Selection(compute='_compute_state', search='_search_state', string='Status',
				 selection=[('new', 'Never Connected'), ('active', 'Confirmed')], tracking=True)

	# totp_secret = fields.Char(copy=False, groups=fields.NO_ACCESS, compute='_compute_totp_secret', inverse='_inverse_token', tracking=True)
	# totp_enabled = fields.Boolean(string="Two-factor authentication", compute='_compute_totp_enabled', search='_totp_enable_search', tracking=True)
	# totp_trusted_device_ids = fields.One2many('auth_totp.device', 'user_id', string="Trusted Devices", tracking=True)


	def action_reset_password(self):
		res = super(ResUsers, self).action_reset_password()
		self.message_post(body="%s requested %s to reset password. "% (self.env.user.name, self.name))

		return res

	@check_identity
	def action_totp_disable(self):
		res = super(ResUsers, self).action_totp_disable()
		self.message_post(body="%s disable two-factor authentication."% (self.env.user.name))

		return res

	def action_open_my_account_settings(self):
		res = super(ResUsers, self).action_open_my_account_settings()
		self.message_post(body="%s open two-factor authentication configuration."% (self.env.user.name))

		return res

	def action_totp_invite(self):
		res = super(ResUsers, self).action_totp_invite()
		self.message_post(body="%s send link to invite for two-factor authentication."% (self.env.user.name))

		return res

	def copy(self, default=None):
		res = super(ResUsers, self).copy()
		self.message_post(body="The %s duplicated this record and created a new one as %s."% (self.env.user.name, res.name))
		res.message_post(body="This record is a copy of %s and was duplicated by the %s"% (self.name, self.env.user.name))

		return res


	@classmethod
	def _login(cls, db, login, password, user_agent_env):
		res = super(ResUsers, cls)._login(db, login, password, user_agent_env)
		user_id = request.env["res.users"].sudo().search([("login", "=", login)]) if login else request.env["res.users"]
		if user_id:
			user_id.with_user(user_id.id).sudo().write({
						   'is_login_custom':True})
		return res

	def write(self, vals):
		if 'signature' in vals:
			soup = BeautifulSoup(self.signature, 'html.parser')
			old_sign = soup.get_text().strip()

		if 'tz' in vals and vals.get('tz'):
			self.message_post(body="%s changed Timezone from %s to %s." % (self.env.user.name, self.tz, vals.get('tz')))

		old_ids = self.groups_id.ids
		res = super(ResUsers, self).write(vals)
		new_ids = self.groups_id.ids
		added_elements = [x for x in old_ids if x not in new_ids]
		removed_elements = [x for x in new_ids if x not in old_ids]

		group_ids = added_elements + removed_elements
		groups = self.env['res.groups'].browse(group_ids)
		group_names = groups.mapped('name')
		category_names = groups.mapped('category_id.name')
		category_id = groups.mapped('category_id.id')
		
		grp_id = []
		same_group_id = self.env['res.groups'].search([('category_id', 'in', category_id)])
		grp_id = grp_id.append(same_group_id)
		if group_names and category_names:
			if 'Receive notifications in Odoo' not in group_names:
				for category_name in set(category_names):
					category_groups = groups.filtered(lambda g: g.category_id.name == category_name)
					changed_group_names = ", ".join(category_groups.mapped('name'))
					message = "Changed groups for category '%s': %s" % (category_name, changed_group_names)
					self.message_post(body=message)

		if 'signature' in vals:
			soup = BeautifulSoup(vals['signature'], 'html.parser')
			new_sign = soup.get_text().strip()
			# new_sign = re.findall(r'<p.*?>(.*?)</p>', html_string)[0] if re.findall(r'<p.*?>(.*?)</p>', html_string) else None
			self.message_post(body="%s changed signature from %s to %s."% (self.env.user.name, old_sign, new_sign))


		return res

class ChangePasswordWizardInherit(models.TransientModel):
	_inherit = "change.password.wizard"

	def change_password_button(self):
		res = super(ChangePasswordWizardInherit, self).change_password_button()
		current_user = self.env.user
		user_ids = self._context.get('active_model') == 'res.users' and self._context.get('active_ids') or []
		user = self.env['res.users'].browse(user_ids)
		if user_ids:
			user.message_post(body="%s changed password."% (current_user.name))

		return res

class ChangePasswordOwnInherit(models.TransientModel):
	_inherit = "change.password.own"

	@check_identity
	def change_password(self):
		res = super(ChangePasswordOwnInherit, self).change_password()
		current_user = self.env.user
		if current_user:
			current_user.message_post(body="%s changed password."% (current_user.name))
		return res

# class IrAttachment(models.Model):
# 	_inherit = 'ir.attachment'
#
# 	def _post_add_create(self, **kwargs):
# 		res = super(IrAttachment, self)._post_add_create()
# 		user = self.env['res.users'].search([('id', '=', self.res_id)])
# 		if user:
# 			user.message_post(body="%s Add New Attachment."% (self.env.user.name))
# 		return res
#
# 	def _delete_and_notify(self, message=None):
# 		user = self.env['res.users'].search([('id', '=', self.res_id)])
# 		if user:
# 			user.message_post(body="%s Delete Attachment."% (self.env.user.name))
# 		res = super(IrAttachment, self)._delete_and_notify()
# 		return res

# class ResPartner(models.Model):
# 	_inherit = 'res.partner'

# 	def action_privacy_lookup(self):
# 		res = super(ResPartner, self).action_privacy_lookup()
# 		current_user = self.env.user
# 		if current_user:
# 			current_user.message_post(body="%s changed privacy lookup."% (current_user.name))

# 		return res


# class IrActionsInherit(models.Model):
# 	_inherit = 'ir.actions.actions'

# 	@api.model
# 	@tools.ormcache('frozenset(self.env.user.groups_id.ids)', 'model_name')
# 	def get_bindings(self, model_name):
# 		result = super(IrActionsInherit, self).get_bindings(model_name)
# 		actions = result.get('action')
# 		if actions:
# 			for action in actions:
# 				if action.get('name') == 'Disable two-factor authentication':
# 					actions.remove(action)
# 					result.update({'action': actions})
# 		return result