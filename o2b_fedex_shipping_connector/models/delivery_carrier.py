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
from odoo.exceptions import ValidationError, UserError
import requests
import xml.etree.ElementTree as ET
import logging
import json
import certifi
import base64
import re
from PyPDF2 import PdfFileMerger
from io import BytesIO
import time

_logger = logging.getLogger(__name__)

# Why using standardized ISO codes? It's way more fun to use made up codes...
# https://www.fedex.com/us/developer/WebHelp/ws/2014/dvg/WS_DVG_WebHelp/Appendix_F_Currency_Codes.htm
FEDEX_CURR_MATCH = {
	u'UYU': u'UYP',
	u'XCD': u'ECD',
	u'MXN': u'NMP',
	u'KYD': u'CID',
	u'CHF': u'SFR',
	u'GBP': u'UKL',
	u'IDR': u'RPA',
	u'DOP': u'RDD',
	u'JPY': u'JYE',
	u'KRW': u'WON',
	u'SGD': u'SID',
	u'CLP': u'CHP',
	u'JMD': u'JAD',
	u'KWD': u'KUD',
	u'AED': u'DHS',
	u'TWD': u'NTD',
	u'ARS': u'ARN',
	u'LVL': u'EURO',
}

FEDEX_REST_STOCK_TYPE = [
	('PAPER_4X6', 'PAPER_4X6'),
	('PAPER_4X675', 'PAPER_4X675'),
	('PAPER_4X8', 'PAPER_4X8'),
	('PAPER_4X9', 'PAPER_4X9'),
	('PAPER_7X475', 'PAPER_7X475'),
	('PAPER_85X11_BOTTOM_HALF_LABEL', 'PAPER_85X11_BOTTOM_HALF_LABEL'),
	('PAPER_85X11_TOP_HALF_LABEL', 'PAPER_85X11_TOP_HALF_LABEL'),
	('PAPER_LETTER', 'PAPER_LETTER'),
	('STOCK_4X6', 'STOCK_4X6'),
	('STOCK_4X675', 'STOCK_4X675'),
	('STOCK_4X675_LEADING_DOC_TAB', 'STOCK_4X675_LEADING_DOC_TAB'),
	('STOCK_4X675_TRAILING_DOC_TAB', 'STOCK_4X675_TRAILING_DOC_TAB'),
	('STOCK_4X8', 'STOCK_4X8'),
	('STOCK_4X9', 'STOCK_4X9'),
	('STOCK_4X9_LEADING_DOC_TAB', 'STOCK_4X9_LEADING_DOC_TAB'),
	('STOCK_4X9_TRAILING_DOC_TAB', 'STOCK_4X9_TRAILING_DOC_TAB')
]

HELP_EXTRA_DATA = """The extra data in FedEx is organized like the inside of a json file.
This functionality is advanced/technical and should only be used if you know what you are doing.

Example of valid value: ```
"ShipmentDetails": {"Pieces": {"Piece": {"AdditionalInformation": "extra info"}}}
```

With the above example, the AdditionalInformation of each piece will be updated.
More info on https://www.fedex.com/en-us/developer/web-services/process.html#documentation"""


class ProviderFedex(models.Model):
	_inherit = 'delivery.carrier'

	delivery_type = fields.Selection(selection_add=[
		('fedex_rest', "FedEx REST")
	], ondelete={'fedex_rest': lambda recs: recs.write({'delivery_type': 'fixed', 'fixed_price': 0})})

	fedex_developer_key = fields.Char(string="Developer Key")
	fedex_developer_password = fields.Char(string="Password")
	fedex_account_number = fields.Char(string="FedEx Account Number")
	fedex_meter_number = fields.Char(string="Meter Number")
	fedex_droppoff_type = fields.Selection([('BUSINESS_SERVICE_CENTER', 'BUSINESS_SERVICE_CENTER'),
											('DROP_BOX', 'DROP_BOX'),
											('REGULAR_PICKUP', 'REGULAR_PICKUP'),
											('REQUEST_COURIER', 'REQUEST_COURIER'),
											('STATION', 'STATION')],
										   string="Fedex Drop-Off Type",
										   default='REGULAR_PICKUP')
	fedex_default_package_type_id = fields.Many2one('stock.package.type', string="Fedex Package Type")
	fedex_service_type = fields.Selection([('INTERNATIONAL_ECONOMY', 'INTERNATIONAL_ECONOMY'),
										   ('INTERNATIONAL_PRIORITY', 'INTERNATIONAL_PRIORITY'),
										   ('FEDEX_INTERNATIONAL_PRIORITY', 'FEDEX_INTERNATIONAL_PRIORITY'),
										   ('FEDEX_INTERNATIONAL_PRIORITY_EXPRESS', 'FEDEX_INTERNATIONAL_PRIORITY_EXPRESS'),
										   ('FEDEX_GROUND', 'FEDEX_GROUND'),
										   ('FEDEX_2_DAY', 'FEDEX_2_DAY'),
										   ('FEDEX_2_DAY_AM', 'FEDEX_2_DAY_AM'),
										   ('FEDEX_3_DAY_FREIGHT', 'FEDEX_3_DAY_FREIGHT'),
										   ('FIRST_OVERNIGHT', 'FIRST_OVERNIGHT'),
										   ('PRIORITY_OVERNIGHT', 'PRIORITY_OVERNIGHT'),
										   ('STANDARD_OVERNIGHT', 'STANDARD_OVERNIGHT'),
										   ('FEDEX_NEXT_DAY_EARLY_MORNING', 'FEDEX_NEXT_DAY_EARLY_MORNING'),
										   ('FEDEX_NEXT_DAY_MID_MORNING', 'FEDEX_NEXT_DAY_MID_MORNING'),
										   ('FEDEX_NEXT_DAY_AFTERNOON', 'FEDEX_NEXT_DAY_AFTERNOON'),
										   ('FEDEX_NEXT_DAY_END_OF_DAY', 'FEDEX_NEXT_DAY_END_OF_DAY'),
										   ('FEDEX_EXPRESS_SAVER', 'FEDEX_EXPRESS_SAVER'),
										   ('FEDEX_REGIONAL_ECONOMY', 'FEDEX_REGIONAL_ECONOMY'),
										   ],
										  default='FEDEX_INTERNATIONAL_PRIORITY')
	fedex_duty_payment = fields.Selection([('SENDER', 'Sender'), ('RECIPIENT', 'Recipient')], required=True, default="SENDER")
	fedex_weight_unit = fields.Selection([('LB', 'LB'),
										  ('KG', 'KG')],
										 default='LB')
	# Note about weight units: Odoo (v9) currently works with kilograms.
	# --> Gross weight of each products are expressed in kilograms.
	# For some services, FedEx requires weights expressed in pounds, so we
	# convert them when necessary.
	fedex_rest_label_stock_type = fields.Selection(FEDEX_REST_STOCK_TYPE, string='Label Type', default='PAPER_LETTER')
	fedex_label_file_type = fields.Selection([('PDF', 'PDF'),
											  ('EPL2', 'EPL2'),
											  ('PNG', 'PNG'),
											  ('ZPLII', 'ZPLII')],
											 default='PDF', string="FEDEX Label File Type")
	fedex_document_stock_type = fields.Selection(FEDEX_REST_STOCK_TYPE, string='Commercial Invoice Type', default='PAPER_LETTER')
	fedex_saturday_delivery = fields.Boolean(string="FedEx Saturday Delivery", help="""Special service:Saturday Delivery, can be requested on following days.
																				 Thursday:\n1.FEDEX_2_DAY.\nFriday:\n1.PRIORITY_OVERNIGHT.\n2.FIRST_OVERNIGHT.
																				 3.INTERNATIONAL_PRIORITY.\n(To Select Countries)""")
	fedex_extra_data_rate_request = fields.Text('Extra data for rate', help=HELP_EXTRA_DATA)
	fedex_extra_data_ship_request = fields.Text('Extra data for ship', help=HELP_EXTRA_DATA)
	fedex_extra_data_return_request = fields.Text('Extra data for return', help=HELP_EXTRA_DATA)
	fedex_cliet_key = fields.Char(string="API key")
	fedex_cliet_secret_key = fields.Char(string="API Secret Key")



	def get_fedex_oauth_token(self):
		self = self.sudo()
		if self.prod_environment == True:
			token_url = "https://apis.fedex.com/oauth/token"
		else:
			token_url = "https://apis-sandbox.fedex.com/oauth/token"
		client_id = self.fedex_cliet_key
		client_secret = self.fedex_cliet_secret_key

		payload = {
			'grant_type': 'client_credentials',
			'client_id': client_id,
			'client_secret': client_secret
		}

		headers = {
			'Content-Type': 'application/x-www-form-urlencoded'
		}

		response = requests.post(token_url, data=payload, headers=headers, verify=certifi.where())
		_logger.info("FedEx OAuth Token Response Status Code: %s", response.status_code)
		_logger.info("FedEx OAuth Token Response: %s", response.text)

		if response.status_code == 200:
			return response.json().get('access_token')
		else:
			raise ValidationError(_("Failed to retrieve FedEx OAuth token. Please check your credentials."))

	def fedex_get_shipping_rate(self, order):
		self = self.sudo()
		if self.prod_environment == True:
			url = 'https://apis.fedex.com/rate/v1/rates/quotes'
		else:
			url = 'https://apis-sandbox.fedex.com/rate/v1/rates/quotes'
		oauth_token = self.get_fedex_oauth_token()

		headers = {
			'Content-Type': 'application/json',
			'Authorization': f"Bearer {oauth_token}",
		}

		packages_ids = self.env.context.get('packages', [])
		_logger.info("Request Data packages::::%s" % packages_ids)
		packages = []
		total_weight_in = 0
		if not len(packages_ids):
			weight = sum(
				[(line.product_id.weight * line.product_uom_qty) for line in order.order_line if not line.is_delivery])
			weight_limit = 150
			pieces = []
			while weight > weight_limit:
				pieces.append(weight_limit)
				weight -= weight_limit
			if weight > 0:
				pieces.append(weight)
			for line in pieces:
				weight = line
				length = self.fedex_default_package_type_id.packaging_length if self.fedex_default_package_type_id and self.fedex_default_package_type_id.packaging_length else "1"
				width = self.fedex_default_package_type_id.width if self.fedex_default_package_type_id and self.fedex_default_package_type_id.width else "1"
				height = self.fedex_default_package_type_id.height if self.fedex_default_package_type_id and self.fedex_default_package_type_id.height else "1"
				packages.append({
						"weight": {
							"units": self.fedex_weight_unit,
							"value": str(weight)
						},
						"dimensions": {
							"length": length,
							"width": width,
							"height": height,
							"units": "IN" if self.fedex_weight_unit == 'LB' else "CM"
						}
					})
				total_weight_in += weight
		else:
			for line in packages_ids:
				weight = line.shipping_weight
				length = (
					line.package_type_id.packaging_length 
					if line.package_type_id and line.package_type_id.packaging_length 
					else (
						self.fedex_default_package_type_id.packaging_length 
						if self.fedex_default_package_type_id and self.fedex_default_package_type_id.packaging_length 
						else "1"
					)
				)
				width = (
					line.package_type_id.width 
					if line.package_type_id and line.package_type_id.width 
					else (
						self.fedex_default_package_type_id.width 
						if self.fedex_default_package_type_id and self.fedex_default_package_type_id.width 
						else "1"
					)
				)
				height = (
					line.package_type_id.height 
					if line.package_type_id and line.package_type_id.height 
					else (
						self.fedex_default_package_type_id.height 
						if self.fedex_default_package_type_id and self.fedex_default_package_type_id.height 
						else "1"
					)
				)
				packages.append({
						"weight": {
							"units": self.fedex_weight_unit,
							"value": str(weight)
						},
						"dimensions": {
							"length": length,
							"width": width,
							"height": height,
							"units": "IN" if self.fedex_weight_unit == 'LB' else "CM"
						}
					})
				total_weight_in += weight

		payload = {
			"accountNumber": {
				"value": self.sudo().fedex_account_number
			},
			"requestedShipment": {
				"shipper": {
					"address": {
						"postalCode": order.warehouse_id.partner_id.zip,
						"countryCode": order.warehouse_id.partner_id.country_id.code,
						"city": order.warehouse_id.partner_id.city,
						"stateOrProvinceCode": order.warehouse_id.partner_id.state_id.code
					}
				},
				"recipient": {
					"address": {
						"postalCode": order.partner_shipping_id.zip,
						"countryCode": order.partner_shipping_id.country_id.code,
						"city": order.partner_shipping_id.city,
						"stateOrProvinceCode": order.partner_shipping_id.state_id.code
					}
				},
				"pickupType": "DROPOFF_AT_FEDEX_LOCATION",
				"rateRequestType": [
					  "ACCOUNT",
					  "LIST"
					],
				"serviceType": self.fedex_service_type,
				"packagingType": self.fedex_default_package_type_id.shipper_package_code,
				"totalPackageCount": len(packages),
				"totalWeight": total_weight_in,
				"requestedPackageLineItems":packages
			}
		}
		response = requests.post(url, headers=headers, json=payload)
		if response.status_code == 200:
			response_json = response.json()
			print("FedEx Response JSON:", response_json)

			try:
				# rate = response_json['output']['rateReplyDetails'][0]['ratedShipmentDetails'][0]['shipmentRateDetail']['totalNetCharge']['amount']
				rate = response_json['output']['rateReplyDetails'][0]['ratedShipmentDetails'][0]['totalNetFedExCharge']
				return rate
			except KeyError as e:
				raise UserError(f"Failed to parse rate from FedEx response. Missing key: {e}. Full response: {response_json}")
		else:
			error_message = response.json().get('errors', [{'message': 'Unknown message'}])[0]['message']
			code = response.json().get('errors', [{'code': 'Unknown code'}])[0]['code']
			error_message = str(code) + ' ' + str(error_message)
			raise UserError(f"Failed to get rate from FedEx: {error_message}")

	def extract_last_10_digits(self, phone_number):
		cleaned_phone_number = re.sub(r'\D', '', phone_number)
		last_10_digits = cleaned_phone_number[-10:]
		return last_10_digits


	def fedex_create_shipment(self, picking, order):
		self = self.sudo()
		oauth_token = self.get_fedex_oauth_token()

		if self.prod_environment == True:
			url = 'https://apis.fedex.com/ship/v1/shipments'
		else:
			url = 'https://apis-sandbox.fedex.com/ship/v1/shipments'

		headers = {
			'Content-Type': 'application/json',
			'Authorization': f"Bearer {oauth_token}",
		}
		ship_date = order.date_order.strftime('%Y-%m-%d')
		has_package = any(line.result_package_id for line in picking.move_line_ids_without_package)
		if not has_package:
			labels = []
			streetLinesRecipients = ' '.join(filter(None, [picking.partner_id.street, picking.partner_id.street2]))
			resp_company_name = picking.partner_id.company_name if picking.partner_id.company_name else ''
			if not resp_company_name:
				resp_company_name = picking.partner_id.parent_id.name if picking.partner_id.parent_id else picking.partner_id.name
			_logger.info("FedEx resp_company_name: %s", resp_company_name)
			total_weight = sum(
				[(line.product_id.weight * line.product_uom_qty) for line in picking.move_line_ids_without_package])
			payload = {
				"labelResponseOptions": 'LABEL',
				"requestedShipment": {
					"shipper": {
						"contact": {
							"personName": order.warehouse_id.partner_id.name,
							"companyName": order.company_id.name,
							"phoneNumber": self.extract_last_10_digits(order.warehouse_id.partner_id.phone) if order.warehouse_id.partner_id.phone else ''
						},
						"address": {
							"streetLines": [
								order.warehouse_id.partner_id.street or "",
								order.warehouse_id.partner_id.street2 or ""
							],
							"city": order.warehouse_id.partner_id.city or "",
							"stateOrProvinceCode": order.warehouse_id.partner_id.state_id.code or "",
							"postalCode": str(order.warehouse_id.partner_id.zip) or "",
							"countryCode": order.warehouse_id.partner_id.country_id.code or ""
						}
					},
					"recipients": [
						{
							"contact": {
								"personName": picking.partner_id.name,
								"phoneNumber": self.extract_last_10_digits(picking.partner_id.phone) if picking.partner_id.phone else '',
								"companyName": resp_company_name
							},
							"address": {
								"streetLines": [
									streetLinesRecipients or "",
									picking.partner_id.street2 or ""
								],
								"city": picking.partner_id.city or "",
								"stateOrProvinceCode": picking.partner_id.state_id.code or "",
								"postalCode": str(picking.partner_id.zip) or "",
								"countryCode": picking.partner_id.country_id.code or ""
							}
						}
					],
					"shipDatestamp": ship_date,
					"serviceType": self.fedex_service_type,
					"packagingType": self.fedex_default_package_type_id.shipper_package_code,
					"pickupType": "USE_SCHEDULED_PICKUP",
					"blockInsightVisibility": None,
					"shippingChargesPayment": {
						"paymentType": self.fedex_duty_payment
					},
					"shipmentSpecialServices": {
						"specialServiceTypes": [
							self.fedex_service_type
						]
					},
					"labelSpecification": {
						"imageType": self.fedex_label_file_type,
						"labelStockType": self.fedex_rest_label_stock_type
					},
					"totalWeight": total_weight,
					"requestedPackageLineItems": [
						{ }
					]
				},
				"accountNumber": {
					"value": self.sudo().fedex_account_number
				}
			}
			print("FedEx API Payload (Blank Package):", json.dumps(payload, indent=4))
			response = requests.post(url, headers=headers, json=payload)
			print("FedEx API Response:", response.status_code, response.text)
			_logger.info("Label Response 00 Data  : %s" % response.content)
			_logger.info("Label Response 00 Status  : %s" % response.status_code)
			if response.status_code == 200:
				try:
					response_json = response.json()
					tracking_number = response_json['output']['transactionShipments'][0]['masterTrackingNumber']
					carrier_price = response_json['output']['transactionShipments'][0]['completedShipmentDetail']['shipmentRating']['shipmentRateDetails'][0]['totalNetFedExCharge']
					package_documents = response_json['output']['transactionShipments'][0]['pieceResponses'][0]['packageDocuments'][0]

					if 'encodedLabel' in package_documents:
						label = package_documents['encodedLabel']
					else:
						label_url = package_documents['url']
						label = f"Label URL: {label_url}"
					labels.append(label)
					return tracking_number, label, carrier_price
				except KeyError as e:
					raise UserError(f"Failed to parse label from FedEx response. Missing key: {e}. Full response: {response_json}")
				else:
					error_message = response.json().get('errors', [{'message': 'Unknown error'}])[0]['message']
					raise UserError(f"Failed to generate label from FedEx: {error_message}")
			else:
				error_message = response.json().get('errors', [{'message': 'Unknown error'}])[0]['message']
				code = response.json().get('errors', [{'code': 'Unknown code'}])[0]['code']
				error_message = str(code) + ' ' + str(error_message)
				raise UserError(f"Failed to generate label from FedEx: {error_message}")
		else:
			tracking_numbers = []
			labels = []
			carrier_price = 0
			streetLinesRecipients = ' '.join(filter(None, [picking.partner_id.street, picking.partner_id.street2]))
			package_list = []

			move_lines = picking.move_line_ids_without_package.filtered(lambda l: l.qty_done != 0.00)
			package_data = {}
			for line in move_lines:
				package_id = line.result_package_id.id
				if package_id not in package_data:
					package_data[package_id] = {
						"weight": 0.0,
						"declared_value": 0.0,
					}

				package_data[package_id]["weight"] += line.product_id.weight * line.qty_done
				package_data[package_id]["declared_value"] += line.product_id.list_price * line.qty_done
			sequenceNumber = 1
			total_weight = 0
			for package in picking.move_line_ids_without_package.mapped('result_package_id'):
				package = {
					"groupPackageCount": 1,
					"sequenceNumber": str(sequenceNumber),
					"weight": {
						"value": package.shipping_weight,
						"units": self.fedex_weight_unit
					},
					"declaredValue": {
						"amount": package_data.get(package.id).get('declared_value'),
						"currency": order.currency_id.name
					}
				}
				total_weight += package['weight']['value']
				sequenceNumber = sequenceNumber + 1
				package_list.append(package)
			# for packagedict in package_list:
			resp_company_name = picking.partner_id.company_name if picking.partner_id.company_name else ''
			if not resp_company_name:
				resp_company_name = picking.partner_id.parent_id.name if picking.partner_id.parent_id else picking.partner_id.name
			_logger.info("FedEx resp_company_name: %s", resp_company_name)
			payload = {
				"labelResponseOptions": "LABEL",
				"requestedShipment": {
					"serviceType": self.fedex_service_type,
					"shipper": {
						"address": {
							"city": order.warehouse_id.partner_id.city or "",
							"countryCode": order.warehouse_id.partner_id.country_id.code or "",
							"streetLines": [
								order.warehouse_id.partner_id.street or "",
								order.warehouse_id.partner_id.street2 or ""
							],
							"postalCode": order.warehouse_id.partner_id.zip or "",
							"stateOrProvinceCode": order.warehouse_id.partner_id.state_id.code or ""
						},
						"contact": {
							"personName": order.warehouse_id.partner_id.name,
							"emailAddress": order.warehouse_id.partner_id.email,
							"phoneNumber": self.extract_last_10_digits(order.warehouse_id.partner_id.phone) if order.warehouse_id.partner_id.phone else '',
							"companyName": order.company_id.name
						}
					},
					"recipients": [
						{
							"contact": {
								"personName": picking.partner_id.name,
								"phoneNumber": self.extract_last_10_digits(picking.partner_id.phone) if picking.partner_id.phone else '',
								"companyName": resp_company_name
							},
							"address": {
								"city": picking.partner_id.city or "",
								"stateOrProvinceCode": picking.partner_id.state_id.code or "",
								"postalCode": picking.partner_id.zip or "",
								"countryCode": picking.partner_id.country_id.code or "",
								"streetLines": [
									streetLinesRecipients or "",
									picking.partner_id.street2 or ""
								]
							}
						}
					],
					"rateRequestType": ["LIST"],
					"labelSpecification": {
						"imageType": self.fedex_label_file_type,
						"labelFormatType": "COMMON2D",
						"labelStockType": self.fedex_rest_label_stock_type,
						"labelPrintingOrientation": "TOP_EDGE_OF_TEXT_FIRST"
					},
					"shipDatestamp": ship_date,
					"pickupType": "USE_SCHEDULED_PICKUP",
					"shippingChargesPayment": {
						"paymentType": self.fedex_duty_payment
					},
					"packagingType": self.fedex_default_package_type_id.shipper_package_code,
					"totalPackageCount": len(package_list),
					"totalWeight": total_weight,
					"requestedPackageLineItems": package_list
				},
				"accountNumber": {
					"value": self.sudo().fedex_account_number
				}
			}

			print("FedEx API Payload:", json.dumps(payload, indent=4))
			_logger.info("FedEx API Payload  : %s" % json.dumps(payload, indent=4))
			response = requests.post(url, headers=headers, json=payload)
			print("FedEx API Response:", response.status_code, response.text)
			_logger.info("FedEx API Response  : %s" % response.text)

			if response.status_code == 200:
				try:
					response_json = response.json()
					transaction_shipments = response_json['output']['transactionShipments']
					carrier_price = response_json['output']['transactionShipments'][0]['completedShipmentDetail']['shipmentRating']['shipmentRateDetails'][0]['totalNetFedExCharge']
					for shipment in transaction_shipments:
						piece_responses = shipment['pieceResponses']
						for piece_response in piece_responses:
							package_documents = piece_response['packageDocuments']
							for document in package_documents:
								tracking_number = piece_response['trackingNumber']
								if 'encodedLabel' in document:
									label = document['encodedLabel']
								else:
									label_url = document.get('url', 'No URL available')
									label = f"Label URL: {label_url}"
								tracking_numbers.append(tracking_number)
								labels.append(label)
				except KeyError as e:
					raise UserError(f"Failed to parse label from FedEx response. Missing key: {e}. Full response: {response_json}")
			else:
				error_message = response.json().get('errors', [{'message': 'Unknown error'}])[0]['message']
				code = response.json().get('errors', [{'code': 'Unknown code'}])[0]['code']
				error_message = str(code) + ' ' + str(error_message)
				raise UserError(f"Failed to generate label from FedEx: {error_message}")

		# Combine labels into a single PDF
		if labels:
			merger = PdfFileMerger()
			zpl_files_content = []
			_logger.info("Fedex Labels : %s" % labels)
			for label in labels:
				if label.startswith("Label URL:"):
					label_url = label.replace("Label URL: ", "")
					time.sleep(5)
					label_response = requests.get(label_url)
					_logger.info("Label Response Data  : %s" % label_response.content)
					_logger.info("Label Response Status  : %s" % label_response.status_code)
					if label_response.status_code == 200:
						label_content = label_response.content
						if self.fedex_label_file_type == "ZPLII":
							label_content = base64.b64decode(label)
							zpl_files_content.append(label_content)
						else:
							temp_file_path = f"/tmp/label_{tracking_numbers[labels.index(label)]}.pdf"
							with open(temp_file_path, "wb") as f:
								f.write(label_content)
							merger.append(temp_file_path)
					# else:
					#   raise UserError(f"Failed to fetch label from URL. Status code: {label_response.status_code}")
				else:
					label = label + '=' * (-len(label) % 4)  # Ensure correct padding for Base64
					if self.fedex_label_file_type == "ZPLII":
						label_content = base64.b64decode(label)
						zpl_files_content.append(label_content)
					else:
						label_content = base64.b64decode(label)
						temp_file_path = f"/tmp/label_{tracking_numbers[labels.index(label)]}.pdf"
						with open(temp_file_path, "wb") as f:
							f.write(label_content)
						merger.append(temp_file_path)

			if self.fedex_label_file_type == "ZPLII":
				output_zpl_path = "/tmp/FedexLabels.zpl"
				with open(output_zpl_path, "wb") as f:
					for zpl_content in zpl_files_content:
						f.write(zpl_content)
						f.write(b'\n')  # Add a newline to separate ZPL commands

				print(f"Output ZPL path: {output_zpl_path}")
				return tracking_numbers, output_zpl_path, carrier_price

			else:
				output_pdf_path = "/tmp/FedexLabels.pdf"
				merger.write(output_pdf_path)
				merger.close()
				return tracking_numbers, output_pdf_path, carrier_price

	def fedex_cancel_shippment(self, picking):
		self = self.sudo()
		list_of_tracking_numbers = picking.carrier_tracking_ref.split(',')
		oauth_token = self.get_fedex_oauth_token()

		if self.prod_environment == True:
			url = 'https://apis.fedex.com/ship/v1/shipments/cancel'
		else:
			url = 'https://apis-sandbox.fedex.com/ship/v1/shipments/cancel'

		headers = {
			'Content-Type': 'application/json',
			'Authorization': f"Bearer {oauth_token}",
		}

		for tracking_number in list_of_tracking_numbers:
			payload = {
				"accountNumber": {
					"value": self.sudo().fedex_account_number
				},
				"trackingNumber": tracking_number.strip()
			}

			_logger.info("FedEx API Payload: %s", json.dumps(payload, indent=4))

			try:
				response = requests.put(url, headers=headers, json=payload)
				_logger.info("FedEx API Response: %s %s", response.status_code, response.text)

				if response.status_code == 200:
					_logger.info("Shipment %s canceled successfully", tracking_number)
				else:
					_logger.error("Failed to cancel shipment %s. Response: %s", tracking_number, response.text)

			except requests.exceptions.RequestException as e:
				_logger.error("Exception occurred while canceling shipment %s: %s", tracking_number, e)

	def fedex_rest_cancel_shipment(self, picking):
		self = self.sudo()
		list_of_tracking_numbers = picking.carrier_tracking_ref.split(',')
		oauth_token = self.get_fedex_oauth_token()

		if self.prod_environment == True:
			url = 'https://apis.fedex.com/ship/v1/shipments/cancel'
		else:
			url = 'https://apis-sandbox.fedex.com/ship/v1/shipments/cancel'

		headers = {
			'Content-Type': 'application/json',
			'Authorization': f"Bearer {oauth_token}",
		}

		for tracking_number in list_of_tracking_numbers:
			payload = {
				"accountNumber": {
					"value": self.sudo().fedex_account_number
				},
				"trackingNumber": tracking_number.strip()
			}

			_logger.info("FedEx API Payload: %s", json.dumps(payload, indent=4))

			try:
				response = requests.put(url, headers=headers, json=payload)
				_logger.info("FedEx API Response: %s %s", response.status_code, response.text)

				if response.status_code == 200:
					_logger.info("Shipment %s canceled successfully", tracking_number)
					picking.message_post(body=_(u'Shipment #%s has been cancelled', tracking_number))
					picking.write({'carrier_tracking_ref': '',
								   'carrier_price': 0.0})
				else:
					_logger.error("Failed to cancel shipment %s. Response: %s", tracking_number, response.text)

			except requests.exceptions.RequestException as e:
				_logger.error("Exception occurred while canceling shipment %s: %s", tracking_number, e)

	def fedex_rest_get_tracking_link(self, picking):
		return 'https://www.fedex.com/apps/fedextrack/?action=track&trackingnumber=%s' % picking.carrier_tracking_ref


	def fedex_get_shipping_return_rate(self, order, return_wiz):
		if self.prod_environment == True:
			url = 'https://apis.fedex.com/rate/v1/rates/quotes'
		else:
			url = 'https://apis-sandbox.fedex.com/rate/v1/rates/quotes'
		oauth_token = self.get_fedex_oauth_token()

		headers = {
			'Content-Type': 'application/json',
			'Authorization': f"Bearer {oauth_token}",
		}

		packages_ids = self.env.context.get('packages', [])
		_logger.info("Request Data packages::::%s" % packages_ids)
		packages = []
		total_weight_in = 0
		if not len(packages_ids):
			weight = sum(
				[(line.product_id.weight * line.quantity) for line in return_wiz.product_return_moves])
			_logger.info("FedEx Total weight: %s" % weight)
			weight_limit = 150
			pieces = []
			while weight > weight_limit:
				pieces.append(weight_limit)
				weight -= weight_limit
			if weight > 0:
				pieces.append(weight)
			for line in pieces:
				weight = line
				length = self.fedex_default_package_type_id.packaging_length if self.fedex_default_package_type_id and self.fedex_default_package_type_id.packaging_length else "1"
				width = self.fedex_default_package_type_id.width if self.fedex_default_package_type_id and self.fedex_default_package_type_id.width else "1"
				height = self.fedex_default_package_type_id.height if self.fedex_default_package_type_id and self.fedex_default_package_type_id.height else "1"
				packages.append({
						"weight": {
							"units": self.fedex_weight_unit,
							"value": str(weight)
						},
						"dimensions": {
							"length": length,
							"width": width,
							"height": height,
							"units": "IN" if self.fedex_weight_unit == 'LB' else "CM"
						}
					})
				total_weight_in += weight
		else:
			for line in packages_ids:
				weight = line.shipping_weight
				length = (
					line.package_type_id.packaging_length 
					if line.package_type_id and line.package_type_id.packaging_length 
					else (
						self.fedex_default_package_type_id.packaging_length 
						if self.fedex_default_package_type_id and self.fedex_default_package_type_id.packaging_length 
						else "1"
					)
				)
				width = (
					line.package_type_id.width 
					if line.package_type_id and line.package_type_id.width 
					else (
						self.fedex_default_package_type_id.width 
						if self.fedex_default_package_type_id and self.fedex_default_package_type_id.width 
						else "1"
					)
				)
				height = (
					line.package_type_id.height 
					if line.package_type_id and line.package_type_id.height 
					else (
						self.fedex_default_package_type_id.height 
						if self.fedex_default_package_type_id and self.fedex_default_package_type_id.height 
						else "1"
					)
				)
				packages.append({
						"weight": {
							"units": self.fedex_weight_unit,
							"value": str(weight)
						},
						"dimensions": {
							"length": length,
							"width": width,
							"height": height,
							"units": "IN" if self.fedex_weight_unit == 'LB' else "CM"
						}
					})
				total_weight_in += weight
		_logger.info("weight division package: %s" % packages)
		payload = {
			"accountNumber": {
				"value": self.sudo().fedex_account_number
			},
			"requestedShipment": {
				"shipper": {
					"address": {
						"postalCode": order.partner_shipping_id.zip,
						"countryCode": order.partner_shipping_id.country_id.code,
						"city": order.partner_shipping_id.city,
						"stateOrProvinceCode": order.partner_shipping_id.state_id.code
					}
				},
				"recipient": {
					"address": {
						"postalCode": order.warehouse_id.partner_id.zip,
						"countryCode": order.warehouse_id.partner_id.country_id.code,
						"city": order.warehouse_id.partner_id.city,
						"stateOrProvinceCode": order.warehouse_id.partner_id.state_id.code
					}
				},
				"pickupType": "DROPOFF_AT_FEDEX_LOCATION",
				"rateRequestType": [
					  "ACCOUNT",
					  "LIST"
					],
				"serviceType": self.fedex_service_type,
				"packagingType": self.fedex_default_package_type_id.shipper_package_code,
				"totalPackageCount": len(packages),
				"totalWeight": total_weight_in,
				"requestedPackageLineItems":packages
			}
		}
		_logger.info("Fede Return Rate Request: %s" % payload)
		response = requests.post(url, headers=headers, json=payload)
		_logger.info("Fedex Return Rate Response code: %s" % response.status_code)
		_logger.info("Fedex Return Rate Response content: %s" % response.content)
		if response.status_code == 200:
			response_json = response.json()
			print("FedEx Response JSON:", response_json)
			_logger.info("Fedex Return Rate Response json: %s" % response_json)

			try:
				rate = response_json['output']['rateReplyDetails'][0]['ratedShipmentDetails'][0]['totalNetFedExCharge']
				return rate
			except KeyError as e:
				raise UserError(f"Failed to parse rate from FedEx response. Missing key: {e}. Full response: {response_json}")
		else:
			raise UserError(f"Failed to get rate from FedEx: {response.json().get('errors')[0]['message']}")


	def fedex_return_shippment_payload(self, picking, order, new_picking, return_wiz):
		oauth_token = self.get_fedex_oauth_token()

		if self.prod_environment == True:
			url = 'https://apis.fedex.com/ship/v1/shipments'
		else:
			url = 'https://apis-sandbox.fedex.com/ship/v1/shipments'

		headers = {
			'Content-Type': 'application/json',
			'Authorization': f"Bearer {oauth_token}",
		}
		ship_date = order.date_order.strftime('%Y-%m-%d')
		labels = []
		package_list = []
		tracking_numbers = []
		streetLinesShipper = ' '.join(filter(None, [new_picking.partner_id.street, new_picking.partner_id.street2]))
		ship_company_name = new_picking.partner_id.company_name if new_picking.partner_id.company_name else ''
		if not ship_company_name:
			ship_company_name = new_picking.partner_id.parent_id.name if new_picking.partner_id.parent_id else new_picking.partner_id.name
		_logger.info("FedEx ship_company_name: %s", ship_company_name)
		weight = sum(
			[(line.product_id.weight * line.quantity) for line in return_wiz.product_return_moves])
		_logger.info("Total weight: %s" % weight)
		package_count = return_wiz.package_qty
		_logger.info("Package count: %s" % package_count)
		if package_count < 0:
			raise ValidationError("Please define a valid Package Count! It should be a positive integer.")

		pieces = []
		weight_limit = 150
		if package_count > 0:
			per_package_weight = round((weight / package_count), 2)
			for _ in range(package_count):
				pieces.append(per_package_weight)
		else:
			while weight > weight_limit:
				pieces.append(weight_limit)
				weight -= weight_limit
			if weight > 0:
				pieces.append(round(weight, 2))

		_logger.info("Packages: %s" % pieces)
		sequenceNumber = 1
		total_weight = 0.0
		for line in pieces:
			package = {
				"groupPackageCount": 1,
				"sequenceNumber": str(sequenceNumber),
				"weight": {
					"value": line,
					"units": self.fedex_weight_unit
				},
			}
			total_weight += line
			sequenceNumber = sequenceNumber + 1
			package_list.append(package)
		_logger.info("Fedex weight division package: %s " % package_list)
		payload = {
			"labelResponseOptions": 'LABEL',
			"requestedShipment": {
				"shipper": {
					"contact": {
						"personName": new_picking.partner_id.name,
						"phoneNumber": self.extract_last_10_digits(new_picking.partner_id.phone) if new_picking.partner_id.phone else '',
						"companyName": ship_company_name
					},
					"address": {
						"streetLines": [
							new_picking.partner_id.street or "",
							new_picking.partner_id.street2 or ""
						],
						"city": new_picking.partner_id.city or "",
						"stateOrProvinceCode": new_picking.partner_id.state_id.code or "",
						"postalCode": str(new_picking.partner_id.zip) or "",
						"countryCode": new_picking.partner_id.country_id.code or ""
					}
				},
				"recipients": [
					{
						"contact": {
							"personName": order.warehouse_id.partner_id.name,
							"companyName": order.company_id.name,
							"phoneNumber": self.extract_last_10_digits(order.warehouse_id.partner_id.phone) if order.warehouse_id.partner_id.phone else ''
						},
						"address": {
							"streetLines": [
								order.warehouse_id.partner_id.street or "",
								order.warehouse_id.partner_id.street2 or ""
							],
							"city": order.warehouse_id.partner_id.city or "",
							"stateOrProvinceCode": order.warehouse_id.partner_id.state_id.code or "",
							"postalCode": str(order.warehouse_id.partner_id.zip) or "",
							"countryCode": order.warehouse_id.partner_id.country_id.code or ""
						}
					}
				],
				"rateRequestType": ["LIST"],
				"labelSpecification": {
					"imageType": self.fedex_label_file_type,
					"labelFormatType": "COMMON2D",
					"labelStockType": self.fedex_rest_label_stock_type,
					"labelPrintingOrientation": "TOP_EDGE_OF_TEXT_FIRST"
				},
				"shipDatestamp": ship_date,
				"serviceType": self.fedex_service_type,
				"pickupType": "USE_SCHEDULED_PICKUP",
				"shippingChargesPayment": {
					"paymentType": self.fedex_duty_payment
				},
				"specialServicesRequested": {
					"specialServiceTypes": ["RETURN_SHIPMENT"],
					"returnShipmentDetail": {
						"returnAssociationDetail": {
							"shipDatestamp": ship_date,
							"trackingNumber": picking.carrier_tracking_ref.split(',')[0] if picking.carrier_id.delivery_type == 'fedex_rest' else ""
						},
						"returnType": "PRINT_RETURN_LABEL"
					}
				},
				"packagingType": self.fedex_default_package_type_id.shipper_package_code,
				"totalPackageCount": len(package_list),
				"totalWeight": total_weight,
				"requestedPackageLineItems": package_list
				# "requestedPackageLineItems": [
				# 	{ }
				# ]
			},
			"accountNumber": {
				"value": self.sudo().fedex_account_number
			}
		}
		_logger.info("FedEx Return Shipment Request Data: %s " % json.dumps(payload, indent=4))
		response = requests.post(url, headers=headers, json=payload)
		_logger.info("FedEx Return Shipment API Response code: %s " % response.status_code)
		_logger.info("FedEx Return Shipment API Response content: %s " % response.text)
		if response.status_code == 200:
			try:

				response_json = response.json()
				transaction_shipments = response_json['output']['transactionShipments']
				tracking_number = response_json['output']['transactionShipments'][0]['masterTrackingNumber']
				carrier_price = response_json['output']['transactionShipments'][0]['completedShipmentDetail']['shipmentRating']['shipmentRateDetails'][0]['totalNetFedExCharge']
				for shipment in transaction_shipments:
					piece_responses = shipment['pieceResponses']
					for piece_response in piece_responses:
						package_documents = piece_response['packageDocuments']
						for document in package_documents:
							tracking_number = piece_response['trackingNumber']  # or document.get('trackingNumber') if different
							if 'encodedLabel' in document:
								label = document['encodedLabel']
							else:
								label_url = document.get('url', 'No URL available')
								label = f"Label URL: {label_url}"
							tracking_numbers.append(tracking_number)
							labels.append(label)

			except KeyError as e:
				raise UserError(f"Failed to parse label from FedEx response. Missing key: {e}. Full response: {response_json}")
			# else:
				# error_message = response.json().get('errors', [{'message': 'Unknown error'}])[0]['message']
				# raise UserError(f"Failed to generate label from FedEx: {error_message}")
		else:
			error_message = response.json().get('errors', [{'message': 'Unknown error'}])[0]['message']
			code = response.json().get('errors', [{'code': 'Unknown code'}])[0]['code']
			error_message = str(code) + ' ' + str(error_message)
			raise UserError(f"Failed to generate label from FedEx: {error_message}")
		if labels:
			merger = PdfFileMerger()
			zpl_files_content = []
			_logger.info("Fedex Labels : %s" % labels)
			for label in labels:
				if label.startswith("Label URL:"):
					label_url = label.replace("Label URL: ", "")
					time.sleep(5)
					label_response = requests.get(label_url)
					_logger.info("Label Response Data  : %s" % label_response.content)
					_logger.info("Label Response Status  : %s" % label_response.status_code)
					if label_response.status_code == 200:
						label_content = label_response.content
						if self.fedex_label_file_type == "ZPLII":
							label_content = base64.b64decode(label)
							zpl_files_content.append(label_content)
							# zpl_files_content.append(label_content.decode('utf-8'))
						else:
							temp_file_path = f"/tmp/label_{tracking_numbers[labels.index(label)]}.pdf"
							with open(temp_file_path, "wb") as f:
								f.write(label_content)
							merger.append(temp_file_path)
					# else:
					#   raise UserError(f"Failed to fetch label from URL. Status code: {label_response.status_code}")
				else:
					label = label + '=' * (-len(label) % 4)  # Ensure correct padding for Base64

					if self.fedex_label_file_type == "ZPLII":
						label_content = base64.b64decode(label)
						zpl_files_content.append(label_content)
						# zpl_files_content.append(label_content.decode('utf-8'))
					else:
						# Handle PDF labels
						label_content = base64.b64decode(label)
						temp_file_path = f"/tmp/label_{tracking_numbers[labels.index(label)]}.pdf"
						with open(temp_file_path, "wb") as f:
							f.write(label_content)
						merger.append(temp_file_path)

			if self.fedex_label_file_type == "ZPLII":
				output_zpl_path = "/tmp/FedexLabels.zpl"
				with open(output_zpl_path, "wb") as f:
					for zpl_content in zpl_files_content:
						f.write(zpl_content)
						f.write(b'\n')  # Add a newline to separate ZPL commands

				print(f"Output ZPL path: {output_zpl_path}")
				return tracking_numbers, output_zpl_path, carrier_price

			else:
				output_pdf_path = "/tmp/FedexLabels.pdf"
				merger.write(output_pdf_path)
				merger.close()
				return tracking_numbers, output_pdf_path, carrier_price



	def fedex_return_shippment(self, picking, order, new_picking, return_wiz):
		sale_order_id = self.env['sale.order'].search([('id', '=', picking.sale_id.id)])
		tracking_number, label_content, carrier_price = self.fedex_return_shippment_payload(picking, order, new_picking, return_wiz)
		if label_content:
			if not isinstance(tracking_number, list):
				tracking_number = [str(tracking_number)]
			if len(tracking_number) > 1:
				all_tracking_numbers = ','.join(tracking_number)
			else:
				all_tracking_numbers = tracking_number[0]
			new_picking.carrier_tracking_ref = all_tracking_numbers
			new_picking.carrier_price = carrier_price
			new_picking.get_min_cost = carrier_price
			new_picking.carrier_id = return_wiz.carrier_id

			if label_content.startswith('Label URL:') and not label_content.startswith('/tmp/'):
				label_url = label_content.replace('Label URL: ', '')
				try:
					label_response = requests.get(label_url)
					if label_response.status_code == 200:
						label_content = base64.b64encode(label_response.content).decode('utf-8')
					else:
						raise UserError(f"Failed to fetch label from URL. Status code: {label_response.status_code}")
				except requests.RequestException as e:
					raise UserError(f"Error fetching label from URL: {e}")
				except Exception as e:
					raise UserError(f"Unknown error fetching label from URL: {e}")

			elif label_content.startswith('/tmp/'):
				try:
					with open(label_content, 'rb') as file:
						label_content = base64.b64encode(file.read()).decode('utf-8')
				except Exception as e:
					raise UserError(f"Error reading local label file: {e}")

			if new_picking.carrier_id.fedex_label_file_type == "ZPLII":
				attachment = self.env['ir.attachment'].create({
					'name': 'FedEx Return Shipping Label.zpl',
					'type': 'binary',
					'datas': label_content,
					'res_model': 'stock.picking',
					'res_id': new_picking.id,
					'mimetype': 'application/zpl',
				})
			else:
				attachment = self.env['ir.attachment'].create({
					'name': 'FedEx Return Shipping Label.pdf',
					'type': 'binary',
					'datas': label_content,
					'res_model': 'stock.picking',
					'res_id': new_picking.id,
					'mimetype': 'application/pdf',
				})


			new_picking.message_post(body="%s Return Shipment Label !<br/>"
								   "<b>Tracking Numbers:</b> %s<br/>" % (return_wiz.carrier_id.name, all_tracking_numbers),
				  attachment_ids=[attachment.id])