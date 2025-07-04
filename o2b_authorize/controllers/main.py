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
from odoo import http
from odoo.http import request
import json
import requests
import xml.etree.ElementTree as ET
from datetime import date, datetime, timedelta
import logging

_logger = logging.getLogger(__name__)


class ProviderWebhookController(http.Controller):

	# @http.route('/provider_credentials', type='json', auth='public', methods=['POST'], csrf=False)
	@http.route('/provider_credentials', type='http', auth='public', csrf=False)
	def provider_credentials(self):
		try:
			data = json.loads(request.httprequest.data)
			print("Received data in request body:", data)
			
			provider = data.get('provider')
			is_connect = data.get('is_connect')
			# user_id = request.env['res.users'].sudo().search([('login', '=', data.get('login'))])

			# if not user_id:
			# 	user_id = request.env['res.users'].sudo().create({
			# 		'name': data.get('name'),
			# 		'login': data.get('login'),
			# 		'email': data.get('login'),
			# 	})
			
			if not provider:
				return {'error': 'Provider is missing'}

			# Process the rest of the data as needed
			if is_connect:
				if provider == 'authorize':
					client_vals = {
						'name': data.get('name'),
						'url': data.get('url'),
						'authorize_login': data.get('authorize_login'),
						'authorize_transaction_key': data.get('authorize_transaction_key'),
						'authorize_signature_key': data.get('authorize_signature_key'),
						'authorize_client_key': data.get('authorize_client_key'),
						'db_name': data.get('db_name'),
						'db_uid': data.get('db_uid'),
						'db_user': data.get('db_user'),
					}
				
				client = request.env['res.client'].sudo().search([('url', '=', data.get('url'))], limit=1)
				print(">>>>>>>>>>>>>>>>>>>>client", client)
				if client:
					client.sudo().write(client_vals)
					return json.dumps({'status': 'success', 'client_id': client.id})
				else:
					return json.dumps({'status': 'failed', 'message': 'Subscription not found. Please configure Client on Service DB (o2b).'})
					# client = request.env['res.client'].sudo().create(client_vals)
			else:
				if provider == 'authorize':
					client_vals = {
						'authorize_login': False,
						'authorize_transaction_key': False,
						'authorize_signature_key': False,
						'authorize_client_key': False,
					}
				
				client = request.env['res.client'].sudo().search([('url', '=', data.get('url'))], limit=1)
				print(">>>>>>>>>>>>>>>>>>>>client", client)
				if client:
					client.sudo().write(client_vals)
					return json.dumps({'status': 'success', 'client_id': client.id})
				else:
					return json.dumps({'status': 'failed', 'message': 'Subscription not found. Please configure Client on Service DB (o2b).'})
					# client = request.env['res.client'].sudo().create(client_vals)

		except Exception as e:
			return json.dumps({'error': str(e)})

	@http.route('/test_authorize_connection', type='http', auth='public', csrf=False)
	# @http.route('/test_authorize_connection', type='json', auth='public', methods=['POST'], csrf=False)
	def api_test_authorize_connection(self):
		try:
			data = json.loads(request.httprequest.data)
			print("Received data in request body:", data)

			config_vals = {
				'url': data.get('url'),
				'authorize_login': data.get('authorize_login'),
				'authorize_transaction_key': data.get('authorize_transaction_key'),
				'authorize_signature_key': data.get('authorize_signature_key'),
				'authorize_client_key': data.get('authorize_client_key'),
				# 'client_email': data.get('login'),
				# 'client_user_id': data.get('partner_id'),
			}
			print("====================== config_vals", config_vals)
			# client_id = request.env['res.client'].sudo().search([('client_email', '=', data.get('login'))])
			client_id = request.env['res.client'].sudo().search([('url', '=', data.get('url'))])
			if client_id:
				mismatched_fields = []
				for field, value in config_vals.items():
					if getattr(client_id, field, None) != value:
						mismatched_fields.append(field)
				
				if mismatched_fields:
					return json.dumps({
						'status': 'failed',
						'message': f"Connection Failed! Mismatched fields: {', '.join(mismatched_fields)}"
					})
				else:
					return json.dumps({'status': 'success', 'message': 'Connection Successful!'})
			else:
				return json.dumps({'status': 'failed', 'message': 'No matching configuration found.'})
		except Exception as e:
			return json.dumps({'error': str(e), 'message': 'Connection Failed'})

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

	NAMESPACE = "AnetApi/xml/v1/schema/AnetApiSchema.xsd"
	def create_xml_request_trans(self, authorize_login, authorize_transaction_key, transId):
		root = ET.Element("getTransactionDetailsRequest", xmlns=self.NAMESPACE)

		merchant_auth = ET.SubElement(root, "merchantAuthentication")
		ET.SubElement(merchant_auth, "name").text = authorize_login
		ET.SubElement(merchant_auth, "transactionKey").text = authorize_transaction_key

		ET.SubElement(root, "transId").text = str(transId)
		return ET.tostring(root, encoding="utf-8", method="xml")

	def get_settled_batch_list(self, authorize_login, authorize_transaction_key, from_date, to_date):
		"""Fetches the list of settled batches from Authorize.Net API"""
		
		url = 'https://api.authorize.net/xml/v1/request.api'
		to_date = datetime.strptime(to_date, "%Y-%m-%d").replace(
		    hour=23,
		    minute=59,
		    second=59,
		    microsecond=999999
		)
		from_date = datetime.strptime(from_date, "%Y-%m-%d").replace(
		    hour=0,
		    minute=0,
		    second=0,
		    microsecond=0
		)
		end_date = to_date
		start_date = from_date
		_logger.info("Fetching transaction from date...: %s" % start_date)
		_logger.info("Fetching transaction to date...:%s" % end_date)
		request_data = {
			"getSettledBatchListRequest": {
				"merchantAuthentication": {
					"name": authorize_login,
					"transactionKey": authorize_transaction_key
				},
				"firstSettlementDate": start_date.strftime("%Y-%m-%dT%H:%M:%SZ"),
				"lastSettlementDate": end_date.strftime("%Y-%m-%dT%H:%M:%SZ")
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
				_logger.info("Batch Respons %s" % response_data)
				batch_list = response_data.get("batchList", [])
				_logger.info("Batch List %s" % batch_list)
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

	@http.route('/fetch_authorize_net_transactions', type='http', auth='public', csrf=False)
	# @http.route('/fetch_authorize_net_transactions', type='json', auth='public', methods=['POST'], csrf=False)
	def api_fetch_authorize_net_transaction_list(self):
		try:
			data = json.loads(request.httprequest.data)
			_logger.info("Received data in request body: %s" % data)

			authorize_login = data.get('authorize_login')
			authorize_transaction_key = data.get('authorize_transaction_key')
			from_date = data.get('from_date')
			to_date = data.get('to_date')
			batch_list = self.get_settled_batch_list(authorize_login, authorize_transaction_key, from_date, to_date)
			for batch in batch_list:
				batch_id = batch.get('batchId')
				if batch_id:
					xml_data = self.create_xml_request(authorize_login, authorize_transaction_key, batch_id)

					url = 'https://api.authorize.net/xml/v1/request.api'
					headers = {'Content-Type': 'text/xml'}

					try:
						# Send XML request to Authorize.Net API
						response = requests.post(url, data=xml_data, headers=headers)
						response.raise_for_status()

						_logger.info("Response received: %s" % response.text)

						# Simulated Response (for testing purposes)
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

						# Parse the actual response (can be switched with the real response)
						# root = ET.fromstring(response_hardcode)
						root = ET.fromstring(response.text)
						result_code = root.find(f'.//{{{self.NAMESPACE}}}resultCode')

						if result_code is None or result_code.text != 'Ok':
							raise UserError("Failed to fetch transactions. Result Code: {}".format(result_code.text if result_code else 'Unknown'))

						transactions = root.findall(f'.//{{{self.NAMESPACE}}}transaction')
						if not transactions:
							_logger.info("No transactions found.")
							return True

						# Return transactions
						transaction_data = []
						for transaction in transactions:
							transId = transaction.find(f'{{{self.NAMESPACE}}}transId').text if transaction.find(f'{{{self.NAMESPACE}}}transId') is not None else None
							if transId:
								xml_data = self.create_xml_request_trans(authorize_login, authorize_transaction_key, transId)

								url = 'https://api.authorize.net/xml/v1/request.api'
								headers = {'Content-Type': 'text/xml'}
								# Send XML request to Authorize.Net API
								response = requests.post(url, data=xml_data, headers=headers)
								response.raise_for_status()
								_logger.info("Response transaction_details received: %s" % response.text)
								detail_root = ET.fromstring(response.text)
								result_code = detail_root.find(f'.//{{{self.NAMESPACE}}}resultCode')

								if result_code is None or result_code.text != 'Ok':
									raise UserError("Failed to fetch transactions. Result Code: {}".format(result_code.text if result_code else 'Unknown'))

								def get_float(el, tag):
									val = el.find(f'{{{self.NAMESPACE}}}{tag}')
									try:
										return float(val.text) if val is not None else 0.0
									except ValueError:
										return 0.0

								detail_transaction = detail_root.find(f'.//{{{self.NAMESPACE}}}transaction')
								transactionStatus = detail_transaction.find(f'{{{self.NAMESPACE}}}transactionStatus').text if detail_transaction.find(f'{{{self.NAMESPACE}}}transactionStatus') is not None else None
								_logger.info("Response transaction_details transactionStatus: %s" % transactionStatus)
								if transactionStatus == 'settledSuccessfully':
									transrefId = detail_root.find(f'.//{{{self.NAMESPACE}}}transrefId').text if detail_root.find(f'.//{{{self.NAMESPACE}}}transrefId') is not None else None
									if transrefId:
										transrefId = transaction.find(f'{{{self.NAMESPACE}}}invoiceNumber').text if transaction.find(f'{{{self.NAMESPACE}}}invoiceNumber') is not None else None
									transaction_data.append({
										'transId': transaction.find(f'{{{self.NAMESPACE}}}transId').text if transaction.find(f'{{{self.NAMESPACE}}}transId') is not None else None,
										'submitTimeUTC': transaction.find(f'{{{self.NAMESPACE}}}submitTimeUTC').text if transaction.find(f'{{{self.NAMESPACE}}}submitTimeUTC') is not None else None,
										'invoice': transaction.find(f'{{{self.NAMESPACE}}}invoice').text if transaction.find(f'{{{self.NAMESPACE}}}invoice') is not None else None,
										'ref': transrefId,
										'firstName': transaction.find(f'{{{self.NAMESPACE}}}firstName').text if transaction.find(f'{{{self.NAMESPACE}}}firstName') is not None else None,
										'lastName': transaction.find(f'{{{self.NAMESPACE}}}lastName').text if transaction.find(f'{{{self.NAMESPACE}}}lastName') is not None else None,
										'amount': get_float(detail_transaction, 'settleAmount'),
										'transactionStatus': transaction.find(f'{{{self.NAMESPACE}}}transactionStatus').text if transaction.find(f'{{{self.NAMESPACE}}}transactionStatus') is not None else None
									})
								elif transactionStatus == 'refundSettledSuccessfully':
									transrefId = detail_transaction.find(f'{{{self.NAMESPACE}}}networkTransId').text if detail_transaction.find(f'{{{self.NAMESPACE}}}networkTransId') is not None else None
									_logger.info("transrefId %s" % transrefId)
									amount = get_float(detail_transaction, 'settleAmount')
									transaction_data.append({
										'transId': transaction.find(f'{{{self.NAMESPACE}}}transId').text if transaction.find(f'{{{self.NAMESPACE}}}transId') is not None else None,
										'submitTimeUTC': transaction.find(f'{{{self.NAMESPACE}}}submitTimeUTC').text if transaction.find(f'{{{self.NAMESPACE}}}submitTimeUTC') is not None else None,
										'invoice': transaction.find(f'{{{self.NAMESPACE}}}invoice').text if transaction.find(f'{{{self.NAMESPACE}}}invoice') is not None else None,
										'ref': transrefId,
										'firstName': transaction.find(f'{{{self.NAMESPACE}}}firstName').text if transaction.find(f'{{{self.NAMESPACE}}}firstName') is not None else None,
										'lastName': transaction.find(f'{{{self.NAMESPACE}}}lastName').text if transaction.find(f'{{{self.NAMESPACE}}}lastName') is not None else None,
										'amount': -amount,
										'transactionStatus': transaction.find(f'{{{self.NAMESPACE}}}transactionStatus').text if transaction.find(f'{{{self.NAMESPACE}}}transactionStatus') is not None else None
									})

						return json.dumps({'status': 'success', 'transactions': transaction_data})

					except requests.exceptions.RequestException as e:
						return json.dumps({'error': str(e), 'message': 'Connection Failed'})

		except Exception as e:
			return json.dumps({'error': str(e), 'message': 'Connection Failed'})