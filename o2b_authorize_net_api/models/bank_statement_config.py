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
import requests
from datetime import datetime, timedelta
from odoo.exceptions import UserError, AccessDenied, ValidationError
import logging
import pprint
import json
from datetime import date, datetime, timedelta

from odoo.addons.payment_authorize import const
from odoo.addons.payment_authorize.models.authorize_request import AuthorizeAPI


_logger = logging.getLogger(__name__)

class BankStatement(models.Model):
	_name = 'authorize.bank.statement.config'
	_inherit = ['mail.thread', 'mail.activity.mixin']
	_description = 'Bank Statement Configuration'

	name = fields.Char(string="Name")
	provider = fields.Selection([('authorize', 'Authorize.Net')], string="Provider", default='authorize')
	# url = fields.Char(string="URL", help="URL of the second database where credentials are stored")
	# user_id = fields.Many2one('res.users', default=lambda self: self.env.uid, required=True)
	last_update = fields.Datetime(string="Last Update", readonly=True)
	next_update = fields.Datetime(string="Next Update", readonly=True)
	state = fields.Selection([
		('active', 'Active'),
		('expired', 'Expired'),
		('draft', 'Draft'),
	], string="Subscription Status", default='draft')
	statement_state = fields.Selection([
		('draft', 'Draft'),
		('connected', 'Connected'),
		('disconnected', 'Disconnected'),
	], string="Status", default='draft')
	journal_id = fields.Many2one(
		'account.journal',
		string='Payment Journal',
		required=True,
		store=True,
	)
	authorize_login = fields.Char(string="API Login ID")
	authorize_transaction_key = fields.Char(string="API Transaction Key")
	authorize_signature_key = fields.Char(string="API Signature Key")
	authorize_client_key = fields.Char(string="API Client Key")
	company_id = fields.Many2one('res.company', string='Company', required=True,
		default=lambda self: self.env.company)
	from_date = fields.Date(string="From Date")
	to_date = fields.Date(string="To Date")
	
	
	def authorize_action_connect_provider(self):
		# res = super(BankStatement, self).check_connection()
		""" Send credentials to DB2 for storing in ResClient. """

		if self.state == 'expired':
			raise UserError("Can not Establish Connection as your subscription expired.")

		if not self.provider:
			raise UserError("Please select a provider.")
		
		host_url = self.env['ir.config_parameter'].sudo().get_param('client_subscription.host_db_url')
		if not host_url:
			raise UserError("Please set the DB2 URL.")


		if self.provider == 'authorize':
			if not self.authorize_client_key:
				raise UserError("Please generate client key.")
				
			url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
			# Prepare the data to send to DB2
			data = {
				'name': self.env.cr.dbname,
				'provider': self.provider,
				'url': url,
				'authorize_login': self.authorize_login,
				'authorize_transaction_key': self.authorize_transaction_key,
				'authorize_signature_key': self.authorize_signature_key,
				'authorize_client_key': self.authorize_client_key,
				'db_name': self.env.cr.dbname,
				'db_uid': self.env.uid,
				'db_user': self.env.user.name,
				'is_connect': True
			}

			try:
				response = requests.post(
					f"{host_url}/provider_credentials", 
					json=data,
					headers={'Content-Type': 'application/json'},
					verify=False
				)
				
				if response.status_code == 200:
					_logger.info("Response status code: %s" % response.status_code)
					_logger.info("Response text: %s" % response.text)
					
					result = response.json()
					_logger.info("Parsed response: %s" % result)

					if result.get('result') and result['result'].get('status') == 'success':
						self.statement_state = 'connected'
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
						self.statement_state = 'disconnected'
						error_message = result['result'].get('message')
						raise UserError(error_message)
				else:
					raise UserError(f"Failed to connect to DB2: {response.text}")
			
			except requests.exceptions.RequestException as e:
				raise UserError(f"Error connecting to DB2: {str(e)}")

		return res

	def authorize_action_disconnect_provider(self):
		""" Send credentials to DB2 for storing in ResClient. """

		host_url = self.env['ir.config_parameter'].sudo().get_param('client_subscription.host_db_url')
		if not host_url:
			raise UserError("Please set the DB2 URL.")

		url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
		data = {
			'url': url,
			'provider': self.provider,
			'is_connect': False
			}
		try:
			response = requests.post(
				f"{host_url}/provider_credentials", 
				json=data,
				headers={'Content-Type': 'application/json'},
				verify=False
			)
			
			if response.status_code == 200:
				_logger.info("Response status code: %s" % response.status_code)
				_logger.info("Response text: %s" % response.text)
				
				result = response.json()
				_logger.info("Parsed response: %s" % result)

				if result.get('result') and result['result'].get('status') == 'success':
					self.statement_state = 'disconnected'
					return {
						'type': 'ir.actions.client',
						'tag': 'display_notification',
						'params': {
							'type': 'warning',
							'title': 'Success',
							'message': 'Disconnected successfully.',
							'sticky': False,
						}
					}
				else:
					self.statement_state = 'disconnected'
					error_message = result['result'].get('message')
					raise UserError(error_message)
			else:
				raise UserError(f"Failed to connect to DB2: {response.text}")
		
		except requests.exceptions.RequestException as e:
			raise UserError(f"Error connecting to DB2: {str(e)}")


	# @api.model
	# def fetch_authorize_client_key(self):
	# 	"""Fetch and store Authorize.Net client key."""
	# 	for record in self:
	# 		api_login_id = record.authorize_login
	# 		transaction_key = record.authorize_transaction_key

	# 		if not api_login_id or not transaction_key:
	# 			raise UserError("API Login ID and Transaction Key are required to fetch the client key.")

	# 		if len(transaction_key) > 16:
	# 			self.message_post(body="Transaction Key exceeds the maximum length of 16.")
	# 			self.env.cr.commit()
	# 			raise UserError(f"Transaction Key exceeds the maximum length of 16.")
			

	# 		# Set up API authentication
	# 		merchant_auth = apicontractsv1.merchantAuthenticationType()
	# 		merchant_auth.name = api_login_id
	# 		merchant_auth.transactionKey = transaction_key

	# 		# Request to fetch merchant details
	# 		request = apicontractsv1.getMerchantDetailsRequest()
	# 		request.merchantAuthentication = merchant_auth

	# 		# Controller to get merchant details
	# 		controller = getMerchantDetailsController(request)
	# 		controller.execute()

	# 		response = controller.getresponse()
	# 		_logger.info("Client Ket response %s" % response)

	# 		if response and hasattr(response, 'messages') and hasattr(response.messages, 'resultCode'):
	# 			if response.messages.resultCode == "Ok":
	# 				client_key = response.publicClientKey
	# 				self.authorize_client_key = client_key
	# 				return True
	# 			else:
	# 				# Log the full response to diagnose the issue
	# 				error_message = "Response Error: " + str(response)
	# 				print(error_message)  # Print the error for debugging
	# 				if hasattr(response.messages, 'message') and response.messages.message:
	# 					error_message = response.messages.message[0].text
	# 				else:
	# 					error_message = "Unknown error from Authorize.Net"
	# 				# Post error message to the chatter
	# 				self.message_post(body=f"Error fetching client key: {error_message}")
	# 				self.env.cr.commit()
	# 				raise UserError(f"Error fetching client key: {error_message}")
	# 		else:
	# 			# Handle malformed response
	# 			error_message = "Malformed Response: " + str(response)
	# 			print(error_message)  # Print the error for debugging
	# 			self.message_post(body="No valid response from Authorize.Net")
	# 			self.env.cr.commit()
	# 			raise UserError("No valid response from Authorize.Net")

	def _o2b_make_request(self, operation, data=None):
		request = {
			operation: {
				'merchantAuthentication': {
					'name': self.authorize_login,
					'transactionKey': self.authorize_transaction_key,
				},
				**(data or {})
			}
		}
		logged_request = {operation: data or {}}

		url = 'https://api.authorize.net/xml/v1/request.api'
		_logger.info("sending request to %s:\n%s", url, pprint.pformat(logged_request))
		response = requests.post(url, json.dumps(request), timeout=60)
		response.raise_for_status()
		response = json.loads(response.content)
		_logger.info("response received:\n%s", pprint.pformat(response))

		messages = response.get('messages')
		if messages and messages.get('resultCode') == 'Error':
			err_msg = messages.get('message')[0]['text']

			tx_errors = response.get('transactionResponse', {}).get('errors')
			if tx_errors:
				if err_msg:
					err_msg += '\n'
				err_msg += '\n'.join([e.get('errorText', '') for e in tx_errors])

			return {
				'err_code': messages.get('message')[0].get('code'),
				'err_msg': err_msg,
			}

		return response

	def o2b_merchant_details(self):
		""" Retrieves the merchant details and generate a new public client key if none exists.

		:return: Dictionary containing the merchant details
		:rtype: dict"""
		return self._o2b_make_request('getMerchantDetailsRequest')

	def o2b_test_authenticate(self):
		""" Test Authorize.net communication with a simple credentials check.

		:return: The authentication results
		:rtype: dict
		"""
		return self._o2b_make_request('authenticateTestRequest')


	def fetch_authorize_client_key(self):
		""" Fetch the merchant details to update the client key and the account currency. """
		# for record in self:
		# self.ensure_one()

		# if self.state == 'disabled':
		# 	raise UserError(_("This action cannot be performed while the provider is disabled."))

		api_login_id = self.authorize_login
		transaction_key = self.authorize_transaction_key

		if not api_login_id or not transaction_key:
			raise UserError("API Login ID and Transaction Key are required to fetch the client key.")

		if len(transaction_key) > 16:
			self.message_post(body="Transaction Key exceeds the maximum length of 16.")
			self.env.cr.commit()
			raise UserError(f"Transaction Key exceeds the maximum length of 16.")
		

		# authorize_API = AuthorizeAPI(self)

		# Validate the API Login ID and Transaction Key
		res_content = self.o2b_test_authenticate()
		_logger.info("o2b_test_authenticate request response:\n%s", pprint.pformat(res_content))
		if res_content.get('err_msg'):
			raise UserError(_("Failed to authenticate.\n%s", res_content['err_msg']))

		# Update the merchant details
		res_content = self.o2b_merchant_details()
		_logger.info("merchant_details request response:\n%s", pprint.pformat(res_content))
		if res_content.get('err_msg'):
			raise UserError(_("Could not fetch merchant details:\n%s", res_content['err_msg']))
		# currency = self.env['res.currency'].search([('name', 'in', res_content.get('currencies'))])
		# self.available_currency_ids = [Command.set(currency.ids)]
		self.authorize_client_key = res_content.get('publicClientKey')


	def action_generate_client_key(self):
		"""Button action to generate the Authorize.Net client key."""
		self.fetch_authorize_client_key()


	# def check_connection(self):
	# 	res = super(BankStatement, self).check_connection()
	# 	"""Check the connection with Authorize.Net using the provided credentials."""
	# 	for record in self:

	# 		if record.state == 'expired':
	# 			raise UserError("Can not Establish Connection as your subscription expired.")

	# 		if record.provider == 'authorize':
	# 			api_login_id = record.authorize_login
	# 			transaction_key = record.authorize_transaction_key
	# 			client_key = record.authorize_client_key

	# 			if not api_login_id or not transaction_key or not client_key:
	# 				raise UserError("API Login ID, Transaction Key, and Client Key are required.")

	# 			if len(transaction_key) > 16:
	# 				self.message_post(body="Transaction Key exceeds the maximum length of 16.")
	# 				self.env.cr.commit()
	# 				raise UserError(f"Transaction Key exceeds the maximum length of 16.")
				
	# 			# Set up API authentication
	# 			merchant_auth = apicontractsv1.merchantAuthenticationType()
	# 			merchant_auth.name = api_login_id
	# 			merchant_auth.transactionKey = transaction_key

	# 			# Request to fetch merchant details
	# 			request = apicontractsv1.getMerchantDetailsRequest()
	# 			request.merchantAuthentication = merchant_auth

	# 			# Controller to get merchant details
	# 			controller = getMerchantDetailsController(request)
	# 			controller.execute()

	# 			response = controller.getresponse()
	# 			# Check the response
	# 			if response and hasattr(response, 'messages') and hasattr(response.messages, 'resultCode'):
	# 				if response.messages.resultCode == "Ok":
	# 					# Connection is successful
	# 					self.message_post(body="Connection successful!")
	# 					self.env.cr.commit()
	# 					# raise ValidationError("Connection successful!")
	# 					return {
	# 						'type': 'ir.actions.client',
	# 						'tag': 'display_notification',
	# 						'params': {
	# 							'title': 'Success',
	# 							'message': 'Connection successful.',
	# 							'sticky': False,
	# 						}
	# 					}
	# 				else:
	# 					# Log the error
	# 					if hasattr(response.messages, 'message') and response.messages.message:
	# 						error_message = response.messages.message[0].text
	# 						self.message_post(body="Error: {}".format(error_message))
	# 						self.env.cr.commit()
	# 						raise UserError("Error: {}".format(error_message))
	# 					else:
	# 						error_message = "Unknown error from Authorize.Net"
	# 						self.message_post(body=error_message)
	# 						self.env.cr.commit()
	# 						raise UserError("Unknown error from Authorize.Net")
	# 					raise UserError(f"Error connecting to Authorize.Net: {error_message}")
	# 			else:
	# 				raise UserError("No valid response from Authorize.Net")
	# 	return res

	def authorize_check_connection(self):
		# res = super(BankStatement, self).check_connection()
		for record in self:

			if record.state == 'expired':
				raise UserError("Can not Test Connection as your subscription expired.")


			host_url = self.env['ir.config_parameter'].sudo().get_param('client_subscription.host_db_url')
			if not host_url:
				raise UserError("Please set the DB2 URL.")

			if record.provider == 'authorize':
				url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
				# Prepare the data to send to DB2
				data = {
					# 'name': self.name,
					'provider': self.provider,
					'url': url,
					'authorize_login': self.authorize_login,
					'authorize_transaction_key': self.authorize_transaction_key,
					'authorize_signature_key': self.authorize_signature_key,
					'authorize_client_key': self.authorize_client_key,
					# 'user_id': self.user_id.id,
					# 'login': self.user_id.login,
					# 'password': self.user_id.password,
					# 'partner_id': self.user_id.partner_id.id,
				}

				try:
					response = requests.post(
						f"{host_url}/test_authorize_connection", 
						json=data,
						headers={'Content-Type': 'application/json'},
						verify=False
					)
					print(">>>>>>>>>>>>>>>>>> response", response)
					if response.status_code == 200:
						result = response.json()
						print("Parsed response:", result)

						if result.get('result'):
							status = result['result'].get('status')
							message = result['result'].get('message', 'Unknown error')
							
							if status == 'success':
								self.statement_state = 'connected'
								return {
									'type': 'ir.actions.client',
									'tag': 'display_notification',
									'params': {
										'title': 'Success',
										'message': message,
										'type': 'success',
										'sticky': False,
									}
								}
							elif status == 'failed':
								self.statement_state = 'disconnected'
								return {
									'type': 'ir.actions.client',
									'tag': 'display_notification',
									'params': {
										'title': 'Danger',
										'message': message,
										'type': 'danger',
										'sticky': False,
									}
								}
						else:
							error_message = result.get('error', 'Unknown error')
							raise UserError(f"Test Connection Failed: {error_message}")
					else:
						raise UserError(f"Test Connection Failed with status {response.status_code}: {response.text}")

				except requests.exceptions.RequestException as e:
					raise UserError(f"Error connecting to DB2: {str(e)}")

	@api.model
	def authorize_fetch_and_update_state(self):
		"""Fetch subscription state from service_db and update."""
		# Retrieve subscription_id from system parameters
		bank_statement = self.env['authorize.bank.statement.config'].sudo().search([])
		subscription_ids = self.env['ir.config_parameter'].sudo().search([
			('key', 'like', 'subscription_id -%')
		])
		for subscription_id in subscription_ids:
			
			for rec in bank_statement:
				url = self.env['ir.config_parameter'].sudo().get_param('client_subscription.host_db_url')
				if not url:
					raise ValidationError("Service DB URL is not configured.")
				
				# Prepare the service_db API endpoint
				service_db_url = f"{url}/api/subscription/state"
				payload = {'subscription_id': subscription_id.value}
				
				try:
					# Make the API request
					response = requests.post(service_db_url, json=payload, verify=False)
					if response.status_code == 200:
						data = response.json()
						if 'result' in data:
							if rec.provider == data['result'].get('provider'):
								rec.write({'state': data['result'].get('state')})
						else:
							raise ValidationError(data.get('error', 'Unexpected response from service_db'))
					else:
						raise ValidationError(f"Error from service_db: {response.status_code} - {response.text}")
				except requests.RequestException as e:
					raise ValidationError(f"Connection error: {str(e)}")

	def get_transaction_list(self, from_date=None, to_date=None, from_cron=False):

		bank_statement = self.env['authorize.bank.statement.config'].sudo().search([])

		if self:
			bank_statement = self

		_logger.info("Fetching transaction list...")

		to_date = datetime.utcnow()
		from_date = to_date - timedelta(days=15)

		_logger.info("Final from_date object: %s (%s)", from_date, type(from_date))
		_logger.info("Final to_date object: %s (%s)", to_date, type(to_date))



		for payment_provider in bank_statement:
			if payment_provider.from_date or payment_provider.to_date:
				from_date = payment_provider.from_date or from_date
				to_date = payment_provider.to_date or to_date

			from_date_str = from_date.strftime("%Y-%m-%d")
			to_date_str = to_date.strftime("%Y-%m-%d")

			if (to_date - from_date).days > 31:
				    raise UserError("Error: The date range cannot exceed 31 days.")

			_logger.info("Fetching transaction from...: %s" % from_date_str)
			_logger.info("Fetching transaction to...:%s" % to_date_str)

			if payment_provider.statement_state == 'connected':

				if not payment_provider.authorize_login:
					_logger.info("\n\n Authorize.Net login is not configured.")
					return

				if not payment_provider.authorize_transaction_key:
					_logger.info("\n\n Authorize.Net Transaction Key is not configured.")
					return

				host_url = self.env['ir.config_parameter'].sudo().get_param('client_subscription.host_db_url')
				if not host_url:
					raise UserError("Please set the Host Database URL.")

				last_update = datetime.now()
				next_update = last_update + timedelta(days=1)

				if payment_provider:
					payment_provider.last_update = last_update
					payment_provider.next_update = next_update

				data = {
					'authorize_login': payment_provider.authorize_login,
					'authorize_transaction_key': payment_provider.authorize_transaction_key,
					'from_date': from_date_str,
					'to_date': to_date_str, 
				}

				try:
					response = requests.post(
						f"{host_url}/fetch_authorize_net_transactions",
						json=data,
						headers={'Content-Type': 'application/json'},
						verify=False
					)
					# _logger.info("Transaction Response %s" % response)
					if response.status_code == 200:
						result = response.json()
						# _logger.info("Transaction Result %s" % result)

						if isinstance(result['result'], bool) and result['result'] is True:
							_logger.info("No transactions or unexpected response received.")
							return {'status': 'success', 'transactions': []}
	
	
						if isinstance(result['result'], dict) and result['result'].get('status') == 'success':
						# if result['result'].get('status') == 'success':
							transactions = result['result'].get('transactions', [])
							_logger.info("Received %d transactions" % len(transactions))

							for transaction in transactions:
								transaction_status = transaction['transactionStatus']
								if transaction_status in ['settledSuccessfully', 'refundSettledSuccessfully']:
									_logger.info("transaction *****************%s", transaction)
									invoice = transaction['invoice']
									ref = transaction['ref']
									_logger.info("ref *****************%s", ref)
									submit_time_utc = transaction['submitTimeUTC']
									first_name = transaction['firstName']
									last_name = transaction['lastName']
									amount = transaction['amount']
									transaction_id = transaction['transId']

									journal = payment_provider.journal_id
									partner_name = f"{first_name} {last_name}"

									existing_line = self.env['account.bank.statement.line'].sudo().search([
										('authorize_transaction_identifier', '=', transaction_id)
									], limit=1)

									if not existing_line and float(amount) != 0:
										self.env['account.bank.statement.line'].sudo().create({
											'payment_ref': partner_name,
											'ref': ref,
											'date': submit_time_utc,
											'name': invoice,
											'amount': float(amount),
											'journal_id': journal.id,
											'company_id': payment_provider.company_id.id,
											'authorize_transaction_identifier': transaction_id
										})
										_logger.info("Authorize Transaction Created")
									elif not existing_line.is_reconciled and not existing_line.to_check and float(amount) != 0:
										existing_line.sudo().write({
											'payment_ref': partner_name,
											'ref': ref,
											'date': submit_time_utc,
											'name': invoice,
											'amount': float(amount),
											'journal_id': journal.id,
											'company_id': payment_provider.company_id.id,
											'authorize_transaction_identifier': transaction_id
										})
										_logger.info("Authorize Transaction Updated")
								else:
									_logger.info("Transaction Status Not Settled Successfully")
						else:
							_logger.info("Failed to fetch transactions: %s" % result.get('message'))

				except requests.exceptions.RequestException as e:
					_logger.info("Failed to get the transaction list from custom API: %s" % str(e))

			else:
				_logger.info('%s your Subscription Expired' % payment_provider.name)


class AccountBankStatementLineInherit(models.Model):
	_inherit = 'account.bank.statement.line'

	authorize_transaction_identifier = fields.Char("Authorize Transaction Identifier", readonly=True)
