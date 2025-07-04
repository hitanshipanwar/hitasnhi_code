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

from odoo.exceptions import ValidationError
from odoo import api, fields, models, _
from odoo.exceptions import UserError
import requests
import json
import logging
import xml.etree.ElementTree as ET
from datetime import date, datetime, timedelta

_logger = logging.getLogger(__name__)

class AccountMove(models.Model):
	_inherit='account.move'

	NAMESPACE = "AnetApi/xml/v1/schema/AnetApiSchema.xsd"

	def create_xml_request(self, authorize_login, authorize_transaction_key, batch_id):
		root = ET.Element("getTransactionListRequest", xmlns=self.NAMESPACE)

		merchant_auth = ET.SubElement(root, "merchantAuthentication")
		ET.SubElement(merchant_auth, "name").text = authorize_login
		ET.SubElement(merchant_auth, "transactionKey").text = authorize_transaction_key

		ET.SubElement(root, "batchId").text = batch_id

		sorting = ET.SubElement(root, "sorting")
		ET.SubElement(sorting, "orderBy").text = "submitTimeUTC"
		ET.SubElement(sorting, "orderDescending").text = "true"

		paging = ET.SubElement(root, "paging")
		ET.SubElement(paging, "limit").text = "100"
		ET.SubElement(paging, "offset").text = "1"

		return ET.tostring(root, encoding="utf-8", method="xml")

	def get_settled_batch_list(self, authorize_login, authorize_transaction_key):
		"""Fetches the list of settled batches from Authorize.Net API"""
		
		url = 'https://api.authorize.net/xml/v1/request.api'
		request_data = {
			"getSettledBatchListRequest": {
				"merchantAuthentication": {
					"name": authorize_login,
					"transactionKey": authorize_transaction_key
				}
			}
		}
		headers = {
			'Content-Type': 'application/json'
		}
		try:
			response = requests.post(url, json=request_data, headers=headers)
			if response.status_code == 200:
				# response_data = response.json()
				response_text = response.content.decode('utf-8-sig')
				response_data = json.loads(response_text)
				batch_list = response_data.get("batchList", [])
				if not batch_list:
					print("No batches found.")
					return []

				return batch_list

			else:
				print(f"Error: {response.status_code}, {response.text}")
				return []

		except requests.exceptions.RequestException as e:
			print(f"Request failed: {e}")
			return []
			
	def get_transaction_list(self):
		_logger.info("Fetching transaction list...")
		clients = self.env['res.client'].sudo().search([])
		is_active = False
		subscription_id = False
		for payment_provider in clients:
			# payment_provider = self.env['res.client'].browse(client)
			_logger.info("******** client id %s" % payment_provider)
			subscription_ids = self.env['subscription.master'].sudo().search([('client_id', '=', payment_provider.id)])
			print('=======================subscription_ids=', subscription_ids)
			for subscription in subscription_ids:
				for service in subscription.subscription_plan_id.service_ids:
					if 'authorize' in (service.service_product_id.name or '').lower() and subscription.state == 'active':
						is_active = True
						subscription_id = subscription
						_logger.info("Subscription ID %s has a service with 'stripe' in its name." % subscription.id)

			print("===========================is_active", is_active)
			print("===========================subscription_id", subscription_id)
			if subscription_id and is_active == True:
				# payment_provider = self.env['res.client'].search([('provider', '=', 'authorize')], limit=1)

				if not payment_provider:
					raise UserError("Authorize.Net payment provider not found.")

				if not payment_provider.authorize_login:
					_logger.info("\n\n Authorize.Net login is not configured.")
					return

				if not payment_provider.authorize_transaction_key:
					_logger.info("\n\n Authorize.Net Transaction Key is not configured.")
					return
 
				authorize_login = payment_provider.authorize_login
				authorize_transaction_key = payment_provider.authorize_transaction_key

				batch_list = self.get_settled_batch_list(authorize_login, authorize_transaction_key)
				for batch in batch_list:
					batch_id = batch.get('batchId')
					if batch_id:
						data = self.create_xml_request(authorize_login, authorize_transaction_key, batch_id)
						# url = 'https://apitest.authorize.net/xml/v1/request.api'
						url = 'https://api.authorize.net/xml/v1/request.api'
						headers = {'Content-Type': 'text/xml'}

						last_update = datetime.now()
						next_update = last_update + timedelta(days=1)

						if payment_provider:
							payment_provider.last_update = last_update
							payment_provider.next_update = next_update

						try:
							response = requests.post(url, data=data, headers=headers)
							response.raise_for_status()
							_logger.info("Response received: %s" % response.text)

							response_hardcode = '''<getTransactionListResponse xmlns="AnetApi/xml/v1/schema/AnetApiSchema.xsd">
				  <messages>
					<resultCode>Ok</resultCode>
					<message>
					  <code>I00001</code>
					  <text>Successful.</text>
					</message>
				  </messages>
				  <transactions>
					<transaction>
					  <transId>121</transId>
					  <submitTimeUTC>2024-06-20</submitTimeUTC>
					  <submitTimeLocal>2024-06-20</submitTimeLocal>
					  <transactionStatus>settledSuccessfully</transactionStatus>
					  <invoice>INV/2024/00009</invoice>
					  <firstName>Ready</firstName>
					  <lastName>Mat</lastName>
					  <amount>280.00</amount>
					  <accountType>Visa</accountType>
					  <accountNumber>XXXX4242</accountNumber>
					  <settleAmount>280.00</settleAmount>
					  <subscription>
						<id>145521</id>
						<payNum>1</payNum>
					  </subscription>
					  <profile>
						<customerProfileId>1806660050</customerProfileId>
						<customerPaymentProfileId>1805324550</customerPaymentProfileId>
					  </profile>
					</transaction>
					<transaction>
					  <transId>121</transId>
					  <submitTimeUTC>2024-06-20</submitTimeUTC>
					  <submitTimeLocal>2024-06-20</submitTimeLocal>
					  <transactionStatus>settledSuccessfully</transactionStatus>
					  <invoice>INV/2024/00008</invoice>
					  <firstName>Deco</firstName>
					  <lastName>Addict</lastName>
					  <amount>420.00</amount>
					  <accountType>Visa</accountType>
					  <accountNumber>XXXX4242</accountNumber>
					  <settleAmount>420.00</settleAmount>
					  <marketType>eCommerce</marketType>
					  <product>Card Not Present</product>
					  <mobileDeviceId>2354578983274523978</mobileDeviceId>
					</transaction>
					<transaction>
					  <transId>12345</transId>
					  <submitTimeUTC>2024-06-20</submitTimeUTC>
					  <submitTimeLocal>2024-06-20</submitTimeLocal>
					  <transactionStatus>settledSuccessfully</transactionStatus>
					  <invoice>INV/2024/00007</invoice>
					  <firstName>Ready</firstName>
					  <lastName>Mat</lastName>
					  <amount>120.00</amount>
					  <accountType>Visa</accountType>
					  <accountNumber>XXXX4242</accountNumber>
					  <settleAmount>120.00</settleAmount>
					  <subscription>
						<id>145521</id>
						<payNum>1</payNum>
					  </subscription>
					  <profile>
						<customerProfileId>1806660050</customerProfileId>
						<customerPaymentProfileId>1805324550</customerPaymentProfileId>
					  </profile>
					</transaction>
				  </transactions>
				  <totalNumInResultSet>2</totalNumInResultSet>
				</getTransactionListResponse>'''

							# Parse the actual response
							# root = ET.fromstring(response_hardcode)
							root = ET.fromstring(response.text)

							result_code = root.find(f'.//{{{self.NAMESPACE}}}resultCode')
							if result_code is None or result_code.text != 'Ok':
								raise UserError("Failed to fetch transactions. Result Code: {}".format(result_code.text if result_code else 'Unknown'))

							transactions = root.findall(f'.//{{{self.NAMESPACE}}}transaction')
							if not transactions:
								_logger.info("No transactions found.")
								return True
							for transaction in transactions:
								
								transaction_id =  transaction.find(f'{{{self.NAMESPACE}}}transId').text if transaction.find(f'{{{self.NAMESPACE}}}transId') is not None else None
								submit_time_utc = transaction.find(f'{{{self.NAMESPACE}}}submitTimeUTC').text if transaction.find(f'{{{self.NAMESPACE}}}submitTimeUTC') is not None else None
								invoice = transaction.find(f'{{{self.NAMESPACE}}}invoice').text if transaction.find(f'{{{self.NAMESPACE}}}invoice') is not None else None
								ref = transaction.find(f'{{{self.NAMESPACE}}}invoiceNumber').text if transaction.find(f'{{{self.NAMESPACE}}}invoiceNumber') is not None else None
								first_name = transaction.find(f'{{{self.NAMESPACE}}}firstName').text if transaction.find(f'{{{self.NAMESPACE}}}firstName') is not None else None
								last_name = transaction.find(f'{{{self.NAMESPACE}}}lastName').text if transaction.find(f'{{{self.NAMESPACE}}}lastName') is not None else None
								amount = float(transaction.find(f'{{{self.NAMESPACE}}}settleAmount').text) if transaction.find(f'{{{self.NAMESPACE}}}settleAmount') is not None else 0.0

								data = {
									'first_name': first_name,
									'last_name': last_name,
									'payment_ref': invoice,
									'ref': ref,
									'date': submit_time_utc,
									'name': invoice,
									'amount': amount,
									'transaction_id': transaction_id,
									'last_update': payment_provider.last_update.strftime('%Y-%m-%d %H:%M:%S'),
									'next_update': payment_provider.next_update.strftime('%Y-%m-%d %H:%M:%S'),
									'authorize_login': payment_provider.authorize_login,
								}
								_logger.info("Sending data: %s" % data)

								try:
									response = requests.post(
										f"{payment_provider.url}/create_statements",
										json=data,
										headers={'Content-Type': 'application/json'},
										verify=False
									)
									if response.status_code == 200:
										result = response.json()
										_logger.info("Result %s" % result)
										if 'status' in result:
											if result.get('status') == 'success':
												_logger.info("Statement Created")
										else:
											error_message = result.get('error', 'Unknown error')
											raise UserError(f"Failed to set credentials on DB2: {error_message}")

								except requests.exceptions.RequestException as e:
									raise UserError(f"DB2 request failed: {str(e)}")

						except requests.exceptions.RequestException as e:
							raise UserError(f"Failed to get the transaction list from Authorize.Net: {str(e)}")
			else:
				# raise ValidationError('%s your Subscription Expired' % payment_provider.name)
				_logger.info('%s your Subscription Expired' % payment_provider.name)