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
from odoo import api, fields, models,_
from datetime import datetime, timedelta
from odoo.exceptions import ValidationError, UserError, AccessError
import requests
import logging

_logger = logging.getLogger(__name__)

class OwnConfiguration(models.Model):
	_name = 'own.configuration'
	_inherit = ['mail.thread', 'mail.activity.mixin']
	_description = 'Own Configuration'
	_order = 'name'

	_sql_constraints = [
        ('subscription_code_unique', 'unique(subscription_code)', 'Subscription code must be unique!')
    ]


	name = fields.Char(string="Name")
	# email = fields.Char(string="E-Mail")
	# phone = fields.Char(string="Phone")
	platform = fields.Selection([
		('stripe', 'Stripe'),
		('authorize', 'Authorize.Net'),
	], string="Platform", default=None)
	subscription_code = fields.Char(string="Subscription Code", required=True)
	state = fields.Selection([
		('active', 'Active'),
		('expired', 'Expired'),
		('draft', 'Draft'),
	], string="Status", default='draft')
	company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.company, related=False, readonly=True)
	last_update_on = fields.Datetime(string="Last Update On")
	last_update_by = fields.Many2one('res.users', string="Last Update By")


	@api.model_create_multi
	def create(self, vals):
		"""Update last update details on record creation."""
		for val in vals:
			val['last_update_on'] = fields.Datetime.now()
			val['last_update_by'] = self.env.user.id
		return super(OwnConfiguration, self).create(vals)

	def write(self, vals):
		"""Update last update details when record is modified."""
		vals['last_update_on'] = fields.Datetime.now()
		vals['last_update_by'] = self.env.user.id
		return super(OwnConfiguration, self).write(vals)

	def action_connect_service(self):
		for rec in self:
			url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
			host_url = self.env['ir.config_parameter'].sudo().get_param('client_subscription.host_db_url')
			_logger.info("Host URL: %s" % host_url)
			# Prepare the data to send to DB2
			if self.platform == 'stripe':
				stripe_id = self.env['stripe.bank.statement.config'].search([], limit=1)
				if stripe_id:
					data = {
						'name': self.env.cr.dbname,
						# 'email': self.email,
						'url': url,
						'subscription_code': self.subscription_code,
						'platform': self.platform,
						# 'phone': self.phone,
						'db_name': self.env.cr.dbname,
						'db_uid': self.env.uid,
						'db_user': self.env.user.name,
						'stripe_publish_key': stripe_id.stripe_publish_key,
						'stripe_secret_key': stripe_id.stripe_secret_key,
						'stripe_webhook_secret': stripe_id.stripe_webhook_secret,
					}
					stripe_id.statement_state = 'connected'
				else:
					raise ValidationError(_("Please configure your Stripe credentials in Accounting -> Configuration -> Stripe Configuration."))
			elif self.platform == 'authorize':
				authorize_id = self.env['authorize.bank.statement.config'].search([], limit=1)
				if authorize_id:
					data = {
						'name': self.env.cr.dbname,
						# 'email': self.email,
						'url': url,
						'subscription_code': self.subscription_code,
						'platform': self.platform,
						# 'phone': self.phone,
						'db_name': self.env.cr.dbname,
						'db_uid': self.env.uid,
						'db_user': self.env.user.name,
						'authorize_login': authorize_id.authorize_login,
						'authorize_transaction_key': authorize_id.authorize_transaction_key,
						'authorize_signature_key': authorize_id.authorize_signature_key,
						'authorize_client_key': authorize_id.authorize_client_key,
					}
					authorize_id.statement_state = 'connected'
				else:
					raise ValidationError(_("Please configure your Authorize.Net credentials in Accounting -> Configuration -> Authorize.Net Configuration."))
			else:
				data = {
					'name': self.env.cr.dbname,
					# 'email': self.email,
					'url': url,
					'subscription_code': self.subscription_code,
					'platform': self.platform,
					# 'phone': self.phone,
					'db_name': self.env.cr.dbname,
					'db_uid': self.env.uid,
					'db_user': self.env.user.name,
				}

			try:
				response = requests.post(
					f"{host_url}/connect_db", 
					json=data,
					headers={'Content-Type': 'application/json'},
					verify=False
				)
				
				if response.status_code == 200:
					_logger.info("Response status code: %s" % response.status_code)
					_logger.info("Response text: %s" % response.text)
					
					result = response.json()
					_logger.info("Parsed response: %s" % result)

					if result.get('result') and result['result'].get('success') == True:
						self.state = 'active'
						return {
							'type': 'ir.actions.client',
							'tag': 'display_notification',
							'params': {
								'title': 'Success',
								'message': 'Connection successful.',
								'sticky': False,
							}
						}
					else:
						self.state = 'expired'
						error_message = result['result'].get('message')
						raise UserError(error_message)
				else:
					raise UserError(f"Failed to connect to DB2: {response.text}")
			
			except requests.exceptions.RequestException as e:
				raise UserError(f"Error connecting to DB2: {str(e)}")


	def action_disconnect_service(self):
		for rec in self:
			url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
			host_url = self.env['ir.config_parameter'].sudo().get_param('client_subscription.host_db_url')
			# Prepare the data to send to DB2
			if self.platform == 'stripe':
				stripe_id = self.env['stripe.bank.statement.config'].search([], limit=1)
				if stripe_id:
					data = {
						'name': self.env.cr.dbname,
						# 'email': self.email,
						'url': url,
						'subscription_code': self.subscription_code,
						'platform': self.platform,
						# 'phone': self.phone,
						'db_name': self.env.cr.dbname,
						'db_uid': self.env.uid,
						'db_user': self.env.user.name,
						'stripe_publish_key': stripe_id.stripe_publish_key,
						'stripe_secret_key': stripe_id.stripe_secret_key,
						'stripe_webhook_secret': stripe_id.stripe_webhook_secret,
					}
					stripe_id.statement_state = 'disconnected'
				else:
					raise ValidationError(_("Please configure your Stripe credentials in Accounting -> Configuration -> Stripe Configuration."))
			elif self.platform == 'authorize':
				authorize_id = self.env['authorize.bank.statement.config'].search([], limit=1)
				if authorize_id:
					data = {
						'name': self.env.cr.dbname,
						# 'email': self.email,
						'url': url,
						'subscription_code': self.subscription_code,
						'platform': self.platform,
						# 'phone': self.phone,
						'db_name': self.env.cr.dbname,
						'db_uid': self.env.uid,
						'db_user': self.env.user.name,
						'authorize_login': authorize_id.authorize_login,
						'authorize_transaction_key': authorize_id.authorize_transaction_key,
						'authorize_signature_key': authorize_id.authorize_signature_key,
						'authorize_client_key': authorize_id.authorize_client_key,
					}
					authorize_id.statement_state = 'disconnected'
				else:
					raise ValidationError(_("Please configure your Authorize.Net credentials in Accounting -> Configuration -> Authorize.Net Configuration."))
			else:
				data = {
					'name': self.env.cr.dbname,
					# 'email': self.email,
					'url': url,
					'subscription_code': self.subscription_code,
					'platform': self.platform,
					# 'phone': self.phone,
					'db_name': self.env.cr.dbname,
					'db_uid': self.env.uid,
					'db_user': self.env.user.name,
				}

			try:
				response = requests.post(
					f"{host_url}/disconnect_db", 
					json=data,
					headers={'Content-Type': 'application/json'},
					verify=False
				)
				
				if response.status_code == 200:
					_logger.info("Response status code: %s" % response.status_code)
					_logger.info("Response text: %s" % response.text)
					
					result = response.json()
					_logger.info("Parsed response: %s" % result)

					if result.get('result') and result['result'].get('success') == True:
						self.state = 'expired'
						return {
							'type': 'ir.actions.client',
							'tag': 'display_notification',
							'params': {
								'title': 'Warning',
								'type': 'danger',
								'message': 'Disconnected !',
								'sticky': False,
							}
						}
					else:
						self.state = 'active'
						error_message = result['result'].get('message')
						raise UserError(error_message)
				else:
					raise UserError(f"Failed to connect to DB2: {response.text}")
			
			except requests.exceptions.RequestException as e:
				raise UserError(f"Error connecting to DB2: {str(e)}")