##############################################################################
#
#    Bista Solutions
#    Copyright (C) 2019 (http://www.bistasolutions.com)
#
##############################################################################

from odoo import api, fields, models, _
# from .connection import BillComService
from odoo.exceptions import UserError, ValidationError
import json
import logging
import requests

_logger = logging.getLogger(__name__)
from datetime import datetime, timedelta


class BillComConfig(models.Model):
	_name = 'bill.com.config'
	_description = 'Bill.com Configuration'

	name = fields.Char('Name')
	bill_com_user_name = fields.Char("Username", copy=False)
	bill_com_password = fields.Char("Password", copy=False)
	bill_com_orgid = fields.Char("Organization ID", copy=False)
	bill_com_devkey = fields.Char("Developer Key", copy=False)
	bill_com_login_url = fields.Char("Login URL", copy=False)
	bill_com_vendor_create_url = fields.Char("Vendor Create URL", copy=False)
	bill_com_vendor_bulk_create_url = fields.Char("Vendor Bulk Create URL", copy=False)
	bill_com_vendor_update_url = fields.Char("Vendor Update URL", copy=False)
	bill_com_vendor_bank_account_create_url = fields.Char("Vendor Bank Account Create URL", copy=False)
	bill_com_vendor_bank_account_update_url = fields.Char("Vendor Bank Account Update URL", copy=False)
	bill_com_bill_create_url = fields.Char("Bill Create URL", copy=False)
	bill_com_bill_update_url = fields.Char("Bill Update URL", copy=False)
	bill_com_organization_bank_account_url = fields.Char("Organization Bank Accounts URL", copy=False)
	bill_com_payment_create_url = fields.Char("Payment Create URL:", copy=False)
	bill_com_environment = fields.Selection([('sandbox', 'Sandbox'), ('production', 'Production')],
											string="Environment", copy=False, default='sandbox')
	bill_com_mfa_challenge_create_url = fields.Char("MFA Challenge URL", copy=False)
	bill_com_mfa_challenge_authenticate_url = fields.Char("MFA Authenticate URL", copy=False)
	bill_com_mfa_challenge = fields.Char("MFA Challenge", copy=False)
	bill_com_device_name = fields.Char("Device Name", copy=False)
	bill_com_machine_name = fields.Char("Machine Name", copy=False)
	bill_com_mfa_token = fields.Char("MFA Token", copy=False)
	bill_com_mfa_id = fields.Char("MFA ID", copy=False)
	company_ids = fields.Many2many('res.company', 'bill_com_config_company_rel', 'bill_com_config_id', 'company_id',
								   string='Companies', copy=False)
	bill_com_payment_import_url = fields.Char("Payment Import URL", copy=False)
	bill_com_payment_cancel_url = fields.Char("Payment Cancel URL", copy=False)
	last_payment_imported_date = fields.Datetime('Payment Imported Date', copy=False)
	bill_com_vendor_import_url = fields.Char("Vendor Import URL", copy=False)
	bill_com_vendor_bank_account_import_url = fields.Char("Vendor Bank Accounts Import URL", copy=False)
	bill_com_bill_import_url = fields.Char("Bill Import URL", copy=False)
	default_payment_journal = fields.Many2one('account.journal', string='Default Payment Journal', copy=False,
											  help="If journal not found based on the Bank Account Configuration, this journal will be used in the Payments.")
	last_bill_imported_date = fields.Datetime('Bill Imported Date', copy=False)
	bill_com_bill_upload_attachment_url = fields.Char("Bill Upload Attachment URL", copy=False)
	bill_com_bill_status = fields.Selection(
		[('1', 'Unpaid'), ('2', 'Partially Paid'), ('4', 'Scheduled'), ('0', 'Paid'), ('all', 'All')],
		string="Payment Status", copy=False, default='all')
	bill_com_coa_import_url = fields.Char("Chart of Account Import URL", copy=False)
	bill_com_attachment_import_url = fields.Char("Attachment Import URL", copy=False)
	bill_com_payment_term_import_url = fields.Char("Payment Term URL", copy=False)
	bill_com_fund_transfer_report_url = fields.Char("Payment Batch Report URL", copy=False)
	import_from_date = fields.Date('From Date', copy=False)
	import_to_date = fields.Date('To Date', copy=False)
	bill_com_set_bill_approver_url = fields.Char("Bill Set Approver URL", copy=False)
	bill_com_users_import_url = fields.Char("Users Import URL", copy=False)
	# host_db_url = fields.Char("Host DB URL")
	state = fields.Selection([
		('active', 'Active'),
		('expired', 'Expired'),
	], string="Status")


	def establish_bill_com_connection(self):
		""" Establish credentials to Host DB. """
		if self.state == 'expired':
			raise ValidationError('Can not Establish Connection as your subscription expired.')
		else:
			if not self.bill_com_user_name:
				raise UserError("Please set Username.")

			if not self.bill_com_password:
				raise UserError("Please set Password.")

			if not self.bill_com_orgid:
				raise UserError("Please set Organization ID.")

			if not self.bill_com_devkey:
				raise UserError("Please set Developer Key.")
			
			# if not self.host_db_url:
			# 	raise UserError("Please set the DB2 URL.")

			client_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
			subscription_ids = self.env['ir.config_parameter'].sudo().search([
				('key', 'like', 'subscription_id -%')
			])
			subscription_value = []
			for subscription in subscription_ids:
				subscription_value.append(subscription.value)
			# Prepare the data to send to DB2
			_logger.info("subscription value: %s" % subscription_value)
			if self.bill_com_environment == 'sandbox':
				data = {
					'is_connect': True,
					'db_name': self.env.cr.dbname,
					'url': client_url,
					'subscription_ids': subscription_value,
					'name': self.name,
					'bill_com_user_name': self.bill_com_user_name,
					'bill_com_password': self.bill_com_password,
					'bill_com_orgid': self.bill_com_orgid,
					'bill_com_devkey': self.bill_com_devkey,
					'bill_com_login_url': self.bill_com_login_url,
					'bill_com_environment': self.bill_com_environment,
					'bill_com_vendor_create_url': self.bill_com_vendor_create_url,
					'bill_com_vendor_bulk_create_url': self.bill_com_vendor_bulk_create_url,
					'bill_com_vendor_update_url': self.bill_com_vendor_update_url,
					'bill_com_vendor_bank_account_create_url': self.bill_com_vendor_bank_account_create_url,
					'bill_com_vendor_bank_account_update_url': self.bill_com_vendor_bank_account_update_url,
					'bill_com_bill_create_url': self.bill_com_bill_create_url,
					'bill_com_bill_update_url': self.bill_com_bill_update_url,
					'bill_com_organization_bank_account_url': self.bill_com_organization_bank_account_url,
					'bill_com_payment_create_url': self.bill_com_payment_create_url,
					'bill_com_mfa_challenge_create_url': self.bill_com_mfa_challenge_create_url,
					'bill_com_mfa_challenge_authenticate_url': self.bill_com_mfa_challenge_authenticate_url,
					'bill_com_mfa_challenge': self.bill_com_mfa_challenge,
					'bill_com_device_name': self.bill_com_device_name,
					'bill_com_machine_name': self.bill_com_machine_name,
					'bill_com_mfa_token': self.bill_com_mfa_token,
					'bill_com_mfa_id': self.bill_com_mfa_id,
					'bill_com_payment_import_url': self.bill_com_payment_import_url,
					'bill_com_payment_cancel_url': self.bill_com_payment_cancel_url,
					'last_payment_imported_date': self.last_payment_imported_date.strftime('%Y-%m-%d') if self.last_payment_imported_date else False,
					'bill_com_vendor_import_url': self.bill_com_vendor_import_url,
					'bill_com_vendor_bank_account_import_url': self.bill_com_vendor_bank_account_import_url,
					'bill_com_bill_import_url': self.bill_com_bill_import_url,
					'last_bill_imported_date': self.last_bill_imported_date.strftime('%Y-%m-%d') if self.last_bill_imported_date else False,
					'bill_com_bill_upload_attachment_url': self.bill_com_bill_upload_attachment_url,
					'bill_com_coa_import_url': self.bill_com_coa_import_url,
					'bill_com_attachment_import_url': self.bill_com_attachment_import_url,
					'bill_com_payment_term_import_url': self.bill_com_payment_term_import_url,
					'bill_com_fund_transfer_report_url': self.bill_com_fund_transfer_report_url,
					'import_from_date': self.import_from_date.strftime('%Y-%m-%d') if self.import_from_date else False,
					'import_to_date': self.import_to_date.strftime('%Y-%m-%d') if self.import_to_date else False,
					'bill_com_set_bill_approver_url': self.bill_com_set_bill_approver_url,
					'bill_com_users_import_url': self.bill_com_users_import_url,
				}
			else:
				data = {
				'is_connect': True,
				'db_name': self.env.cr.dbname,
				'url': client_url,
				'name': self.name,
				'subscription_ids': subscription_value,
				'bill_com_user_name': self.bill_com_user_name,
				'bill_com_password': self.bill_com_password,
				'bill_com_orgid': self.bill_com_orgid,
				'bill_com_devkey': self.bill_com_devkey,
				'bill_com_login_url': self.bill_com_login_url,
				'bill_com_vendor_create_url': self.bill_com_vendor_create_url,
				'bill_com_vendor_bulk_create_url': self.bill_com_vendor_bulk_create_url,
				'bill_com_vendor_update_url': self.bill_com_vendor_update_url,
				'bill_com_vendor_bank_account_create_url': self.bill_com_vendor_bank_account_create_url,
				'bill_com_vendor_bank_account_update_url': self.bill_com_vendor_bank_account_update_url,
				'bill_com_bill_create_url': self.bill_com_bill_create_url,
				'bill_com_bill_update_url': self.bill_com_bill_update_url,
				'bill_com_organization_bank_account_url': self.bill_com_organization_bank_account_url,
				'bill_com_payment_create_url': self.bill_com_payment_create_url,
				'bill_com_mfa_challenge_create_url': self.bill_com_mfa_challenge_create_url,
				'bill_com_mfa_challenge_authenticate_url': self.bill_com_mfa_challenge_authenticate_url,
				'bill_com_mfa_challenge': self.bill_com_mfa_challenge,
				'bill_com_device_name': self.bill_com_device_name,
				'bill_com_machine_name': self.bill_com_machine_name,
				'bill_com_mfa_token': self.bill_com_mfa_token,
				'bill_com_mfa_id': self.bill_com_mfa_id,
				'bill_com_payment_import_url': self.bill_com_payment_import_url,
				'bill_com_payment_cancel_url': self.bill_com_payment_cancel_url,
				'last_payment_imported_date': self.last_payment_imported_date.strftime('%Y-%m-%d') if self.last_payment_imported_date else False,
				'bill_com_vendor_import_url': self.bill_com_vendor_import_url,
				'bill_com_vendor_bank_account_import_url': self.bill_com_vendor_bank_account_import_url,
				'bill_com_bill_import_url': self.bill_com_bill_import_url,
				'last_bill_imported_date': self.last_bill_imported_date.strftime('%Y-%m-%d') if self.last_bill_imported_date else False,
				'bill_com_bill_upload_attachment_url': self.bill_com_bill_upload_attachment_url,
				'bill_com_coa_import_url': self.bill_com_coa_import_url,
				'bill_com_attachment_import_url': self.bill_com_attachment_import_url,
				'bill_com_payment_term_import_url': self.bill_com_payment_term_import_url,
				'bill_com_fund_transfer_report_url': self.bill_com_fund_transfer_report_url,
				'import_from_date': self.import_from_date.strftime('%Y-%m-%d') if self.import_from_date else False,
				'import_to_date': self.import_to_date.strftime('%Y-%m-%d') if self.import_to_date else False,
				'bill_com_set_bill_approver_url': self.bill_com_set_bill_approver_url,
				'bill_com_users_import_url': self.bill_com_users_import_url,
			}
			url = self.env['ir.config_parameter'].sudo().get_param('client_subscription.host_db_url')
			if not url:
				raise UserError("Please Configure Sevice DB URL in General settings.")

			try:
				response = requests.post(
					f"{url}/bill_com_credentials", 
					json=data,
					headers={'Content-Type': 'application/json'},
					verify=False
				)
				_logger.info("Bill .com response: %s" % response)
				if response.status_code == 200:
					print("Response status code:", response.status_code)
					print("Response text:", response.text)
					
					result = response.json()
					_logger.info("Parsed response: %s" % result)

					if result.get('result') and result['result'].get('status') == 'success':
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
						# error_message = result.get('error', 'Unknown error')
						# raise UserError(f"Failed to set credentials on DB2: {error_message}")
						error_message = result['result'].get('message')
						raise UserError(error_message)
				else:
					raise UserError(f"Failed to connect to DB2: {response.text}")
			
			except requests.exceptions.RequestException as e:
				raise UserError(f"Error connecting to DB2: {str(e)}")

	def disconnect_bill_com_connection(self):
		""" Establish credentials to Host DB. """
		client_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
		subscription_ids = self.env['ir.config_parameter'].sudo().search([
			('key', 'like', 'subscription_id -%')
		])
		subscription_value = []
		for subscription in subscription_ids:
			subscription_value.append(subscription.value)
		# Prepare the data to send to DB2
		_logger.info("subscription value: %s" % subscription_value)
		data = {
			'name': self.name,
			'is_connect': False,
			'url': client_url,
		}
		url = self.env['ir.config_parameter'].sudo().get_param('client_subscription.host_db_url')
		if not url:
			raise UserError("Please Configure Sevice DB URL in General settings.")

		try:
			response = requests.post(
				f"{url}/bill_com_credentials", 
				json=data,
				headers={'Content-Type': 'application/json'},
				verify=False
			)
			_logger.info("Bill .com response: %s" % response)
			if response.status_code == 200:
				print("Response status code:", response.status_code)
				print("Response text:", response.text)
				
				result = response.json()
				_logger.info("Parsed response: %s" % result)

				if result.get('result') and result['result'].get('status') == 'success':
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
					# error_message = result.get('error', 'Unknown error')
					# raise UserError(f"Failed to set credentials on DB2: {error_message}")
					error_message = result['result'].get('message')
					raise UserError(error_message)
			else:
				raise UserError(f"Failed to connect to DB2: {response.text}")
		
		except requests.exceptions.RequestException as e:
			raise UserError(f"Error connecting to DB2: {str(e)}")


	def test_bill_com_connection(self):
		if self.state == 'expired':
			raise ValidationError('Can not Test Connection as your subscription expired.')
		else:
			client_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
			data = {
				'url': client_url,
				'name': self.name,
				'bill_com_user_name': self.bill_com_user_name,
				'bill_com_password': self.bill_com_password,
				'bill_com_orgid': self.bill_com_orgid,
				'bill_com_devkey': self.bill_com_devkey,
				'bill_com_environment': self.bill_com_environment,
				'bill_com_mfa_challenge': self.bill_com_mfa_challenge,
				'bill_com_mfa_id': self.bill_com_mfa_id,
				'bill_com_mfa_token': self.bill_com_mfa_token,
				'bill_com_device_name': self.bill_com_device_name,
				'bill_com_machine_name': self.bill_com_machine_name,
			}
			url = self.env['ir.config_parameter'].sudo().get_param('client_subscription.host_db_url')
			if not url:
				raise UserError("Please Configure Sevice DB URL in General settings.")

			try:
				response = requests.post(
					f"{url}/test_bill_com_connection",
					json=data,
					headers={'Content-Type': 'application/json'},
					verify=False
				)
				print("Response status code:", response.status_code)
				print("Response text:", response.text)
				if response.status_code == 200:
					result = response.json()
					print("Parsed response:", result)

					if result.get('result'):
						status = result['result'].get('status')
						message = result['result'].get('message', 'Unknown error')
						
						if status == 'success':
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


	def get_bill_com_config(self, company_id):
		bill_com_config_obj = False
		if company_id:
			bill_com_config_obj = self.search([('company_ids', '=', company_id)])
		return bill_com_config_obj

	@api.constrains('company_ids')
	def _check_company_id(self):
		bill_com_config_obj = self.env['bill.com.config']
		for each_config in self.sudo():
			company_ids = each_config.company_ids
			same_company_id_rec = bill_com_config_obj.sudo().search(
				[('id', '!=', each_config.id), ('company_ids', '=', company_ids.ids)])
			if same_company_id_rec:
				raise ValidationError(_('You cannot have multiple Bill.com Configuration for same company.'))

	@api.onchange('bill_com_environment')
	def onchange_bill_com_environment(self):
		bill_com_environment = self.bill_com_environment
		if bill_com_environment == 'sandbox':
			self.bill_com_login_url = 'https://api-stage.bill.com/api/v2/Login.json'
			self.bill_com_vendor_create_url = 'https://api-stage.bill.com/api/v2/Crud/Create/Vendor.json'
			self.bill_com_vendor_bulk_create_url = 'https://api-stage.bill.com/api/v2/Bulk/Crud/Create/Vendor'
			self.bill_com_vendor_update_url = 'https://api-stage.bill.com/api/v2/Crud/Update/Vendor.json'
			self.bill_com_vendor_bank_account_create_url = 'https://api-stage.bill.com/api/v2/Crud/Create/VendorBankAccount.json'
			self.bill_com_vendor_bank_account_update_url = 'https://api-stage.bill.com/api/v2/Crud/Delete/VendorBankAccount.json'
			self.bill_com_bill_create_url = 'https://api-stage.bill.com/api/v2/Bulk/Crud/Create/Bill'
			self.bill_com_bill_update_url = 'https://api-stage.bill.com/api/v2/Bulk/Crud/Update/Bill'
			self.bill_com_mfa_challenge_create_url = 'https://api-stage.bill.com/api/v2/MFAChallenge.json'
			self.bill_com_mfa_challenge_authenticate_url = 'https://api-stage.bill.com/api/v2/MFAAuthenticate.json'
			self.bill_com_organization_bank_account_url = 'https://api-stage.bill.com/api/v2/List/BankAccount.json'
			self.bill_com_payment_create_url = 'https://api-stage.bill.com/api/v2/PayBills.json'
			self.bill_com_payment_import_url = 'https://api-stage.bill.com/api/v2/List/SentPay.json'
			self.bill_com_payment_cancel_url = 'https://api-stage.bill.com/api/v2/CancelAPPayment.json'
			self.bill_com_vendor_import_url = 'https://api-stage.bill.com/api/v2/List/Vendor.json'
			self.bill_com_vendor_bank_account_import_url = 'https://api-stage.bill.com/api/v2/List/VendorBankAccount.json'
			self.bill_com_bill_import_url = 'https://api-stage.bill.com/api/v2/List/Bill.json'
			self.bill_com_bill_upload_attachment_url = 'https://api-stage.bill.com/api/v2/UploadAttachment.json'
			self.bill_com_coa_import_url = 'https://api-stage.bill.com/api/v2/List/ChartOfAccount.json'
			self.bill_com_attachment_import_url = 'https://api-stage.bill.com/api/v2/UploadAttachment.json'
			self.bill_com_fund_transfer_report_url = 'https://api-stage.bill.com/api/v2/List/MoneyMovement.json'
			self.bill_com_payment_term_import_url = 'https://api-stage.bill.com/api/v2/List/PaymentTerm.json'
			self.bill_com_set_bill_approver_url = 'https://api-stage.bill.com/api/v2/SetApprovers.json'
			self.bill_com_users_import_url = 'https://api-stage.bill.com/api/v2/List/User.json'
		else:
			self.bill_com_login_url = 'https://api.bill.com/api/v2/Login.json'
			self.bill_com_vendor_create_url = 'https://api.bill.com/api/v2/Crud/Create/Vendor.json'
			self.bill_com_vendor_bulk_create_url = 'https://api.bill.com/api/v2/Bulk/Crud/Create/Vendor'
			self.bill_com_vendor_update_url = 'https://api.bill.com/api/v2/Crud/Update/Vendor.json'
			self.bill_com_vendor_bank_account_create_url = 'https://api.bill.com/api/v2/Crud/Create/VendorBankAccount.json'
			self.bill_com_vendor_bank_account_update_url = 'https://api.bill.com/api/v2/Crud/Delete/VendorBankAccount.json'
			self.bill_com_bill_create_url = 'https://api.bill.com/api/v2/Bulk/Crud/Create/Bill'
			self.bill_com_bill_update_url = 'https://api.bill.com/api/v2/Bulk/Crud/Update/Bill'
			self.bill_com_mfa_challenge_create_url = 'https://api.bill.com/api/v2/MFAChallenge.json'
			self.bill_com_mfa_challenge_authenticate_url = 'https://api.bill.com/api/v2/MFAAuthenticate.json'
			self.bill_com_organization_bank_account_url = 'https://api.bill.com/api/v2/List/BankAccount.json'
			self.bill_com_payment_create_url = 'https://api.bill.com/api/v2/PayBills.json'
			self.bill_com_payment_import_url = 'https://api.bill.com/api/v2/List/SentPay.json'
			self.bill_com_payment_cancel_url = 'https://api.bill.com/api/v2/CancelAPPayment.json'
			self.bill_com_vendor_import_url = 'https://api.bill.com/api/v2/List/Vendor.json'
			self.bill_com_vendor_bank_account_import_url = 'https://api.bill.com/api/v2/List/VendorBankAccount.json'
			self.bill_com_bill_import_url = 'https://api.bill.com/api/v2/List/Bill.json'
			self.bill_com_bill_upload_attachment_url = 'https://api.bill.com/api/v2/UploadAttachment.json'
			self.bill_com_coa_import_url = 'https://api.bill.com/api/v2/List/ChartOfAccount.json'
			self.bill_com_attachment_import_url = 'https://api.bill.com/api/v2//UploadAttachment.json'
			self.bill_com_fund_transfer_report_url = 'https://api.bill.com/api/v2/List/MoneyMovement.json'
			self.bill_com_payment_term_import_url = 'https://api.bill.com/api/v2/List/PaymentTerm.json'
			self.bill_com_set_bill_approver_url = 'https://api.bill.com/api/v2/SetApprovers.json'
			self.bill_com_users_import_url = 'https://api.bill.com/api/v2/List/User.json'

	def get_organizational_bank_accounts_details(self):
		if self.state == 'expired':
			raise ValidationError('Can not Get Organizational Bank Account details as your subscription expired.')
		else:
			bill_com_user_name = self.bill_com_user_name
			bill_com_password = self.bill_com_password
			bill_com_orgid = self.bill_com_orgid
			bill_com_devkey = self.bill_com_devkey
			bill_com_login_url = self.bill_com_login_url
			bill_com_organization_bank_account_url = self.bill_com_organization_bank_account_url
			# bill_com_service_obj = BillComService(bill_com_user_name, bill_com_password, bill_com_orgid, bill_com_devkey,
			# 									  bill_com_login_url)
			# data_dict = '''{"start" : 0, "max" : 999}'''
			# bill_com_service_obj.get_organizational_bank_accounts_details(bill_com_organization_bank_account_url, data)
			data_dict = {"start" : 0, "max" : 999}
			data = {
				'bill_com_user_name': bill_com_user_name,
				'bill_com_password': bill_com_password,
				'bill_com_orgid': bill_com_orgid,
				'bill_com_devkey': bill_com_devkey,
				'bill_com_login_url': bill_com_login_url,
				'bill_com_organization_bank_account_url': bill_com_organization_bank_account_url,
				'data': data_dict,
			}
			url = self.env['ir.config_parameter'].sudo().get_param('client_subscription.host_db_url')
			if not url:
				raise UserError("Please Configure Sevice DB URL in General settings.")

			try:
				response = requests.post(
					f"{url}/get_organizational_bank_accounts_details",
					json=data,
					headers={'Content-Type': 'application/json'},
					verify=False
				)
				result = response.json()
				_logger.info("get_organizational_bank_accounts_details result %s" % result)
				# if response.status_code == 200:
				# 	result = response.json()
				# 	print("Parsed response:", result)
				if result.get('result') and result['result'].get('status') == 'success':
					result = response.json()
					print("Parsed response:", result)
				else:
					raise UserError(f"Failed to fetch challenge ID: {result['result'].get('message')}")

					# if result.get('result') and result['result'].get('status') == 'success':
				# 		self.bill_com_mfa_challenge = result['result'].get('challengeId')
				# 	else:
				# 		raise UserError(result.get('error', 'Failed to fetch challenge ID.'))
				# else:
				# 	raise UserError(f"Failed to fetch challenge ID: {response.text}")

			except requests.exceptions.RequestException as e:
				raise UserError(f"Error connecting to the server: {str(e)}")

	def get_mfn_challenge(self):
		if self.state == 'expired':
			raise ValidationError('Can not Get MFA Challenge ID as your subscription expired.')
		else:
			if not all([self.bill_com_user_name, self.bill_com_password, self.bill_com_orgid,
						self.bill_com_devkey, self.bill_com_login_url, self.bill_com_mfa_challenge_create_url]):
				raise UserError("Please ensure all Bill.com credentials and URLs are set.")
			data = {
				'db_name': self.env.cr.dbname,
				'username': self.bill_com_user_name,
				'password': self.bill_com_password,
				'orgid': self.bill_com_orgid,
				'devkey': self.bill_com_devkey,
				'login_url': self.bill_com_login_url,
				'mfa_challenge_url': self.bill_com_mfa_challenge_create_url,
			}
			url = self.env['ir.config_parameter'].sudo().get_param('client_subscription.host_db_url')
			if not url:
				raise UserError("Please Configure Sevice DB URL in General settings.")

			try:
				response = requests.post(
					f"{url}/get_mfn_challenge",
					json=data,
					headers={'Content-Type': 'application/json'},
					verify=False
				)

				result = response.json()
				_logger.info("get_mfn_challenge result %s" % result)
				if response.status_code == 200:
					result = response.json()
					print("Parsed response:", result)
					if result.get('result') and result['result'].get('status') == 'success':
						self.bill_com_mfa_challenge = result['result'].get('challengeId')
					else:
						raise UserError(result['result'].get('message'))
				else:
					raise UserError(f"Failed to fetch challenge ID: {result['result'].get('message')}")

			except requests.exceptions.RequestException as e:
				raise UserError(f"Error connecting to the server: {str(e)}")

	def mfn_authenticate(self):
		if self.state == 'expired':
			raise ValidationError('Can not get MFA Authenticates as your subscription expired.')
		else:
			if not self.bill_com_mfa_token:
				raise UserError(_("Please Enter MFA Token"))
			if not self.bill_com_device_name:
				raise UserError(_("Please Enter Device Name"))
			if not self.bill_com_machine_name:
				raise UserError(_("Please Enter Machine Name"))
			if not self.bill_com_mfa_challenge:
				raise UserError(_("Please Enter MFA Challenge"))
			if not all([self.bill_com_user_name, self.bill_com_password, self.bill_com_orgid,
						self.bill_com_devkey, self.bill_com_login_url, self.bill_com_mfa_challenge_authenticate_url]):
				raise UserError("Please ensure all Bill.com credentials and URLs are set.")
			data = {
				'username': self.bill_com_user_name,
				'password': self.bill_com_password,
				'orgid': self.bill_com_orgid,
				'devkey': self.bill_com_devkey,
				'login_url': self.bill_com_login_url,
				'challengeId': self.bill_com_mfa_challenge,
				'token': self.bill_com_mfa_token,
				'deviceId': self.bill_com_device_name,
				'machineName': self.bill_com_machine_name,
				'bill_com_mfa_challenge_authenticate_url': self.bill_com_mfa_challenge_authenticate_url,
				'rememberMe': 'true'
			}
			url = self.env['ir.config_parameter'].sudo().get_param('client_subscription.host_db_url')
			if not url:
				raise UserError("Please Configure Sevice DB URL in General settings.")

			try:
				response = requests.post(
					f"{url}/mfn_authenticate",
					json=data,
					headers={'Content-Type': 'application/json'},
					verify=False
				)
				result = response.json()
				_logger.info("mfn_authenticate result: %s" % result)
				if response.status_code == 200:
					result = response.json()
					if result.get('result') and result['result'].get('status') == 'success':
						self.bill_com_mfa_id = result['result'].get('mfaId')
					else:
						raise UserError(result['result'].get('message'))
				else:
					raise UserError(f"Failed to authenticate MFA Id: {result['result'].get('message')}")

			except requests.exceptions.RequestException as e:
				raise UserError(f"Error connecting to the server: {str(e)}")


	@api.model
	def auto_bill_com_payment_import(self, from_date='', to_date='', bill_payment_id=''):
		if self.state == 'expired':
			raise ValidationError('Can not Import Payments as your subscription expired.')
		else:
			context = self._context.copy()
			if from_date and to_date:
				context.update({'from_date': from_date, 'to_date': to_date})
			if bill_payment_id:
				context.update({'bill_payment_id': bill_payment_id})
			context.update({'from_scheduler': True})
			search_config = self.env['bill.com.config'].search([])
			search_config.with_context(context).import_bill_com_payments()

	@api.model
	def auto_bill_com_bill_import(self, from_date='', to_date='', bill_id=''):
		if self.state == 'expired':
			raise ValidationError('Can not Import Bills as your subscription expired.')
		else:
			context = self._context.copy()
			if from_date and to_date:
				context.update({'from_date': from_date, 'to_date': to_date})
			if bill_id:
				context.update({'bill_id': bill_id})
			context.update({'from_scheduler': True})
			search_config = self.env['bill.com.config'].search([])
			search_config.with_context(context).import_bill_com_bills()

	def import_bill_com_payments(self):
		context = self._context.copy()
		for each_config in self:
			if each_config.state == 'expired':
					raise ValidationError('Can not Import Payments as your subscription expired.')
			else:
				last_payment_imported_date = each_config.last_payment_imported_date
				if not last_payment_imported_date and not 'from_scheduler' in context:
					raise UserError(_("Please Enter Last Imported Date"))
				bill_com_user_name = each_config.bill_com_user_name
				bill_com_password = each_config.bill_com_password
				bill_com_orgid = each_config.bill_com_orgid
				bill_com_devkey = each_config.bill_com_devkey
				bill_com_login_url = each_config.bill_com_login_url
				bill_com_payment_import_url = each_config.bill_com_payment_import_url
				filter_data = ''
				if 'bill_payment_id' in context:
					bill_payment_id = context.get('bill_payment_id', '')
					filter_data = {"start": 0, "max": 999,
								   "filters": [{"field": "id", "op": "=", "value": bill_payment_id}]}
				elif 'from_date' in context and 'to_date' in context:
					from_date = context.get('from_date', '')
					to_date = context.get('to_date', '')
					filter_data = {"start": 0, "max": 999,
								   "filters": [{"field": "updatedTime", "op": ">=", "value": from_date},
											   {"field": "updatedTime", "op": "<=", "value": to_date}]}
				elif last_payment_imported_date:
					last_payment_imported_date = fields.Date.to_string(last_payment_imported_date - timedelta(1))
					filter_data = {"start": 0, "max": 999,
								   "filters": [{"field": "updatedTime", "op": ">", "value": last_payment_imported_date}]}
				if filter_data:
					# bill_com_service_obj = BillComService(bill_com_user_name, bill_com_password, bill_com_orgid,
					# 									  bill_com_devkey, bill_com_login_url)
					# filter_data = json.dumps(filter_data)
					# payment_data = bill_com_service_obj.import_bill_payments(bill_com_payment_import_url, filter_data)
					data = {
						'bill_com_user_name': bill_com_user_name,
						'bill_com_password': bill_com_password,
						'bill_com_orgid': bill_com_orgid,
						'bill_com_devkey': bill_com_devkey,
						'bill_com_login_url': bill_com_login_url,
						'bill_com_payment_import_url': bill_com_payment_import_url,
						'filter_data': filter_data,
					}
					url = self.env['ir.config_parameter'].sudo().get_param('client_subscription.host_db_url')
					if not url:
						raise UserError("Please Configure Sevice DB URL in General settings.")

					# try:
					response = requests.post(
						f"{url}/import_bill_com_payments",
						json=data,
						headers={'Content-Type': 'application/json'},
						verify=False
					)
					print(">>>>>>>>>>>>>>>>>>>>>. response", response)
					result = response.json()
					_logger.info("import_bill_com_payments result: %s" % result)
					if response.status_code == 200:
						result = response.json()
						print("Parsed response:", result)
						if result.get('result') and result['result'].get('status') == 'success':
							payment_data = result['result'].get('data')
							print("======================payment_data", payment_data)
					# except requests.exceptions.RequestException as e:
						# raise UserError(f"Error connecting to the server: {str(e)}")

							if payment_data:
								cr = self._cr
								payment_obj = self.env['account.payment']
								account_move_obj = self.env['account.move']
								error_logs_obj = self.env['bill.com.error.logs']
								for each_data in payment_data:
									paymentName = each_data.get('name', '')
									bill_com_payment_id = each_data.get('id', '')
									try:
										status = each_data.get('status', '')
										processDate = each_data.get('processDate', '')
										journal_id = [each_config.default_payment_journal]
										bill_com_exchange_rate = each_data.get('exchangeRate', '')
										if status in ('1', '2', '3', '4') and journal_id:
											cr.execute(
												"select id from account_payment where bill_com_payment_id='%s'" % (
													bill_com_payment_id))
											odoo_payment_ids = list(filter(None, map(lambda x: x, cr.fetchall())))
											if odoo_payment_ids:
												for each_odoo_payment_id in odoo_payment_ids:
													payment_id = each_odoo_payment_id[0]
													payment_id_brw = payment_obj.sudo().browse(payment_id)
													payment_id_state = payment_id_brw.state
													if status in ('1', '2'):
														if status == '1':
															payment_id_brw.bill_com_payment_status = 'Scheduled'
														elif status == '2':
																payment_id_brw.bill_com_payment_status = 'Paid'
													elif status in ('3', '4') and payment_id_state != 'cancelled':
														payment_id_brw.with_context({'from_bill_com_cancel': True}).action_draft()
														payment_id_brw.with_context({'from_bill_com_cancel': True}).action_cancel()
														payment_id_brw.bill_com_payment_status = 'Cancelled'
													ref = payment_id_brw.ref
													if ref:
														cr.execute("""select id from account_move where name = '%s'""" % (ref))
														odoo_invoice_id = list(filter(None, map(lambda x: x[0], cr.fetchall())))
														if odoo_invoice_id:
															odoo_invoice_id_brw = account_move_obj.sudo().browse(odoo_invoice_id[0])
															odoo_invoice_id_brw._compute_amount()
											else:
												billPays = each_data.get('billPays', [])
												billIds = []
												for each_bill_data in billPays:
													billId = each_bill_data.get('billId')
													amount = each_bill_data.get('amount')
													billIds.append(billId)
													cr.execute(
														"""select id from account_move where bill_com_bill_id = '%s'""" % (billId))
													odoo_invoice_ids = list(filter(None, map(lambda x: x[0], cr.fetchall())))
													if odoo_invoice_ids and status in ('1', '2'):
														odoo_invoice_id_brw = account_move_obj.browse(odoo_invoice_ids[0])
														bill_currency_id = odoo_invoice_id_brw.currency_id
														company_id = odoo_invoice_id_brw.company_id.id
														payment_vals = {'amount': amount,
																		'bill_com_payment_id': bill_com_payment_id,
																		'date': processDate,
																		'journal_id': journal_id[0].id, 'payment_type': 'outbound',
																		'currency_id': bill_currency_id.id,
																		'partner_type': 'supplier', 'company_id': company_id,
																		'reconciled_invoice_ids': [(6, 0, odoo_invoice_ids)],
																		'partner_id': odoo_invoice_id_brw.commercial_partner_id.id,
																		'ref': odoo_invoice_id_brw.name,
																		'currency_exchange_rate': bill_com_exchange_rate if bill_com_exchange_rate and bill_com_exchange_rate > 0 else 0.0,
																		'payment_method_id': 1,
																		'payment_date': processDate,
																		'vendor_name': odoo_invoice_id_brw.commercial_partner_id.name}
														new_payment_id = payment_obj.create(payment_vals)
														new_payment_id.action_post()
														if status == '1':
															new_payment_id.bill_com_payment_status = 'Scheduled'
														elif status == '2':
															new_payment_id.bill_com_payment_status = 'Paid'
														move_lines = new_payment_id.move_id.line_ids.filtered(
															lambda line: line.account_type in (
																'asset_receivable', 'liability_payable') and not line.reconciled)
														for line in move_lines:
															odoo_invoice_id_brw.with_context(
																{'skip_valiation': True}).js_assign_outstanding_line(line.id)
									except Exception as e:
										error_message = "%s(%s) - %s " % (paymentName, bill_com_payment_id, str(e))
										error_logs_obj.create_error_log('Import Payment', str(error_message))
						else:
							raise UserError(f"Failed to fetch challenge ID: {result['result'].get('message')}")
				current_date_time = fields.Datetime.now()
				each_config.last_payment_imported_date = current_date_time

	def check_duplicate_vendor_reference(self, ref, partner_id, invoice_date):
		ref = ref.replace("'", "''")
		cr = self._cr
		cr.execute(
			"""SELECT id from account_move move where move.ref='%s' and move.partner_id=%s and (move.invoice_date is Null or move.invoice_date='%s')"""
			% (ref, partner_id, invoice_date))
		invoice_exists = list(filter(None, map(lambda x: x, cr.fetchall())))
		if invoice_exists:
			return True
		return False

	def get_line_account(self, bill_com_coa_id, product_id, journal_id, company_id):
		account_id = False
		search_odoo_account_id = self.env['account.account'].search(
			[('bill_com_coa_id', '=', bill_com_coa_id), ('company_id', '=', company_id)], limit=1)
		if search_odoo_account_id:
			return search_odoo_account_id
		if product_id:
			accounts = product_id.product_tmpl_id.get_product_accounts(fiscal_pos=False)
			if accounts and accounts.get('income'):
				account_id = accounts.get('income', False)
		elif journal_id:
			account_id = journal_id.default_account_id
		return account_id

	def import_bill_com_bills(self):
		context = self._context.copy()
		for each_config in self:
			if each_config.state == 'expired':
				raise ValidationError('Can not Import Bills as your subscription expired.')
			else:
				last_bill_imported_date = each_config.last_bill_imported_date
				if not last_bill_imported_date and not 'from_scheduler' in context:
					raise UserError(_("Please Enter Last Imported Date"))
				bill_com_user_name = each_config.bill_com_user_name
				bill_com_password = each_config.bill_com_password
				bill_com_orgid = each_config.bill_com_orgid
				bill_com_devkey = each_config.bill_com_devkey
				bill_com_login_url = each_config.bill_com_login_url
				bill_com_bill_import_url = each_config.bill_com_bill_import_url
				bill_com_bill_status = each_config.bill_com_bill_status
				bill_com_vendor_import_url = each_config.bill_com_vendor_import_url
				journal_obj = self.env['account.journal']
				company_ids = each_config.company_ids
				filter_data = ''
				if 'bill_id' in context:
					bill_id = context.get('bill_id', '')
					filter_data = {"start": 0, "max": 999,
								   "filters": [{"field": "id", "op": "=", "value": bill_id},
											   {"field": "isActive", "op": "=", "value": "1"}]}
				elif 'from_date' in context and 'to_date' in context:
					from_date = context.get('from_date', '')
					to_date = context.get('to_date', '')
					filter_data = {"start": 0, "max": 999,
								   "filters": [{"field": "updatedTime", "op": ">=", "value": from_date},
											   {"field": "updatedTime", "op": "<=", "value": to_date},
											   {"field": "isActive", "op": "=", "value": "1"}
											   ]}
					if bill_com_bill_status and bill_com_bill_status != 'all':
						filter_data["filters"].append({"field": "paymentStatus", "op": "=", "value": bill_com_bill_status})
				elif last_bill_imported_date:
					last_bill_imported_date = fields.Date.to_string(last_bill_imported_date)
					filter_data = {"start": 0, "max": 999,
								   "filters": [{"field": "updatedTime", "op": ">", "value": last_bill_imported_date},
											   {"field": "isActive", "op": "=", "value": "1"}]}
					if bill_com_bill_status and bill_com_bill_status != 'all':
						filter_data["filters"].append({"field": "paymentStatus", "op": "=", "value": bill_com_bill_status})
				if filter_data:
					# bill_com_service_obj = BillComService(bill_com_user_name, bill_com_password, bill_com_orgid,
					# 									  bill_com_devkey, bill_com_login_url)
					# filter_data = json.dumps(filter_data)
					# bill_data = bill_com_service_obj.import_bills(bill_com_bill_import_url, filter_data)
					data = {
						'bill_com_bill_import_url': bill_com_bill_import_url,
						'bill_com_user_name': bill_com_user_name,
						'bill_com_password': bill_com_password,
						'bill_com_orgid': bill_com_orgid,
						'bill_com_devkey': bill_com_devkey,
						'bill_com_login_url': bill_com_login_url,
						'filter_data':filter_data,
					}
					url = self.env['ir.config_parameter'].sudo().get_param('client_subscription.host_db_url')
					if not url:
						raise UserError("Please Configure Sevice DB URL in General settings.")

					bill_response = requests.post(
						f"{url}/import_bill_com_bills",
						json=data,
						headers={'Content-Type': 'application/json'},
						verify=False
					)
					print(" >>>>>>>>>>>>>>>>>>>>>>>> bill_response ", bill_response)
					result = bill_response.json()
					_logger.info("import_bill_com_bills result %s" % result)
					print(" >>>>>>>>>>>>>>>>>>>>>>>> result ", result)
					if result.get('result') and result['result'].get('status') == 'success':
						bill_data = result['result'].get('data')
						print("================ bill_data", bill_data)
						cr = self._cr
						account_move_obj = self.env['account.move']
						purchase_order_obj = self.env['purchase.order']
						partner_obj = self.env['res.partner']
						error_logs_obj = self.env['bill.com.error.logs']
						product_obj = self.env['product.product']
						currency_obj = self.env['res.currency']
						bill_com_vendor_company_data_obj = self.env['bill.com.vendor.company.data']
						payment_term_obj = self.env['account.payment.term']
						if bill_data:
							for each_data in bill_data:
								bill_com_bill_id = each_data.get('id', '')
								invoice_number = each_data.get('invoiceNumber', '')
								try:
									approvalStatus = each_data.get('approvalStatus', '')
									if approvalStatus in ('0', '3'):  # 0 means "Unassigned" and 3 Approved.
										bill_com_vendor_id = each_data.get('vendorId', '')
										po_number = each_data.get('poNumber', '')
										localAmount = each_data.get('localAmount')
										bill_amount = localAmount if 'localAmount' in each_data and localAmount and localAmount > 0.0 else each_data.get(
											'amount')
										invoiceDate = each_data.get('invoiceDate')
										dueDate = each_data.get('dueDate')
										glPostingDate = each_data.get('glPostingDate', '')
										exchangeRate = each_data.get('exchangeRate', '')
										paymentTermId = each_data.get('paymentTermId', '')
										if paymentTermId:
											odoo_payment_term_id = payment_term_obj.sudo().search(
												[('bill_com_payment_term_ids.bill_com_payment_term_id', '=', paymentTermId)],
												limit=1)
										reference = invoice_number
										journal_id = journal_obj.search(
											[('company_id', 'in', company_ids.ids), ('type', '=', 'purchase')], limit=1)
										if journal_id:
											company_id = journal_id.company_id
										else:
											error_message = "%s - Purchase Journal Not Found" % (
												invoice_number)
											error_logs_obj.create_error_log('Import Bill', str(error_message))
											continue
										odoo_vendor_id = partner_obj.get_odoo_vendor_id(bill_com_vendor_id)
										if not odoo_vendor_id:
											filter_data = {"start": 0, "max": 999,
														   "filters": [{"field": "id", "op": "=", "value": bill_com_vendor_id}]}
											filter_data = json.dumps(filter_data)
											response_vendor_data = bill_com_service_obj.import_vendor_data(
												bill_com_vendor_import_url, filter_data)
											if response_vendor_data:
												response_vendor_data = response_vendor_data[0]
												vendor_name = response_vendor_data.get('name', '')
												isActive = response_vendor_data.get('isActive', '')
												address1 = response_vendor_data.get('address1', '')
												address2 = response_vendor_data.get('address2', '')
												addressCity = response_vendor_data.get('addressCity', '')
												addressZip = response_vendor_data.get('addressZip', '')
												addressCity = response_vendor_data.get('addressCity', '')
												addressCountry = response_vendor_data.get('addressCountry', '')
												odoo_country_rec_id = odoo_state_rec_id = False
												if addressCountry:
													odoo_country_id = self.env['res.country'].sudo().search(
														[('name', '=', addressCountry)], limit=1)
													# cr.execute(
													#     "select id from res_country where name ilike '%s'" % (addressCountry))
													# odoo_country_id = list(filter(None, map(lambda x: x[0], cr.fetchall())))
													if odoo_country_id:
														odoo_country_rec_id = odoo_country_id.id
														addressState = response_vendor_data.get('addressState')

														if addressState:
															odoo_state_id = self.env['res.country.state'].sudo().search(
																[('code', '=', addressState),
																 ('country_id', '=', odoo_country_rec_id)], limit=1)
															# cr.execute(
															#     "select id from res_country_state where code='%s' and country_id=%s" % (
															#     addressState, odoo_country_id[0]))
															# odoo_state_id = list(
															#     filter(None, map(lambda x: x[0], cr.fetchall())))
															if odoo_state_id:
																odoo_state_rec_id = odoo_state_id.id
												phone = response_vendor_data.get('phone', '')
												email = response_vendor_data.get('email', '')
												bill_currency = response_vendor_data.get('billCurrency')
												bill_currency_id = currency_obj.search([('name', '=', bill_currency)])
												vals = {'supplier_rank': 1, 'name': vendor_name,
														'email': email if email else False,
														'active': True if isActive == '1' else False, 'street': address1,
														'street2': address2, 'city': addressCity,
														'zip': addressZip, 'country_id': odoo_country_rec_id,
														'state_id': odoo_state_rec_id, 'phone': phone if phone else '',
														'property_purchase_currency_id': bill_currency_id.id if bill_currency_id else False}
												odoo_vendor_id = [partner_obj.create(vals).id]
												for each_com in company_ids:
													bill_com_vendor_company_data_obj.sudo().create(
														{'partner_id': odoo_vendor_id[0],
														 'bill_com_vendor_id': bill_com_vendor_id, 'company_id': each_com.id})
										if odoo_vendor_id:
											cr.execute(
												"select id from account_move where bill_com_bill_id='%s' and move_type='in_invoice'" % (
													bill_com_bill_id))
											odoo_bill_id = list(filter(None, map(lambda x: x[0], cr.fetchall())))
											po_number = po_number.replace("'", "''") if po_number else False
											cr.execute("select id from purchase_order where name='%s'" % (po_number))
											odoo_purchase_order_id = list(filter(None, map(lambda x: x[0], cr.fetchall())))
											billLineItems = each_data.get('billLineItems', [])
											line_vals = []
											for each_line_data in billLineItems:
												description = each_line_data.get('description', '')
												chartOfAccountId = each_line_data.get('chartOfAccountId', '')
												departmentId = each_line_data.get('departmentId', '')
												description_brw = description.find('[') if description else ''
												purchase_line_id = False
												if description_brw == 0:
													odoo_internal_reference = description.split('[', 1)[1].split(']')[0]
													product_id = product_obj.search(
														['|', ('default_code', '=', odoo_internal_reference),
														 ('name', '=', description)], limit=1)
												else:
													product_id = product_obj.search([('name', '=', description)], limit=1)
												quantity = each_line_data.get('quantity', 1)
												subtotal = each_line_data.get('amount', 0.0)
												unit_price = each_line_data.get('unit_price', 0.0)
												if not quantity:
													quantity = 1
												if 'quantity' not in each_line_data:
													quantity = subtotal / unit_price
												if 'unit_price' in each_line_data:
													unit_price = unit_price
												else:
													unit_price = subtotal / quantity
												if odoo_purchase_order_id and product_id:
													cr.execute(
														"select id from purchase_order_line where order_id=%s and product_id=%s" % (
															odoo_purchase_order_id[0], product_id.id))
													purchase_line_id = list(filter(None, map(lambda x: x[0], cr.fetchall())))
												line_account_id = self.get_line_account(chartOfAccountId,
																						product_id if product_id else False,
																						journal_id, company_id.id)
												line_vals.append((0, 0, {
													'account_id': line_account_id.id,
													'name': description, 'product_id': product_id.id if product_id else False,
													'display_type': 'product',
													'quantity': quantity,
													'price_unit': unit_price, 'price_subtotal': unit_price,
													'purchase_line_id': purchase_line_id[0] if purchase_line_id else False,
													'tax_ids': []
												}))
											partner_obj_brw = partner_obj.browse(odoo_vendor_id[0])
											company_currency_id = company_id.currency_id.id
											if not odoo_bill_id and line_vals:
												if not self.check_duplicate_vendor_reference(invoice_number, odoo_vendor_id[0],
																							 invoiceDate):
													partner_currency = partner_obj_brw.property_purchase_currency_id
													date = fields.Date.today()
													bill_vals = {
														'partner_id': odoo_vendor_id[0], 'ref': invoice_number,
														'bill_com_bill_id': bill_com_bill_id,
														'invoice_line_ids': line_vals, 'move_type': 'in_invoice',
														'invoice_date': invoiceDate, 'invoice_date_due': dueDate,
														'state': 'draft',
														'invoice_origin': po_number,
														'journal_id': journal_id.id if journal_id else False,
														'company_id': company_id.id,
														'company_currency_id': company_currency_id,
														'currency_id': partner_currency.id if partner_currency else company_currency_id}
													# if odoo_payment_term_id:
													#     bill_vals.update({'invoice_payment_term_id': odoo_payment_term_id.id})
													if glPostingDate:
														bill_vals.update({'date': glPostingDate})
													if exchangeRate:
														bill_vals.update({'currency_exchange_rate': exchangeRate})
													odoo_bill_id = account_move_obj.with_context(
														{'currency_exchange_rate': exchangeRate}).create(bill_vals)
													odoo_bill_id.with_context({'from_import_bill': True}).action_post()
													odoo_bill_id = odoo_bill_id.id
													cr.execute(
														"select purchase_order_id from account_move_purchase_order_rel where account_move_id='%s'" % (
															odoo_bill_id))
													purchase_order_id = list(filter(None, map(lambda x: x[0], cr.fetchall())))
													if purchase_order_id:
														purchase_order_obj.browse(purchase_order_id[0])._compute_invoice()
													if odoo_purchase_order_id:
														purchase_order_obj.browse(odoo_purchase_order_id[0])._compute_invoice()
												else:
													error_message = "%s(%s) - Duplicate Reference Number exists for the same vendor." % (
														invoice_number, bill_com_bill_id)
													error_logs_obj.create_error_log('Import Bill', str(error_message))
								except Exception as e:
									error_message = "%s(%s) - %s" % (invoice_number, bill_com_bill_id, str(e))
									error_logs_obj.create_error_log('Import Bill', str(error_message))
					else:
						raise UserError(f"Failed to fetch challenge ID: {result['result'].get('message')}")
				current_date_time = fields.Datetime.now()
				each_config.last_bill_imported_date = current_date_time

	def import_vendor_data(self):
		context_copy = self._context.copy()
		context_copy.update({'from_import_vendor_data': True})
		bill_com_vendor_company_data_obj = self.env['bill.com.vendor.company.data']
		
		for each_config in self:
			if each_config.state == 'expired':
				raise ValidationError('Can not Import Vendors as your subscription expired.')
			else:
				bill_com_vendor_import_url = each_config.bill_com_vendor_import_url
				if not bill_com_vendor_import_url:
					raise ValidationError(_('Missing Vendor Import URL !'))
				
				company_ids = each_config.company_ids
				bill_com_user_name = each_config.bill_com_user_name
				bill_com_password = each_config.bill_com_password
				bill_com_orgid = each_config.bill_com_orgid
				bill_com_devkey = each_config.bill_com_devkey
				bill_com_login_url = each_config.bill_com_login_url

				# Call the controller and get the response
				data = {
					'bill_com_vendor_import_url': bill_com_vendor_import_url,
					'bill_com_user_name': bill_com_user_name,
					'bill_com_password': bill_com_password,
					'bill_com_orgid': bill_com_orgid,
					'bill_com_devkey': bill_com_devkey,
					'bill_com_login_url': bill_com_login_url,
				}
				url = self.env['ir.config_parameter'].sudo().get_param('client_subscription.host_db_url')
				if not url:
					raise UserError("Please Configure Sevice DB URL in General settings.")

				try:
					vendor_data_response = requests.post(
						f"{url}/import_vendor_data",
						json=data,
						headers={'Content-Type': 'application/json'},
						verify=False
					)
					print(" >>>>>>>>>>>>>>>>>>>>>>>> vendor_data_response ", vendor_data_response)
					result = vendor_data_response.json()
					_logger.info("import_vendor_data result %s" % result)
					if result.get('result') and result['result'].get('status') == 'success':
						final_vendor_data = result['result'].get('data', [])
						print("#########################", final_vendor_data)
						if not final_vendor_data:
							raise ValidationError(_('No vendor data found from Bill.com'))
						
						cr = each_config._cr
						partner_obj = self.env['res.partner']
						i = 1
						_logger.info('length of Vendor Data %s' % len(final_vendor_data))
						
						for each_vendor_data in final_vendor_data:
							_logger.info('i value %s' % i)
							vendor_id = each_vendor_data.get('id')
							if vendor_id:
								query_string = ''
								name = each_vendor_data.get('name')
								if name == "'\'":
									continue
								name_replace = name.replace("'", "''")
								odoo_vendor_id = partner_obj.get_odoo_vendor_id(vendor_id)
								if not odoo_vendor_id:
									query_string += "name ilike '%s'" % (name_replace)
									cr.execute("select id from res_partner where %s limit 1" % (query_string))
									odoo_vendor_id = list(filter(None, map(lambda x: x[0], cr.fetchall())))
								_logger.info('odoo_vendor_id %s, %s' % odoo_vendor_id % query_string)
								email = each_vendor_data.get('email')
								isActive = each_vendor_data.get('isActive')
								address1 = each_vendor_data.get('address1')
								address2 = each_vendor_data.get('address2')
								addressCity = each_vendor_data.get('addressCity')
								addressZip = each_vendor_data.get('addressZip')
								addressCountry = each_vendor_data.get('addressCountry')
								bill_currency = each_vendor_data.get('billCurrency')
								accountType = each_vendor_data.get('accountType')
								bill_currency_id = self.env['res.currency'].search([('name', '=', bill_currency)])
								odoo_country_rec_id = odoo_state_rec_id = False
								if addressCountry:
									odoo_country_id = self.env['res.country'].sudo().search([('name', '=', addressCountry)], limit=1)
									if odoo_country_id:
										odoo_country_rec_id = odoo_country_id.id
										addressState = each_vendor_data.get('addressState')
										if addressState:
											addressState = addressState.replace("'", "''")
											cr.execute("select id from res_country_state where code='%s' and country_id=%s"
													   % (addressState, odoo_country_id.id))
											odoo_state_id = list(filter(None, map(lambda x: x[0], cr.fetchall())))
											if odoo_state_id:
												odoo_state_rec_id = odoo_state_id[0]
								phone = each_vendor_data.get('phone')
								company_type = 'person'
								if accountType == '1':
									company_type = 'company'
								vals = {'supplier_rank': 1, 'name': name, 'bill_com_vendor_id': vendor_id,
										'email': email if email else False, 'active': True if isActive == '1' else False,
										'street': address1, 'street2': address2, 'city': addressCity, 'zip': addressZip,
										'country_id': odoo_country_rec_id, 'state_id': odoo_state_rec_id,
										'phone': phone if phone else '',
										'property_purchase_currency_id': bill_currency_id.id if bill_currency_id else False,
										'company_type': company_type}
								if not odoo_vendor_id:
									partner_id_brw = partner_obj.create(vals)
								else:
									partner_id_brw = partner_obj.sudo().browse(odoo_vendor_id[0])
									partner_id_brw.with_context(context_copy).write(vals)
								for each_company in company_ids:
									bill_com_vendor_id = partner_id_brw.get_bill_com_vendor_id(partner_id_brw, each_company)
									if not bill_com_vendor_id:
										bill_com_vendor_company_data_obj.sudo().create({'partner_id': partner_id_brw.id,
																						 'company_id': each_company.id,
																						 'bill_com_vendor_id': vendor_id})
							i = i + 1
					else:
						raise UserError(f"Failed to fetch challenge ID: {result['result'].get('message')}")
				except requests.exceptions.RequestException as e:
					raise UserError(f"Error connecting to the server: {str(e)}")


	@api.model
	def auto_bill_com_vendor_sync(self):
		if self.state == 'expired':
			raise ValidationError('Can not Sync Vendor as your subscription expired.')
		else:
			search_config = self.env['bill.com.config'].search([])
			search_config.import_vendor_data()

	def import_vendor_bank_account_data(self):
		for each_config in self:
			if each_config.state == 'expired':
				raise ValidationError('Can not Import Vendor Bank Account data as your subscription expired.')
			else:
				bill_com_vendor_bank_account_import_url = each_config.bill_com_vendor_bank_account_import_url
				if not bill_com_vendor_bank_account_import_url:
					raise ValidationError(_('Missing Vendor Bank Accounts Import URL !'))
				company_id = each_config.company_ids.ids
				bill_com_user_name = each_config.bill_com_user_name
				bill_com_password = each_config.bill_com_password
				bill_com_orgid = each_config.bill_com_orgid
				bill_com_devkey = each_config.bill_com_devkey
				bill_com_login_url = each_config.bill_com_login_url
				vendor_bank_data, final_vendor_bank_data = True, []
				start = 0
				max_range = 999
				while vendor_bank_data:
					filter_data = {"start": start, "max": max_range,
								   "filters": [{"field": "status", "op": "=", "value": '1'}]}
					# bill_com_service_obj = BillComService(bill_com_user_name, bill_com_password, bill_com_orgid,
					# 									  bill_com_devkey, bill_com_login_url)
					# filter_data = json.dumps(filter_data)
					# response_vendor_bank_data = bill_com_service_obj.import_vendor_bank_account_data(
					# 	bill_com_vendor_bank_account_import_url, filter_data)
					data = {
						'bill_com_vendor_bank_account_import_url': bill_com_vendor_bank_account_import_url,
						'bill_com_user_name': bill_com_user_name,
						'bill_com_password': bill_com_password,
						'bill_com_orgid': bill_com_orgid,
						'bill_com_devkey': bill_com_devkey,
						'bill_com_login_url': bill_com_login_url,
						'filter_data': filter_data,
					}
					url = self.env['ir.config_parameter'].sudo().get_param('client_subscription.host_db_url')
					if not url:
						raise UserError("Please Configure Sevice DB URL in General settings.")

					response = requests.post(
						f"{url}/import_vendor_bank_account_data",
						json=data,
						headers={'Content-Type': 'application/json'},
						verify=False
					)
					print(" >>>>>>>>>>>>>>>>>>>>>>>> response ", response)
					result = response.json()
					_logger.info("import_vendor_bank_account_data result" % result)
					if result.get('result') and result['result'].get('status') == 'success':
						response_vendor_bank_data = result['result'].get('data', [])
						print("======================== response_vendor_bank_data", response_vendor_bank_data)
						if response_vendor_bank_data:
							final_vendor_bank_data = final_vendor_bank_data + response_vendor_bank_data
							start = start + max_range
						else:
							vendor_bank_data = False
					else:
						raise UserError(f"Failed to fetch challenge ID: {result['result'].get('message')}")
				cr = each_config._cr
				partner_bank_obj = self.env['res.partner.bank']
				partner_obj = self.env['res.partner']
				i = 1
				for each_vendor_bank_data in final_vendor_bank_data:
					_logger.info('i value %s' % i)
					vendorId = each_vendor_bank_data.get('vendorId')
					_logger.info('vendorId %s' % vendorId)
					if vendorId:
						odoo_vendor_id = partner_obj.get_odoo_vendor_id(vendorId)
						if odoo_vendor_id:
							odoo_vendor_id_brw = partner_obj.sudo().browse(odoo_vendor_id[0])
							odoo_vendor_name = odoo_vendor_id_brw.name
							query_string = ''
							accountNumber = each_vendor_bank_data.get('accountNumber')[-4:]
							routingNumber = each_vendor_bank_data.get('routingNumber')
							bank_bill_id = each_vendor_bank_data.get('id')
							nameOnAcct = each_vendor_bank_data.get('nameOnAcct')
							if not nameOnAcct:
								nameOnAcct = odoo_vendor_name
							if bank_bill_id and accountNumber and routingNumber:
								query_string = "(bill_com_vendor_bank_account_id='%s') or (aba_routing='%s' and acc_number ilike '%s') and partner_id=%s" % (
									bank_bill_id, routingNumber, '%s' % ('%' + accountNumber), odoo_vendor_id[0])
								cr.execute("select id from res_partner_bank where %s" % (query_string))
								odoo_vendor_bank_id_id = list(filter(None, map(lambda x: x[0], cr.fetchall())))
								_logger.info('odoo_vendor_bank_id_id %s' % odoo_vendor_bank_id_id)
								try:
									if not odoo_vendor_bank_id_id:
										search_bank_acc_id = partner_bank_obj.sudo().search(
											[('acc_number', '=', accountNumber), ('company_id', 'in', company_id)])
										if not search_bank_acc_id:
											for each in company_id:
												partner_bank_obj.with_context({'default_partner_id': True}).sudo().create(
													{'bill_com_vendor_bank_account_id': bank_bill_id,
													 'aba_routing': routingNumber,
													 'acc_number': accountNumber, 'active': True,
													 'partner_id': odoo_vendor_id[0],
													 'bank_id': False, 'acc_holder_name': nameOnAcct,
													 'company_id': each
													 })
								except Exception as e:
									pass
					i = i + 1

	def import_bill_com_coa(self):
		for each_config in self:
			if each_config.state == 'expired':
				raise ValidationError('Can not MAP ChartOfAccounts as your subscription expired.')
			else:
				company_ids = each_config.company_ids.ids
				bill_com_user_name = each_config.bill_com_user_name
				bill_com_password = each_config.bill_com_password
				bill_com_orgid = each_config.bill_com_orgid
				bill_com_devkey = each_config.bill_com_devkey
				bill_com_login_url = each_config.bill_com_login_url
				bill_com_coa_import_url = each_config.bill_com_coa_import_url
				filter_data = {"start": 0, "max": 999, "filters": [{"field": "isActive", "op": "=", "value":"1"}]}
				data = {
					'bill_com_coa_import_url': bill_com_coa_import_url,
					'bill_com_user_name': bill_com_user_name,
					'bill_com_password': bill_com_password,
					'bill_com_orgid': bill_com_orgid,
					'bill_com_devkey': bill_com_devkey,
					'bill_com_login_url': bill_com_login_url,
					'filter_data':filter_data,
				}
				url = self.env['ir.config_parameter'].sudo().get_param('client_subscription.host_db_url')
				if not url:
					raise UserError("Please Configure Sevice DB URL in General settings.")

				coa_response = requests.post(
					f"{url}/import_bill_com_coa",
					json=data,
					headers={'Content-Type': 'application/json'},
					verify=False
				)
				print(" >>>>>>>>>>>>>>>>>>>>>>>> coa_response ", coa_response)
				result = coa_response.json()
				_logger.info("import_bill_com_coa result %s" % result)
				print(" >>>>>>>>>>>>>>>>>>>>>>>> result ", result)
				if result.get('result') and result['result'].get('status') == 'success':
					response_data = result['result'].get('data')
					if response_data:
						account_account_obj = self.env['account.account']
						for each_response in response_data:
							print("================ each_response", each_response)
							accountNumber = each_response.get('accountNumber', '')
							bill_com_coa_id = each_response.get('id', '')
							for each_company in company_ids:
								search_odoo_account_id = account_account_obj.search(
									[('code', '=', accountNumber), ('company_ids', 'in', [each_company])], limit=1)
								print(">>>>>>>>>>>>>>>>>>>>>> search_odoo_account_id", search_odoo_account_id)
								if search_odoo_account_id:
									print("======================== bill_com_coa_id", bill_com_coa_id)
									search_odoo_account_id.write({'bill_com_coa_id': bill_com_coa_id})
				else:
					raise UserError(f"Failed to fetch challenge ID: {result['result'].get('message')}")

	def import_bill_com_payment_term(self):
		for each_config in self:
			if each_config.state == 'expired':
				raise ValidationError('Can not MAP Payment Terms as your subscription expired.')
			else:
				company_ids = each_config.company_ids
				bill_com_user_name = each_config.bill_com_user_name
				bill_com_password = each_config.bill_com_password
				bill_com_orgid = each_config.bill_com_orgid
				bill_com_devkey = each_config.bill_com_devkey
				bill_com_login_url = each_config.bill_com_login_url
				bill_com_payment_term_import_url = each_config.bill_com_payment_term_import_url
				filter_data = {"start": 0, "max": 999}
				# bill_com_service_obj = BillComService(bill_com_user_name, bill_com_password, bill_com_orgid,
				# 									  bill_com_devkey, bill_com_login_url)
				# filter_data = json.dumps(filter_data)
				# response_data = bill_com_service_obj.import_payment_term_data(bill_com_payment_term_import_url, filter_data)
				data = {
					'bill_com_payment_term_import_url': bill_com_payment_term_import_url,
					'bill_com_user_name': bill_com_user_name,
					'bill_com_password': bill_com_password,
					'bill_com_orgid': bill_com_orgid,
					'bill_com_devkey': bill_com_devkey,
					'bill_com_login_url': bill_com_login_url,
					'filter_data':filter_data,
				}
				url = self.env['ir.config_parameter'].sudo().get_param('client_subscription.host_db_url')
				if not url:
					raise UserError("Please Configure Sevice DB URL in General settings.")

				coa_response = requests.post(
					f"{url}/import_bill_com_payment_term",
					json=data,
					headers={'Content-Type': 'application/json'},
					verify=False
				)
				print(" >>>>>>>>>>>>>>>>>>>>>>>> coa_response ", coa_response)
				result = coa_response.json()
				_logger.info("import_bill_com_payment_term result %s" % result)
				print(" >>>>>>>>>>>>>>>>>>>>>>>> result ", result)
				if result.get('result') and result['result'].get('status') == 'success':
					response_data = result['result'].get('data')
					print("=====================response_data", response_data)
					if response_data:
						account_payment_term_obj = self.env['account.payment.term']
						account_payment_term_data_obj = self.env['bill.com.payment.term.company.data']
						for each_response in response_data:
							payment_term = each_response.get('name', '')
							payment_term_name = payment_term.strip()
							due_time = each_response.get('netDue', '')
							bill_com_payment_term_id = each_response.get('id', '')
							# # cr = self._cr
							# self.env.cr.execute("""select account_payment_term.id from account_payment_term
							#             inner join account_payment_term_line on account_payment_term.id = account_payment_term_line.payment_id
							#             where account_payment_term_line.days='%s' and account_payment_term.name ilike %s""",
							#            (due_time, payment_term_name))
							search_odoo_payment_term_id = self.env['account.payment.term'].search([
								('line_ids.nb_days', '=', due_time),
								('name', 'ilike', payment_term_name)
							])
							print("=====================search_odoo_payment_term_id", search_odoo_payment_term_id)
							# search_odoo_payment_term_id = list(filter(None, map(lambda x: x[0], self.env.cr.fetchall())))
							if search_odoo_payment_term_id:
								odoo_mapped_term_id = search_odoo_payment_term_id[0]
								payment_term_brw = account_payment_term_obj.sudo().browse(odoo_mapped_term_id.id)
								print("=======================payment_term_brw", payment_term_brw)
								if payment_term_brw:
									for each_company in company_ids:
										bill_com_payment_id = payment_term_brw.get_bill_com_payment_term_id(
											payment_term_brw, each_company)
										if not bill_com_payment_id:
											account_payment_term_data_obj.sudo().create(
												{'payment_term_id': payment_term_brw.id,
												 'company_id': each_company.id,
												 'bill_com_payment_term_id': bill_com_payment_term_id})
				else:
					raise UserError(f"Failed to fetch challenge ID: {result['result'].get('message')}")

	def _get_fund_transfer_report_data(self, from_date='', to_date=''):
		account_payment_obj = self.env['account.payment']
		# batch_payment_obj = self.env['account.batch.payment']
		bank_journal_ids = self.env['account.journal'].sudo().search(
			[('bank_account_id.bill_com_organization_bank_account_id', '!=', False)])
		for each_journal_id in bank_journal_ids:
			journal_bank_org_id = each_journal_id.bank_account_id.bill_com_organization_bank_account_id
			bill_com_config_id = self.env['bill.com.config'].search(
				[('company_ids', 'in', each_journal_id.company_id.ids)])
			for each_config in bill_com_config_id:
				if each_config.state == 'expired':
					raise ValidationError('Can not Get Fund Transfer Report Data as your subscription expired.')
				else:
					bill_com_fund_transfer_report_url = each_config.bill_com_fund_transfer_report_url
					bill_com_user_name = each_config.bill_com_user_name
					bill_com_password = each_config.bill_com_password
					bill_com_orgid = each_config.bill_com_orgid
					bill_com_devkey = each_config.bill_com_devkey
					bill_com_login_url = each_config.bill_com_login_url
					if from_date and to_date:
						filter_data = {"start": 0, "max": 999,
									   "filters": [{"field": "status", "op": "=", "value": "1"},
												   {"field": "type", "op": "=", "value": "1"},
												   {"field": "bankAccountId", "op": "=", "value": journal_bank_org_id},
												   {"field": "processDate", "op": ">=", "value": from_date},
												   {"field": "processDate", "op": "<=", "value": to_date}]}
					else:
						current_date = fields.Date.today()
						from_date = fields.Date.to_string(current_date - timedelta(1))
						to_date = fields.Date.to_string(current_date)
						filter_data = {"start": 0, "max": 999,
									   "filters": [{"field": "status", "op": "=", "value": "1"},
												   {"field": "type", "op": "=", "value": "1"},
												   {"field": "bankAccountId", "op": "=", "value": journal_bank_org_id},
												   {"field": "processDate", "op": ">=", "value": from_date},
												   {"field": "processDate", "op": "<=", "value": to_date}]}
					# bill_com_service_obj = BillComService(bill_com_user_name, bill_com_password, bill_com_orgid,
					# 									  bill_com_devkey, bill_com_login_url)
					# filter_data = json.dumps(filter_data)
					# fund_transfer_data = bill_com_service_obj.import_fund_transfer_report_data(
					# 	bill_com_fund_transfer_report_url, filter_data)
					data = {
						'bill_com_fund_transfer_report_url': bill_com_fund_transfer_report_url,
						'bill_com_user_name': bill_com_user_name,
						'bill_com_password': bill_com_password,
						'bill_com_orgid': bill_com_orgid,
						'bill_com_devkey': bill_com_devkey,
						'bill_com_login_url': bill_com_login_url,
						'filter_data':filter_data,
					}
					url = self.env['ir.config_parameter'].sudo().get_param('client_subscription.host_db_url')
					if not url:
						raise UserError("Please Configure Sevice DB URL in General settings.")

					response = requests.post(
						f"{url}/_get_fund_transfer_report_data",
						json=data,
						headers={'Content-Type': 'application/json'},
						verify=False
					)
					print(" >>>>>>>>>>>>>>>>>>>>>>>> response ", response)
					result = response.json()
					_logger.info("_get_fund_transfer_report_data result %s" % result)
					print(" >>>>>>>>>>>>>>>>>>>>>>>> result ", result)
					if result.get('result') and result['result'].get('status') == 'success':
						fund_transfer_data = result['result'].get('data')
						if fund_transfer_data:
							for each_rec in fund_transfer_data:
								cr = self._cr
								batch_name = each_rec.get('name', '')
								processDate = each_rec.get('processDate', '')
								payment_ids = []
								money_movement_items = each_rec.get('moneyMovementItems', '')
								for each_payment_rec in money_movement_items:
									vendor_name = each_payment_rec.get('name', '')
									vendor_name = vendor_name.replace("'", "''")
									cr.execute(
										"""SELECT id from account_payment where vendor_name='%s' and 
											payment_date='%s' and bill_com_payment_id IS NOT NULL
											"""
										% (vendor_name, processDate))
									payment_id = list(filter(None, map(lambda x: x[0], cr.fetchall())))
									if payment_id:
										payment_id_brw = account_payment_obj.browse(payment_id)
										payment_id = payment_id_brw.filtered(lambda l: l.state in ('posted', 'sent') and l.journal_id.id == each_journal_id.id)
										payment_ids += payment_id.ids
								sorted_payment_ids = list(set(payment_ids))
								if sorted_payment_ids:
									payment_obj_brw = account_payment_obj.browse(sorted_payment_ids)
									payment_obj_brw.write({'bill_com_fund_transfer_id': batch_name})
									create_batch = each_config.company_ids.filtered(lambda x: x.create_batch_payment == True)
									if create_batch:
										cr.execute(
											"""select id from account_payment_method 
											where payment_type = 'outbound' and code = 'manual'""")
										payment_method_id = list(filter(None, map(lambda x: x[0], cr.fetchall())))
										# batch_payment_obj.create({
										#     'batch_type': "outbound",
										#     'date': processDate,
										#     'journal_id': each_journal_id.id,
										#     'name': batch_name,
										#     'payment_method_id': payment_method_id[0] if payment_method_id else 2,
										#     'payment_ids': sorted_payment_ids
										# })

	def get_fund_transfer_report_data(self):
		journal_obj = self.env['account.journal']
		account_payment_obj = self.env['account.payment']
		# batch_payment_obj = self.env['account.batch.payment']
		for each_config in self:
			if each_config.state == 'expired':
				raise ValidationError('Can not Import Payment Batch as your subscription expired.')
			else:
				if not each_config.import_from_date:
					raise UserError(_("Please Enter From Date"))
				import_from_date = each_config.import_from_date
				import_to_date = each_config.import_to_date
				if not import_to_date:
					import_to_date = fields.Date.today()
				if import_from_date and import_to_date:
					import_from_date = fields.Date.to_string(import_from_date)
					import_to_date = fields.Date.to_string(import_to_date)
					if import_from_date > import_to_date:
						raise ValidationError(_('To Date cannot be set before From Date.'))
				bill_com_fund_transfer_report_url = each_config.bill_com_fund_transfer_report_url
				bill_com_user_name = each_config.bill_com_user_name
				bill_com_password = each_config.bill_com_password
				bill_com_orgid = each_config.bill_com_orgid
				bill_com_devkey = each_config.bill_com_devkey
				bill_com_login_url = each_config.bill_com_login_url
				for each_company_id in each_config.company_ids:
					bank_journal_ids = journal_obj.search([('company_id', '=', each_company_id.id),
														   ('bank_account_id', '!=', False),
														   ('bank_account_id.bill_com_organization_bank_account_id', '!=',
															False)])
					for each_journal in bank_journal_ids:
						journal_bank_org_id = each_journal.bank_account_id.bill_com_organization_bank_account_id
						if journal_bank_org_id:
							import_to_date = import_to_date if import_to_date else fields.Date.to_string(
								fields.Date.today())
							filter_data = {"start": 0, "max": 999,
										   "filters": [{"field": "status", "op": "=", "value": "1"},
													   {"field": "type", "op": "=", "value": "1"},
													   {"field": "bankAccountId", "op": "=", "value": journal_bank_org_id},
													   {"field": "processDate", "op": ">=", "value": import_from_date},
													   {"field": "processDate", "op": "<=", "value": import_to_date}]}
							# bill_com_service_obj = BillComService(bill_com_user_name, bill_com_password, bill_com_orgid,
							# 									  bill_com_devkey, bill_com_login_url)
							# filter_data = json.dumps(filter_data)
							# fund_transfer_data = bill_com_service_obj.import_fund_transfer_report_data(
							# 	bill_com_fund_transfer_report_url, filter_data)
							data = {
								'bill_com_fund_transfer_report_url': bill_com_fund_transfer_report_url,
								'bill_com_user_name': bill_com_user_name,
								'bill_com_password': bill_com_password,
								'bill_com_orgid': bill_com_orgid,
								'bill_com_devkey': bill_com_devkey,
								'bill_com_login_url': bill_com_login_url,
								'filter_data':filter_data,
							}
							url = self.env['ir.config_parameter'].sudo().get_param('client_subscription.host_db_url')
							if not url:
								raise UserError("Please Configure Sevice DB URL in General settings.")

							response = requests.post(
								f"{url}/_get_fund_transfer_report_data",
								json=data,
								headers={'Content-Type': 'application/json'},
								verify=False
							)
							print(" >>>>>>>>>>>>>>>>>>>>>>>> response ", response)
							result = response.json()
							_logger.info("get_fund_transfer_report_data result %s" % result)
							print(" >>>>>>>>>>>>>>>>>>>>>>>> result ", result)
							if result.get('result') and result['result'].get('status') == 'success':
								fund_transfer_data = result['result'].get('data')
								if fund_transfer_data:
									for each_rec in fund_transfer_data:
										cr = each_config._cr
										batch_name = each_rec.get('name', '')
										processDate = each_rec.get('processDate', '')
										payment_ids = []
										money_movement_items = each_rec.get('moneyMovementItems', '')
										for each_payment_rec in money_movement_items:
											vendor_name = each_payment_rec.get('name', '')
											vendor_name = vendor_name.replace("'", "''")
											cr.execute("""SELECT id from account_payment where vendor_name='%s' and 
														  payment_date='%s' and bill_com_payment_id IS NOT NULL
														  """
													   % (vendor_name, processDate))
											payment_id = list(filter(None, map(lambda x: x[0], cr.fetchall())))
											if payment_id:
												payment_id_brw = account_payment_obj.browse(payment_id)
												payment_id = payment_id_brw.filtered(lambda l: l.state in ('posted', 'sent') and l.journal_id.id == each_journal.id)
												payment_ids += payment_id.ids
										sorted_payment_ids = list(set(payment_ids))
										if sorted_payment_ids:
											payment_obj_brw = account_payment_obj.browse(sorted_payment_ids)
											payment_obj_brw.write({'bill_com_fund_transfer_id': batch_name})
											create_batch = each_company_id.filtered(lambda x: x.create_batch_payment == True)
											if create_batch:
												cr.execute(
													"""select id from account_payment_method 
													where payment_type = 'outbound' and code = 'manual'""")
												payment_method_id = list(filter(None, map(lambda x: x[0], cr.fetchall())))
												# batch_payment_obj.create({
												#     'batch_type': "outbound",
												#     'date': processDate,
												#     'journal_id': each_journal.id,
												#     'name': batch_name,
												#     'payment_method_id': payment_method_id[0] if payment_method_id else 2,
												#     'payment_ids': sorted_payment_ids
												# })
							else:
								raise UserError(f"Failed to fetch challenge ID: {result['result'].get('message')}")
				each_config.import_from_date = each_config.import_to_date = False

	def import_bill_com_users(self):
		bill_com_users_company_data_obj = self.env['bill.com.users.company.data']
		for each_config in self:
			if each_config.state == 'expired':
				raise ValidationError('Can not Import Users as your subscription expired.')
			else:
				bill_com_users_import_url = each_config.bill_com_users_import_url
				if not bill_com_users_import_url:
					raise ValidationError(_('Missing Users Import URL !'))
				company_ids = each_config.company_ids
				bill_com_user_name = each_config.bill_com_user_name
				bill_com_password = each_config.bill_com_password
				bill_com_orgid = each_config.bill_com_orgid
				bill_com_devkey = each_config.bill_com_devkey
				bill_com_login_url = each_config.bill_com_login_url
				users_data, final_users_data = True, []
				start = 0
				max_range = 999
				while users_data:
					filter_data = {"start": start, "max": max_range}
					data = {
						'bill_com_users_import_url': bill_com_users_import_url,
						'bill_com_user_name': bill_com_user_name,
						'bill_com_password': bill_com_password,
						'bill_com_orgid': bill_com_orgid,
						'bill_com_devkey': bill_com_devkey,
						'bill_com_login_url': bill_com_login_url,
						'filter_data':filter_data,
					}
					url = self.env['ir.config_parameter'].sudo().get_param('client_subscription.host_db_url')
					if not url:
						raise UserError("Please Configure Sevice DB URL in General settings.")

					users_response = requests.post(
						f"{url}/import_bill_com_users",
						json=data,
						headers={'Content-Type': 'application/json'},
						verify=False
					)
					print(" >>>>>>>>>>>>>>>>>>>>>>>> users_response ", users_response)
					result = users_response.json()
					_logger.info("import_bill_com_users result %s" % result)
					print(" >>>>>>>>>>>>>>>>>>>>>>>> result ", result)
					if result.get('result') and result['result'].get('status') == 'success':
						response_users_data = result['result'].get('data')
						print("====================== response_users_data", response_users_data)
						# bill_com_service_obj = BillComService(bill_com_user_name, bill_com_password, bill_com_orgid,
						# 									  bill_com_devkey, bill_com_login_url)
						# filter_data = json.dumps(filter_data)
						# response_users_data = bill_com_service_obj.import_users_data(bill_com_users_import_url, filter_data)
						if response_users_data:
							final_users_data = final_users_data + response_users_data
							start = start + max_range
						else:
							users_data = False
					else:
						raise UserError(f"Failed to fetch challenge ID: {result['result'].get('message')}")
				cr = each_config._cr
				i = 1
				_logger.info('length of Users Data %s' % len(final_users_data))
				print(">>>>>>>>>>>>>>>>>>>>>>>final_users_data", final_users_data)
				users_obj = self.env['res.users']
				for each_vendor_data in final_users_data:
					_logger.info('i value %s' % i)
					user_id = each_vendor_data.get('id')
					print(">>>>>>>>>>>>>>>>>>>>>user_id", user_id)
					if user_id:
						email = each_vendor_data.get('email')
						odoo_user_id_brw = users_obj.search([('login','=', email)])
						print("=================== odoo_user_id_brw", odoo_user_id_brw)
						if odoo_user_id_brw:
							for each_company in company_ids:
								bill_com_user_id = odoo_user_id_brw.get_bill_com_user_id(odoo_user_id_brw, each_company)
								print("======================= bill_com_user_id", bill_com_user_id)
								if not bill_com_user_id:
									print(">>>>>>>>>>>>>>>>>>>>>>>>>>>")
									bill_com_users_company_data_obj.sudo().create({'user_id': odoo_user_id_brw.id,
																					'company_id': each_company.id,
																					'bill_com_user_id': user_id})
									print("---------------------------bill_com_users_company_data_obj", bill_com_users_company_data_obj)
					i = i + 1