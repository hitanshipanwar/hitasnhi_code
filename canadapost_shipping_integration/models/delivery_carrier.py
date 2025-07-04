from odoo import models, fields, api, _
from odoo.exceptions import Warning,ValidationError
import xml.etree.ElementTree as etree
from requests import request
from odoo.addons.canadapost_shipping_integration.ncs_api.ncs_response import Response
import logging
import re
import requests
from requests.exceptions import RequestException
import time

_logger = logging.getLogger(__name__)

class DeliveryCarrier(models.Model):
	_inherit = "delivery.carrier"
	delivery_type = fields.Selection(selection_add=[('canada_post', 'Canada Post NCS')], ondelete={'canada_post': 'set default'})
	ncs_option_code = fields.Selection([('SO', 'SO - Signature'),
										('COV', 'COV - Coverage'),
										('COD', 'COD - Collect on delivery'),
										('PA18', 'PA18 - Proof of Age Required - 18'),
										('PA19', 'PA19 - Proof of Age Required - 19'),
										('HFP', 'HFP - Card for pickup'),
										('DNS', 'DNS - Do not safe drop'),
										('LAD', 'LAD - Leave at door - do not card'),
										('D2PO', 'D2PO - Deliver to Post Office'),
										('RASE', 'RASE - Return at Sender’s Expense'),
										('RTS', 'RTA - Return to Sender'),
										('ABAN', 'ABAN - Abandon')], string="Option Code",
									   help="Required if the corresponding parent XML element option exists. This is "
											"the option code indicating which option applies to this shipment.\n "
											"Note: The D2PO option indicates that the parcel will be delivered "
											"directly to a nearby Post Office. For the D2PO option, the following XML "
											"elements are required: \n name (under destination) \n "
											"client-voice-number (under destination) \n notification \n "
											"option-qualifier-2 \n Note: If you select Collect on Delivery (COD), "
											"specify Card for Pickup (HFP) or Deliver to Post Office (D2PO). This is "
											"to facilitate the collection of COD funds at a post office. If not "
											"specified, the system will default to HFP. \n Non-delivery handling "
											"codes (required for some U.S.A. and international shipments)\n RASE - "
											"Return at Sender’s Expense \n RTS - Return to Sender \n ABAN - Abandon")
	ncs_service_type = fields.Selection([('DOM.RP', 'DOM.RP - Regular Parcel'),
										 ('DOM.EP', 'DOM.EP - Expedited Parcel'),
										 ('DOM.XP', 'DOM.XP - Xpresspost'),
										 ('DOM.PC', 'DOM.PC - Priority'),
										 ('USA.PW.ENV', 'USA.PW.ENV - Priority Worldwide Envelope USA'),
										 ('USA.PW.PAK', 'USA.PW.PAK - Priority Worldwide pak USA'),
										 ('USA.PW.PARCEL', 'USA.PW.PARCEL - Priority Worldwide Parcel USA'),
										 ('USA.XP', 'USA.XP - Xpresspost USA'),
										 ('USA.EP', 'USA.EP - Expedited Parcel USA'),
										 ('USA.SP.AIR', 'USA.SP.AIR - Small Packet USA Air'),
										 ('USA.TP', 'USA.TP - Tracked Packet – USA'),
										 ('INT.IP.AIR', 'INT.IP.AIR - International Parcel Air'),
										 ('INT.IP.SURF', 'INT.IP.SURF - International Parcel Surface'),
										 ('INT.PW.ENV', 'INT.PW.ENV - Priority Worldwide Envelope Int’l'),
										 ('INT.PW.PAK', 'INT.PW.PAK - Priority Worldwide pak Int’l'),
										 ('INT.PW.PARCEL', 'INT.PW.PARCEL - Priority Worldwide parcel Int’l'),
										 ('INT.XP', 'INT.XP - Xpresspost International'),
										 ('INT.SP.AIR', 'INT.SP.AIR - Small Packet International Air'),
										 ('INT.SP.SURF', 'INT.SP.SURF - Small Packet International Surface'),
										 ('INT.TP', 'INT.TP - Tracked Packet – International')], string="Service Type",
										help="Canada Post delivery service used for shipping the item")
	ncs_product_packaging_id = fields.Many2one('stock.package.type', string="Default Package Type",
											   help="Selected packaging type, used in the request parameter")

	ncs_reason_for_export = fields.Selection([('DOC', 'DOC = document'),
											  ('SAM', 'SAM = commercial sample'),
											  ('REP', 'REP = repair or warranty'),
											  ('SOG', 'SOG = sale of goods'),
											  ('OTH', 'OTH = other')], string="Reason For Export", default="SOG",
											 help="This is a code that represents the reason for export, which "
												  "assists with border crossing.")
	ncs_manifest = fields.Boolean(string="Generate Manifest")
	print_ncs_manifest = fields.Boolean(string="Send Manifest To Printer")

	def get_canadapost_url(self):
		if self.prod_environment:
			return "https://soa-gw.canadapost.ca/rs/"
		else:
			return "https://ct.soa-gw.canadapost.ca/rs/"

	def lbs_to_kg(self, lbs):
		kg = lbs * 0.45359237
		kg = round(kg, 2)
		return kg

	def canada_post_rate_shipment(self, order):

		shipment_weight = self.ncs_product_packaging_id.max_weight

		shipper_address = order.warehouse_id.partner_id
		recipient_address = order.partner_shipping_id

		# convet weight in to the delivery method's weight UOM
		total_weight = sum([(line.product_id.weight * line.product_uom_qty) for line in order.order_line if not line.is_delivery])
		total_weight = self.lbs_to_kg(total_weight)
		declared_value = round(order.amount_untaxed, 2)
		declared_currency = order.currency_id.name

		price = 0.0
		rate_dict = self.ncs_canada_post_get_shipping_rate(shipper_address, recipient_address, total_weight,
														   picking_bulk_weight=False, packages=False,
														   declared_value=declared_value,
														   declared_currency=declared_currency,
														   company_id=order.company_id)
		_logger.info("Rate Response Data  : %s" % str(rate_dict))
		if rate_dict.get('messages', False):
			return {'success': False, 'price': price, 'error_message': rate_dict['messages']['message']['description'],
					'warning_message': False}
		if rate_dict.get('price-quotes', False) and rate_dict.get('price-quotes').get('price-quote', False):
			quotes = rate_dict['price-quotes']['price-quote']
			if isinstance(quotes, dict):
				quotes = [quotes]
			for quote in quotes:
				if quote['service-code'] == self.ncs_service_type:
					price = quote['price-details']['due']
					return {'success': True, 'price': float(price), 'error_message': False, 'warning_message': False}
		return {'success': False, 'price': 0.0,
						'error_message': "Rate API dosen't provide this service type price %s"%(rate_dict),
						'warning_message': False}

	def canada_post_package_rate(self, order, package):

		shipment_weight = self.ncs_product_packaging_id.max_weight

		shipper_address = order.warehouse_id.partner_id
		recipient_address = order.partner_shipping_id

		# convet weight in to the delivery method's weight UOM
		total_weight = package.shipping_weight
		total_weight = self.lbs_to_kg(total_weight)
		declared_value = round(order.amount_untaxed, 2)
		declared_currency = order.currency_id.name

		price = 0.0
		rate_dict = self.ncs_canada_post_get_shipping_rate(shipper_address, recipient_address, total_weight,
														   picking_bulk_weight=False, packages=False,
														   declared_value=declared_value,
														   declared_currency=declared_currency,
														   company_id=order.company_id)
		_logger.info("Rate Response Data  : %s" % str(rate_dict))
		if rate_dict.get('messages', False):
			return {'success': False, 'price': price, 'error_message': rate_dict['messages']['message']['description'],
					'warning_message': False}
		if rate_dict.get('price-quotes', False) and rate_dict.get('price-quotes').get('price-quote', False):
			quotes = rate_dict['price-quotes']['price-quote']
			if isinstance(quotes, dict):
				quotes = [quotes]
			for quote in quotes:
				if quote['service-code'] == self.ncs_service_type:
					price = quote['price-details']['due']
					return {'success': True, 'price': float(price), 'error_message': False, 'warning_message': False}
		return {'success': False, 'price': 0.0,
						'error_message': "Rate API dosen't provide this service type price %s"%(rate_dict),
						'warning_message': False}



	def ncs_canada_post_get_shipping_rate(self, shipper_address, recipient_address, total_weight, picking_bulk_weight,
										  packages=False, declared_value=False, declared_currency=False,
										  company_id=False):
		result = {}
		# built request data
		service_root = etree.Element("mailing-scenario")
		service_root.attrib["xmlns"] = "http://www.canadapost.ca/ws/ship/rate-v3"
		etree.SubElement(service_root, "customer-number").text = self.company_id and self.company_id.ncs_customer_number

		parcel = etree.SubElement(service_root, "parcel-characteristics")
		etree.SubElement(parcel, "weight").text = str(total_weight)

		etree.SubElement(service_root, "origin-postal-code").text = "%s" % (
			shipper_address.zip.replace(" ", "").upper())

		destination = etree.SubElement(service_root, "destination")
		if str(self.ncs_service_type[:3]) == 'DOM':
			domestic = etree.SubElement(destination, "domestic")
			etree.SubElement(domestic, "postal-code").text = "%s" % (recipient_address.zip.replace(" ", "").upper())
		elif str(self.ncs_service_type[:3]) == 'USA':
			united_states = etree.SubElement(destination, "united-states")
			etree.SubElement(united_states, "zip-code").text = "%s" % (recipient_address.zip.upper())
		elif str(self.ncs_service_type[:3]) == 'INT':
			international = etree.SubElement(destination, "international")
			etree.SubElement(international, "country-code").text = "%s" % (
					recipient_address.country_id and recipient_address.country_id.code)
		url = '%sship/price' % (self.get_canadapost_url())
		base_data = etree.tostring(service_root).decode('utf-8')
		headers = {"Accept": "application/vnd.cpc.ship.rate-v3+xml",
				   "Content-Type": "application/vnd.cpc.ship.rate-v3+xml"}
		_logger.info("Rate Request Data  : %s" % base_data)
		try:
			response_body = request(method='POST', url=url, data=base_data, headers=headers,
									auth=(self.company_id.ncs_username,
										  self.company_id.ncs_password))
			api = Response(response_body)
			result = api.dict()
			_logger.info("Rate Response Data  : %s" % result)
			result['base_data'] = base_data
		except Exception as e:
			result['error_message'] = e.message
			return result
		return result

	def canada_post_send_shipping(self, pickings):
		response = []
		for picking in pickings:
			extra_price = 0
			ship_ref = ''
			tracking_numbers = []
			for package in picking.move_line_ids_without_package.mapped('result_package_id'):
				total_weight = round(package.shipping_weight, 2)
				total_weight = self.lbs_to_kg(total_weight)
				destination_address = picking.partner_id
				sender_address = picking.picking_type_id and picking.picking_type_id.warehouse_id and \
								 picking.picking_type_id.warehouse_id.partner_id

				resp_company_name = picking.partner_id.company_name if picking.partner_id.company_name else ''
				if not resp_company_name:
					resp_company_name = picking.partner_id.parent_id.name if picking.partner_id.parent_id else picking.partner_id.name

				root_node = etree.Element("shipment")
				root_node.attrib["xmlns"] = "http://www.canadapost.ca/ws/shipment-v8"

				etree.SubElement(root_node, "group-id").text = picking.origin
				etree.SubElement(root_node, "cpc-pickup-indicator").text = "true"
				etree.SubElement(root_node, "requested-shipping-point").text = "%s" % (
						sender_address.zip.replace(" ", "").upper() or "")

				delivery_spec_node = etree.SubElement(root_node, "delivery-spec")
				etree.SubElement(delivery_spec_node, "service-code").text = "%s" % (self.ncs_service_type)

				sender_node = etree.SubElement(delivery_spec_node, "sender")
				etree.SubElement(sender_node, "company").text = sender_address.name
				etree.SubElement(sender_node, "contact-phone").text = "%s" % (sender_address.phone or "")
				address_details = etree.SubElement(sender_node, "address-details")
				etree.SubElement(address_details, "address-line-1").text = sender_address.street or ""
				etree.SubElement(address_details, "address-line-2").text = sender_address.street2 or ""
				etree.SubElement(address_details, "city").text = sender_address.city or ""
				etree.SubElement(address_details, "prov-state").text = "%s" % (
						sender_address.state_id and sender_address.state_id.code or "")
				etree.SubElement(address_details, "country-code").text = "%s" % (
						sender_address.country_id and sender_address.country_id.code or "")
				etree.SubElement(address_details, "postal-zip-code").text = "%s" % (
						sender_address.zip.replace(" ", "").upper() or "")

				destination_node = etree.SubElement(delivery_spec_node, "destination")
				etree.SubElement(destination_node, "name").text = destination_address.name
				etree.SubElement(destination_node, "company").text = resp_company_name
				etree.SubElement(destination_node, "client-voice-number").text = destination_address.phone
				destination_address_details = etree.SubElement(destination_node, "address-details")
				street = destination_address.street
				if not street and destination_address.street2:
					street = destination_address.street2
				etree.SubElement(destination_address_details, "address-line-1").text = street or ""
				etree.SubElement(destination_address_details, "address-line-2").text = destination_address.street2 or ""
				etree.SubElement(destination_address_details, "city").text = destination_address.city or ""
				etree.SubElement(destination_address_details, "prov-state").text = "%s" % (
						destination_address.state_id and destination_address.state_id.code or "")
				etree.SubElement(destination_address_details, "country-code").text = "%s" % (
						destination_address.country_id and destination_address.country_id.code or "")
				etree.SubElement(destination_address_details, "postal-zip-code").text = "%s" % (
						destination_address.zip.replace(" ", "").upper() or "")

				if self.ncs_option_code:
					options = etree.SubElement(delivery_spec_node, "options")
					option = etree.SubElement(options, "option")
					etree.SubElement(option, "option-code").text = str(self.ncs_option_code or "")

				parcel_characteristics = etree.SubElement(delivery_spec_node, "parcel-characteristics")
				etree.SubElement(parcel_characteristics, "weight").text = "%s" % total_weight
				dimensions = etree.SubElement(parcel_characteristics, "dimensions ")
				
				etree.SubElement(dimensions, "length").text = "%s" % (
					package.package_type_id.packaging_length 
					if package.package_type_id and package.package_type_id.packaging_length 
					else (
						self.ncs_product_packaging_id.packaging_length 
						if self.ncs_product_packaging_id and self.ncs_product_packaging_id.packaging_length 
						else "1"
					)
				)
				etree.SubElement(dimensions, "width").text = "%s" % (
					package.package_type_id.width 
					if package.package_type_id and package.package_type_id.width 
					else (
						self.ncs_product_packaging_id.width 
						if self.ncs_product_packaging_id and self.ncs_product_packaging_id.width 
						else "1"
					)
				)
				etree.SubElement(dimensions, "height").text = "%s" % (
					package.package_type_id.height 
					if package.package_type_id and package.package_type_id.height 
					else (
						self.ncs_product_packaging_id.height 
						if self.ncs_product_packaging_id and self.ncs_product_packaging_id.height 
						else "1"
					)
				)
				notification = etree.SubElement(delivery_spec_node, "notification")
				etree.SubElement(notification, "email").text = "%s" %(sender_address.email)
				etree.SubElement(notification, "on-shipment").text = "true"
				etree.SubElement(notification, "on-exception").text = "true"
				etree.SubElement(notification, "on-delivery").text = "true"

				print_preferences = etree.SubElement(delivery_spec_node, "print-preferences")
				etree.SubElement(print_preferences, "output-format").text = "4x6"

				preferences = etree.SubElement(delivery_spec_node, "preferences")
				etree.SubElement(preferences, "show-packing-instructions").text = "true"
				etree.SubElement(preferences, "show-postage-rate").text = "false"
				etree.SubElement(preferences, "show-insured-value").text = "true"

				settelment_info = etree.SubElement(delivery_spec_node, "settlement-info")
				etree.SubElement(settelment_info, "contract-id").text = self.company_id.ncs_contract_id
				etree.SubElement(settelment_info, "intended-method-of-payment").text = "Account"


				# if picking.move_line_ids_without_package and len(picking.move_line_ids_without_package.mapped('result_package_id')):
				customs = etree.SubElement(delivery_spec_node, "customs")
				etree.SubElement(customs, "currency").text = str(picking.sale_id.currency_id.name)
				# if picking.sale_id.currency_id.rate:
				#     rate = picking.sale_id.currency_id.rate
				#     rate = round(rate, 2)
				# etree.SubElement(customs, "conversion-from-cad").text = str(rate or '')
				etree.SubElement(customs, "reason-for-export").text = "%s" % self.ncs_reason_for_export
				sku_list = etree.SubElement(customs, "sku-list")
				for move_line in picking.move_line_ids_without_package:
					if move_line.result_package_id.id == package.id:
						item = etree.SubElement(sku_list, "item")
						desc = move_line.product_id.name
						if desc and len(desc) > 45:
							desc = desc[:45]
						etree.SubElement(item, "customs-description").text = str(desc)
						etree.SubElement(item, "unit-weight").text = str(total_weight)
						etree.SubElement(item, "customs-value-per-unit").text = str(move_line.move_id.sale_line_id.price_unit)
						etree.SubElement(item, "customs-number-of-units").text = str(int(move_line.qty_done))

				ncs_url = self.get_canadapost_url()
				url = "%s%s/%s/shipment" % (ncs_url, self.company_id.ncs_customer_number, self.company_id.ncs_customer_number)
				base_data = etree.tostring(root_node).decode('utf-8')
	#             base_data = """<shipment xmlns="http://www.canadapost.ca/ws/shipment-v8">
	# <group-id>4326432</group-id>
	# <requested-shipping-point>H2B1A0</requested-shipping-point>
	# <cpc-pickup-indicator>true</cpc-pickup-indicator>
	# <delivery-spec>
	# <service-code>DOM.EP</service-code>
	# <sender>
	# <name>Bob</name>
	# <company>CGI</company>
	# <contact-phone>1 (450) 823-8432</contact-phone>
	# <address-details>

	# <address-line-1>502 MAIN ST N</address-line-1>
	# <city>MONTREAL</city>
	# <prov-state>QC</prov-state>
	# <country-code>CA</country-code>
	# <postal-zip-code>H2B1A0</postal-zip-code>
	# </address-details>
	# </sender>
	# <destination>
	# <name>Jain</name>
	# <company>CGI</company>
	# <address-details>
	# <address-line-1>23 jardin private</address-line-1>
	# <city>Ottawa</city>
	# <prov-state>ON</prov-state>
	# <country-code>CA</country-code>
	# <postal-zip-code>K1K4T3</postal-zip-code>
	# </address-details>
	# </destination>
	# <options>
	# <option>
	# <option-code>DC</option-code>
	# </option>
	# </options>
	# <parcel-characteristics>
	# <weight>20</weight>
	# <dimensions>
	# <length>6</length>
	# <width>12</width>
	# <height>9</height>
	# </dimensions>
	# <mailing-tube>false</mailing-tube>
	# </parcel-characteristics>
	# <notification>
	# <email>himanshu.keshri@o2b.co.in</email>
	# <on-shipment>true</on-shipment>
	# <on-exception>false</on-exception>
	# <on-delivery>true</on-delivery>
	# </notification>
	# <print-preferences>
	# <output-format>8.5x11</output-format>
	# </print-preferences>
	# <preferences>
	# <show-packing-instructions>true</show-packing-instructions>
	# <show-postage-rate>false</show-postage-rate>
	# <show-insured-value>true</show-insured-value>
	# </preferences>
	# <settlement-info>
	# <contract-id>0042682521</contract-id>
	# <intended-method-of-payment>Account</intended-method-of-payment>
	# </settlement-info>
	# </delivery-spec>
	# </shipment>"""
				headers = {"Accept": "application/vnd.cpc.shipment-v8+xml",
						   "Content-Type": "application/vnd.cpc.shipment-v8+xml", "Accept-language": "en-CA"}

				try:
					_logger.info("Create Shipment Request Data  : %s" % (base_data))
					response_body = request(method='POST', url=url, data=base_data, headers=headers,
											auth=(self.company_id.ncs_username, self.company_id.ncs_password))
					if response_body.status_code == 200:
						api = Response(response_body)
						print("response_body**",response_body.content)
						result = api.dict()
						_logger.info("Create Shipment Response Data  : %s" % (result))
					else:
						error_code = "%s" % response_body.status_code
						error_message = response_body.reason
						message = error_code + " " + error_message
						raise Warning(
							"ShipmentRequest Fail : %s \n More Information \n %s" % (message, response_body.text))
				except Exception as e:
					raise Warning(e)
				if not result['shipment-info']['shipment-id'] or not \
						result['shipment-info']['links']['link']:
					raise Warning("ShipmentRequest Fail \n More Information \n %s" % (result))
				shipment_id = str(result['shipment-info']['shipment-id'])
				tracking_pin = result['shipment-info'].get('tracking-pin', False)
				if not tracking_pin:
					tracking_pin = shipment_id
				commercial_invoice_url_attchment = ""
				commercial_invoice = False
				url_attchment = ""
				for link in result['shipment-info']['links']['link']:
					if link['_rel'] == 'label':
						url_attchment = link['_href']
					if link['_rel'] == 'commercialInvoice':
						commercial_invoice_url_attchment = link['_href']
						commercial_invoice = True
				headers_attchment = {'Accept': 'application/pdf'}
				try:
					attachment_response = request(method='GET', url=url_attchment, headers=headers_attchment, auth=(
						self.company_id.ncs_username, self.company_id.ncs_password))
					_logger.info("Label Response Data  : %s" % attachment_response)
					mesage_ept = (_("Shipment created!<br/> <b>Shipment Tracking Number : </b>%s") % (
						tracking_pin))
					shipment_id = result['shipment-info']['shipment-id']
					tracking_numbers.append(shipment_id)
					picking.message_post(body=mesage_ept, attachments=[
						('NCS Label - %s.PDF' % tracking_pin,
						 attachment_response.content)])

					if commercial_invoice:
						commercial_invoice_attachment_response = request(method='GET', url=commercial_invoice_url_attchment,
																		 headers=headers_attchment, auth=(
								self.company_id.ncs_username, self.company_id.ncs_password))
						mesage_ept = (_("Shipment created!<br/> <b>Shipment Tracking Number : </b>%s") % (
							tracking_pin))
						shipment_id = result['shipment-info']['shipment-id']
						tracking_numbers.append(shipment_id)
						picking.message_post(body=mesage_ept, attachments=[
							('NCS Commercial Invoice - %s.PDF' % tracking_pin,
							 commercial_invoice_attachment_response.content)])

				except Exception as e:
					raise Warning(e)

				url_receipt = "%s" % (self.get_canadapost_url()) + str(
					self.company_id.ncs_customer_number) + '/' + str(
					self.company_id.ncs_customer_number) + "/shipment/" + str(shipment_id) + "/price"
				print("url_receipt**",url_receipt)
				try:
					receipt_response = request(method='GET', url=url_receipt, headers=headers, auth=(
						self.company_id.ncs_username, self.company_id.ncs_password))
					print("receipt_response**",receipt_response.content)
					if receipt_response.status_code == 200:
						api_receipt = Response(receipt_response)
						result_receipt = api_receipt.dict()
						_logger.info("Get shipment Detail Response Data  : %s" % (result_receipt))
					else:
						error_code = "%s" % receipt_response.status_code
						error_message = response_body.reason
						message = error_code + " " + error_message
						mesage_ept = "ShipmentAcceptRequest Fail : %s \n More Information \n %s" % (
							message, response_body.text)

						picking.message_post(body=mesage_ept)

				except Exception as e:
					picking.message_post(body=e)

				print("extra_price", extra_price)
				extra_price1 = result_receipt['shipment-price'] and \
							  result_receipt['shipment-price']['due-amount'] or 0.0
				print("extra_price1", extra_price1)
				extra_price = extra_price + float(extra_price1)
				tracking_pin = result['shipment-info'].get('tracking-pin', False)
				if tracking_pin:
					shipment_id = tracking_pin
				else:
					_logger.info("This Service not provide the tracking no.Service is : %s" % self.ncs_service_type)

				if not ship_ref:
					ship_ref = shipment_id
				else:
					ship_ref = ship_ref + ',' + shipment_id
				# shipment_chrg = self.canada_post_rate_shipment(picking.sale_id)
			shipping_data = {
				'exact_price': float(extra_price) or 0.0,
				'tracking_number': ship_ref}
			picking.carrier_tracking_ref = ship_ref
			response += [shipping_data]
			all_tracking_numbers = ','.join(tracking_numbers)
			picking.tracking_num = all_tracking_numbers
		return response

	def canada_post_get_tracking_link(self, picking):
		link = 'https://www.canadapost.ca/trackweb/en#/resultList?searchFor='
		res = '%s%s' % (link, picking.carrier_tracking_ref)
		return res

	def canada_post_cancel_shipment(self, picking):
		list_of_tracking_numbers = picking.tracking_num.split(',')
		for tracking_num in list_of_tracking_numbers:
			headers = {"Accept": "application/vnd.cpc.shipment-v8+xml",
							   "Content-Type": "application/vnd.cpc.shipment-v8+xml", "Accept-language": "en-CA"}
			shipment_id = tracking_num
			url_receipt = "%s" % (self.get_canadapost_url()) + str(
				self.company_id.ncs_customer_number) + '/' + str(
				self.company_id.ncs_customer_number) + "/shipment/" + str(shipment_id)
			try:
				cancel_response = request(method='DELETE', url=url_receipt, headers=headers, auth=(
					self.company_id.ncs_username, self.company_id.ncs_password))
				_logger.info("Delet shipment  : %s" % (cancel_response))
				_logger.info("Delet shipment  : %s" % (cancel_response.status_code))
				_logger.info("Delet shipment  : %s" % (cancel_response.content))
				if cancel_response.status_code in [200, 204]:
					api_receipt = Response(cancel_response)
					response_data = api_receipt.dict()
					_logger.info("Delet shipment  : %s" % (response_data))
				else:
					error_code = "%s" % cancel_response.status_code
					error_message = cancel_response.reason
					message = error_code + " " + error_message
					mesage_ept = "CancelRequest Fail : %s \n More Information \n %s" % (
						message, cancel_response.text)

					_logger.info("Cancel Shipment Response Data  : %s" % (mesage_ept))
			except Exception as e:
				_logger.info("Cancel Shipment Exception Response Data  : %s" % (e))

	def get_canada_post_shipment_info(self, picking):
		headers = {"Accept": "application/vnd.cpc.shipment-v8+xml",
						   "Content-Type": "application/vnd.cpc.shipment-v8+xml", "Accept-language": "en-CA"}
		shipment_ids = picking.carrier_tracking_ref
		if shipment_ids and ',' in shipment_ids:
			shipment_ids = shipment_ids.split(',')
		else:
			shipment_ids = [picking.carrier_tracking_ref]
		tracking_pin_ref = ''
		for shipment_id in shipment_ids:
			url_receipt = "%s" % (self.get_canadapost_url()) + str(
				self.company_id.ncs_customer_number) + '/' + str(
				self.company_id.ncs_customer_number) + "/shipment/" + str(shipment_id) + "/details"
			try:
				receipt_response = request(method='GET', url=url_receipt, headers=headers, auth=(
					self.company_id.ncs_username, self.company_id.ncs_password))
				if receipt_response.status_code == 200:
					api_receipt = Response(receipt_response)
					result_receipt = api_receipt.dict()
					_logger.info("Get shipment Detail Response Data  : %s" % (result_receipt))
					shipment_details = result_receipt.get('shipment-details', False)
					if shipment_details and 'tracking-pin' in shipment_details:
						tracking_pin = shipment_details.get('tracking-pin', False)
						if not tracking_pin_ref and tracking_pin:
							tracking_pin_ref = tracking_pin
						elif tracking_pin_ref and tracking_pin:
							tracking_pin_ref = tracking_pin_ref + ',' + tracking_pin
				else:
					error_code = "%s" % receipt_response.status_code
					error_message = receipt_response.reason
					message = error_code + " " + error_message
					mesage_ept = "ShipmentAcceptRequest Fail : %s \n More Information \n %s" % (
						message, receipt_response.text)

					_logger.info("Get shipment Detail Response Data  : %s" % (mesage_ept))
			except Exception as e:
				_logger.info("Get shipment Detail Exception Response Data  : %s" % (e))
		if tracking_pin_ref:
			picking.carrier_tracking_ref = tracking_pin_ref

	def get_transmit_details(self, picking):
		headers = {
			"Accept": "application/vnd.cpc.manifest-v8+xml",
			"Content-Type": "application/vnd.cpc.manifest-v8+xml",
			"Accept-language": "en-CA"
		}
		ncs_url = self.get_canadapost_url()
		url = f"{ncs_url}{self.company_id.ncs_customer_number}/{self.company_id.ncs_customer_number}/manifest"

		transmit_set = etree.Element("transmit-set", xmlns="http://www.canadapost.ca/ws/manifest-v8")

		group_ids = etree.SubElement(transmit_set, "group-ids")
		group_id = etree.SubElement(group_ids, "group-id")
		group_id.text = picking.origin or ""

		shippingpoint = picking.partner_id.zip.replace(" ", "")
		requested_shipping_point = etree.SubElement(transmit_set, "requested-shipping-point")
		requested_shipping_point.text = shippingpoint or ""

		cpc_pickup_indicator = etree.SubElement(transmit_set, "cpc-pickup-indicator")
		cpc_pickup_indicator.text = "true"

		detailed_manifests = etree.SubElement(transmit_set, "detailed-manifests")
		detailed_manifests.text = "true"

		method_of_payment = etree.SubElement(transmit_set, "method-of-payment")
		method_of_payment.text = "Account"

		manifest_address = etree.SubElement(transmit_set, "manifest-address")

		resp_company_name = picking.company_id.name
		
		manifest_company = etree.SubElement(manifest_address, "manifest-company")
		manifest_company.text = resp_company_name or ""

		manifest_name = etree.SubElement(manifest_address, "manifest-name")
		manifest_name.text = "Shipping Department"

		phone_number = etree.SubElement(manifest_address, "phone-number")
		phone_number.text = picking.sale_id.warehouse_id.partner_id.phone or ""

		address_details = etree.SubElement(manifest_address, "address-details")

		Address = ' '.join(filter(None, [picking.sale_id.warehouse_id.partner_id.street, picking.sale_id.warehouse_id.partner_id.street2]))

		address_line_1 = etree.SubElement(address_details, "address-line-1")
		address_line_1.text = Address or ""

		address_line_2 = etree.SubElement(address_details, "address-line-2")
		address_line_2.text = picking.sale_id.warehouse_id.partner_id.street2 or ""

		city = etree.SubElement(address_details, "city")
		city.text = picking.sale_id.warehouse_id.partner_id.city or ""

		prov_state = etree.SubElement(address_details, "prov-state")
		prov_state.text = picking.sale_id.warehouse_id.partner_id.state_id.code or ""

		postal_zip_code = etree.SubElement(address_details, "postal-zip-code")
		postal_zip_code.text = picking.sale_id.warehouse_id.partner_id.zip.replace(" ", "") or ""

		data = etree.tostring(transmit_set).decode('utf-8')

		try:
			receipt_response = request(
				method='POST', url=url, data=data, headers=headers, 
				auth=(self.company_id.ncs_username, self.company_id.ncs_password)
			)
			_logger.info("POST Manifest Request URL: %s" % url)
			_logger.info("POST Manifest Request Data: %s" % data)
			_logger.info("POST Manifest Response Status Code: %s" % receipt_response.status_code)

			if receipt_response.status_code == 200:
				api_receipt = Response(receipt_response)
				result_receipt = api_receipt.dict()
				_logger.info("Get Manifest Response Data: %s" % result_receipt)
				href = result_receipt['manifests']['link']['_href']
				match = re.search(r'/manifest/(\d+)$', href)
				if match:
					manifest_id = match.group(1)
					return manifest_id
				else:
					_logger.warning("Manifest ID not found in the response href.")
			else:
				error_code = receipt_response.status_code
				error_message = receipt_response.reason
				message = f"{error_code} {error_message}"
				_logger.error("Get Manifest Request Failed: %s\nMore Information:\n%s" % (message, receipt_response.text))
		except RequestException as e:
			_logger.error("RequestException during Manifest Request: %s" % str(e))
		except Exception as e:
			_logger.error("Exception during Manifest Request: %s" % str(e))


	def get_canadapost_manifest(self, picking):
		manifest_id = self.get_transmit_details(picking)
		if not manifest_id:
			_logger.error("Failed to get manifest ID.")
			return

		headers = {
			"Accept": "application/vnd.cpc.manifest-v8+xml",
			"Accept-language": "en-CA"
		}
		ncs_url = self.get_canadapost_url()
		url = f"{ncs_url}{self.company_id.ncs_customer_number}/{self.company_id.ncs_customer_number}/manifest/{manifest_id}"

		try:
			time.sleep(2)
			receipt_response = request(
				method='GET', url=url, headers=headers,
				auth=(self.company_id.ncs_username, self.company_id.ncs_password)
			)
			_logger.info("GET Manifest Request URL: %s" % url)
			_logger.info("GET Manifest Response Status Code: %s" % receipt_response.status_code)

			if receipt_response.status_code == 200:
				api_receipt = Response(receipt_response)
				result_receipt = api_receipt.dict()
				artifact_url = next(
					(link['_href'] for link in result_receipt['manifest']['links']['link'] if link['_rel'] == 'artifact'),
					None
				)
				if artifact_url:
					headers_attachment = {'Accept': 'application/pdf'}
					time.sleep(2)
					artifact_response = request(
						method='GET', url=artifact_url, headers=headers_attachment,
						auth=(self.company_id.ncs_username, self.company_id.ncs_password)
					)
					if artifact_response.status_code == 200:
						message_ept = _("Manifest created!")
						picking.tracking_num = result_receipt['manifest']['po-number']
						picking.message_post(
							body=message_ept,
							attachments=[('NCS Manifest.PDF', artifact_response.content)]
						)
					else:
						_logger.error("Failed to retrieve artifact. Status code: %s\nResponse Data: %s" % (artifact_response.status_code, artifact_response.text))
				else:
					_logger.warning("Artifact URL not found in manifest response.")
			else:
				error_code = receipt_response.status_code
				error_message = receipt_response.reason
				message = f"{error_code} {error_message}"
				_logger.error("Get Manifest Request Failed: %s\nMore Information:\n%s" % (message, receipt_response.text))
		except RequestException as e:
			_logger.error("RequestException during Manifest Retrieval: %s" % str(e))
		except Exception as e:
			_logger.error("Exception during Manifest Retrieval: %s" % str(e))

	def canada_post_return_rate_shipment(self, order, return_wiz):

		shipment_weight = self.ncs_product_packaging_id.max_weight

		recipient_address = order.warehouse_id.partner_id
		shipper_address = order.partner_shipping_id

		total_weight = sum(
				[(line.product_id.weight * line.quantity) for line in return_wiz.product_return_moves])
		weight = self.lbs_to_kg(total_weight)
		weight_limit = 30
		pieces = []
		while weight > weight_limit:
			pieces.append(weight_limit)
			weight -= weight_limit
		if weight > 0:
			pieces.append(weight)

		declared_value = round(order.amount_untaxed, 2)
		declared_currency = order.currency_id.name

		price = 0.0
		net_price = 0.0
		_logger.info("List of weight divion: %s" % pieces)
		for line in pieces:
			total_weight = round(line, 2)
			rate_dict = self.ncs_canada_post_get_shipping_return_rate(shipper_address, recipient_address, total_weight,
															   picking_bulk_weight=False, packages=False,
															   declared_value=declared_value,
															   declared_currency=declared_currency,
															   company_id=order.company_id)
			_logger.info("Rate Response Data  : %s" % str(rate_dict))
			if rate_dict.get('messages', False):
				return {'success': False, 'price': price, 'error_message': rate_dict['messages']['message']['description'],
						'warning_message': False}
			if rate_dict.get('price-quotes', False) and rate_dict.get('price-quotes').get('price-quote', False):
				quotes = rate_dict['price-quotes']['price-quote']
				if isinstance(quotes, dict):
					quotes = [quotes]
				for quote in quotes:
					if quote['service-code'] == self.ncs_service_type:
						price = quote['price-details']['due']
						net_price += float(quote['price-details']['due'])
						_logger.info("Net Price: %s" % net_price)
			# 			return {'success': True, 'price': float(price), 'error_message': False, 'warning_message': False}
			# return {'success': False, 'price': 0.0,
			# 				'error_message': "Rate API dosen't provide this service type price %s"%(rate_dict),
			# 				'warning_message': False}
		if net_price > 0.0:
			return {'success': True, 'price': net_price, 'error_message': False, 'warning_message': False}
		else:
			return {
				'success': False, 
				'price': 0.0,
				'error_message': "Rate API doesn't provide this service type price %s" % (rate_dict),
				'warning_message': False
			}

	def canada_post_package_return_rate(self, order, package):
		shipment_weight = self.ncs_product_packaging_id.max_weight

		recipient_address = order.warehouse_id.partner_id
		shipper_address = order.partner_shipping_id

		# convet weight in to the delivery method's weight UOM
		total_weight = package.shipping_weight
		total_weight = self.lbs_to_kg(total_weight)
		declared_value = round(order.amount_untaxed, 2)
		declared_currency = order.currency_id.name

		price = 0.0
		rate_dict = self.ncs_canada_post_get_shipping_return_rate(shipper_address, recipient_address, total_weight,
														   picking_bulk_weight=False, packages=False,
														   declared_value=declared_value,
														   declared_currency=declared_currency,
														   company_id=order.company_id)
		_logger.info("Rate Response Data  : %s" % str(rate_dict))
		if rate_dict.get('messages', False):
			return {'success': False, 'price': price, 'error_message': rate_dict['messages']['message']['description'],
					'warning_message': False}
		if rate_dict.get('price-quotes', False) and rate_dict.get('price-quotes').get('price-quote', False):
			quotes = rate_dict['price-quotes']['price-quote']
			if isinstance(quotes, dict):
				quotes = [quotes]
			for quote in quotes:
				if quote['service-code'] == self.ncs_service_type:
					price = quote['price-details']['due']
					return {'success': True, 'price': float(price), 'error_message': False, 'warning_message': False}
		return {'success': False, 'price': 0.0,
						'error_message': "Rate API dosen't provide this service type price %s"%(rate_dict),
						'warning_message': False}



	def ncs_canada_post_get_shipping_return_rate(self, shipper_address, recipient_address, total_weight, picking_bulk_weight,
										  packages=False, declared_value=False, declared_currency=False,
										  company_id=False):
		result = {}
		# built request data
		service_root = etree.Element("mailing-scenario")
		service_root.attrib["xmlns"] = "http://www.canadapost.ca/ws/ship/rate-v3"
		etree.SubElement(service_root, "customer-number").text = self.company_id and self.company_id.ncs_customer_number

		parcel = etree.SubElement(service_root, "parcel-characteristics")
		etree.SubElement(parcel, "weight").text = str(total_weight)

		etree.SubElement(service_root, "origin-postal-code").text = "%s" % (
			shipper_address.zip.replace(" ", "").upper())

		destination = etree.SubElement(service_root, "destination")
		if str(self.ncs_service_type[:3]) == 'DOM':
			domestic = etree.SubElement(destination, "domestic")
			etree.SubElement(domestic, "postal-code").text = "%s" % (recipient_address.zip.replace(" ", "").upper())
		elif str(self.ncs_service_type[:3]) == 'USA':
			united_states = etree.SubElement(destination, "united-states")
			etree.SubElement(united_states, "zip-code").text = "%s" % (recipient_address.zip.upper())
		elif str(self.ncs_service_type[:3]) == 'INT':
			international = etree.SubElement(destination, "international")
			etree.SubElement(international, "country-code").text = "%s" % (
					recipient_address.country_id and recipient_address.country_id.code)
		url = '%sship/price' % (self.get_canadapost_url())
		base_data = etree.tostring(service_root).decode('utf-8')
		headers = {"Accept": "application/vnd.cpc.ship.rate-v3+xml",
				   "Content-Type": "application/vnd.cpc.ship.rate-v3+xml"}
		_logger.info("Rate Request Data  : %s" % base_data)
		try:
			response_body = request(method='POST', url=url, data=base_data, headers=headers,
									auth=(self.company_id.ncs_username,
										  self.company_id.ncs_password))
			api = Response(response_body)
			result = api.dict()
			_logger.info("Rate Response Data  : %s" % result)
			result['base_data'] = base_data
		except Exception as e:
			result['error_message'] = e.message
			return result
		return result


	def canada_post_return_shipment(self, pickings, new_picking, return_wiz):
		for picking in new_picking:
			labels = []
			# _logger.info("NCS Package %s" % picking.move_line_ids_without_package)
			# _logger.info("NCS Package %s" % picking.move_line_ids_without_package.mapped('result_package_id'))
			# _logger.info("Out Picking %s" % pickings)
			# _logger.info("New Return Picking %s" % new_picking)
			weight = sum(
				[(line.product_id.weight * line.quantity) for line in return_wiz.product_return_moves])
			# _logger.info("weight in lb: %s" % weight)
			weight = self.lbs_to_kg(weight)
			# _logger.info("weight in kg: %s" % weight)
			package_count = return_wiz.package_qty
			# _logger.info("Pacakge count: %s" % package_count)
			pieces = []
			weight_limit = 30

			if package_count < 0:
				raise ValidationError("Please define a valid Package Count! It should be a positive integer.")

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
				# _logger.info("weight divion : %s" % pieces)
				
			# _logger.info("weight divion : %s" % pieces)
			for line in pieces:
				total_weight = round(line, 2)
				total_weight = total_weight
				returner_address = picking.partner_id
				destination_address = picking.picking_type_id and picking.picking_type_id.warehouse_id and \
								 picking.picking_type_id.warehouse_id.partner_id

				root = etree.Element("authorized-return", xmlns="http://www.canadapost.ca/ws/authreturn-v2")

				etree.SubElement(root, "service-code").text = self.ncs_service_type

				returner = etree.SubElement(root, "returner")
				etree.SubElement(returner, "name").text = returner_address.name
				etree.SubElement(returner, "company").text = returner_address.name
				returner_add = etree.SubElement(returner, "domestic-address")
				etree.SubElement(returner_add, "address-line-1").text = returner_address.street or ""
				etree.SubElement(returner_add, "address-line-2").text = returner_address.street2 or ""
				etree.SubElement(returner_add, "city").text = returner_address.city
				etree.SubElement(returner_add, "province").text = returner_address.state_id.code
				# etree.SubElement(returner_add, "postal-code").text = returner_address.zip
				etree.SubElement(returner_add, "postal-code").text = "%s" % (
						returner_address.zip.replace(" ", "").upper() or "")

				receiver = etree.SubElement(root, "receiver")
				etree.SubElement(receiver, "name").text = destination_address.name
				receiver_address = etree.SubElement(receiver, "domestic-address")
				etree.SubElement(receiver_address, "address-line-1").text = destination_address.street or ""
				etree.SubElement(receiver_address, "address-line-2").text = destination_address.street2 or ""
				etree.SubElement(receiver_address, "city").text = destination_address.city
				etree.SubElement(receiver_address, "province").text = destination_address.state_id.code
				# etree.SubElement(receiver_address, "postal-code").text = destination_address.zip
				etree.SubElement(receiver_address, "postal-code").text = "%s" % (
						destination_address.zip.replace(" ", "").upper() or "")

				parcel_characteristics = etree.SubElement(root, "parcel-characteristics")
				etree.SubElement(parcel_characteristics, "weight").text = str(total_weight)
				dimensions = etree.SubElement(parcel_characteristics, "dimensions ")
				etree.SubElement(dimensions, "length").text = "%s" % (
						self.ncs_product_packaging_id and self.ncs_product_packaging_id.packaging_length or 0.0)
				etree.SubElement(dimensions, "width").text = "%s" % (
						self.ncs_product_packaging_id and self.ncs_product_packaging_id.width or 0.0)
				etree.SubElement(dimensions, "height").text = "%s" % (
						self.ncs_product_packaging_id and self.ncs_product_packaging_id.height or 0.0)


				print_preferences = etree.SubElement(root, "print-preferences")
				etree.SubElement(print_preferences, "output-format").text = "4x6"

				references = etree.SubElement(root, "references")
				etree.SubElement(references, "customer-ref-1").text = pickings.origin

				settlement_info = etree.SubElement(root, "settlement-info")
				base_data = etree.tostring(root).decode('utf-8')


# 				base_data = """
# <authorized-return xmlns="http://www.canadapost.ca/ws/authreturn-v2">
# <create-public-key>true</create-public-key>
# <service-code>DOM.EP</service-code>
# <returner>
# <name>Jane Doe</name>
# <company>Capsule Corp.</company>
# <domestic-address>
# <address-line-1>2701 Return Avenue</address-line-1>
# <city>Ottawa</city>
# <province>ON</province>
# <postal-code>K1A0B1</postal-code>
# </domestic-address>
# </returner>
# <receiver>
# <name>John Doe</name>
# <company>Canada Post Corporation</company>
# <domestic-address>
# <address-line-1>2701 Riverside Drive</address-line-1>
# <city>Ottawa</city>
# <province>ON</province>
# <postal-code>K1A0B1</postal-code>
# </domestic-address>
# </receiver>
# <parcel-characteristics>
# <weight>15</weight>
# </parcel-characteristics>
# <print-preferences>
# <output-format>8.5x11</output-format>
# </print-preferences>
# <settlement-info></settlement-info>
# </authorized-return>
# 				"""
				ncs_url = self.get_canadapost_url()
				url = "%s%s/%s/openreturn" % (ncs_url, self.company_id.ncs_customer_number, self.company_id.ncs_customer_number)
				url = "%s" % (self.get_canadapost_url()) + str(
				self.company_id.ncs_customer_number) + '/' + str(
				self.company_id.ncs_customer_number) + "/authorizedreturn"

				# Set the headers
				headers = {
					"Content-Type": "application/vnd.cpc.authreturn-v2+xml",
					"Accept": "application/vnd.cpc.authreturn-v2+xml"
				}
				_logger.info("NCS Request Data : %s" % base_data)
				try:
					response = request(method='POST', url=url, data=base_data, headers=headers,
												auth=(self.company_id.ncs_username, self.company_id.ncs_password))
					_logger.info("NCS Response Data  : %s" % response)
					_logger.info("NCS Response Code  : %s" % response.status_code)
					_logger.info("NCS Response Content  : %s" % response.content)
					
					if response.status_code == 200:
						response_data = response.content
						response_xml = etree.fromstring(response_data)
						namespaces = {'ns0': 'http://www.canadapost.ca/ws/authreturn-v2'}
						tracking_pin = response_xml.find('ns0:tracking-pin', namespaces).text
						link_element = response_xml.find(".//ns0:links/ns0:link[@rel='returnLabel']", namespaces)
						if link_element is not None and 'href' in link_element.attrib:
							label_url = link_element.attrib['href']
						# Download the PDF file
						headers_attchment = {'Accept': 'application/pdf'}
						pdf_response = request(method='GET', url=label_url, headers=headers_attchment, auth=(
							self.company_id.ncs_username, self.company_id.ncs_password))
						# _logger.info("Label Response Data  : %s" % pdf_response)
						if pdf_response.status_code == 200:
							pdf_content = pdf_response.content
							res = self.canada_post_return_rate_shipment(picking.sale_id, return_wiz)
							total_price = res['price']
							new_picking.carrier_price = total_price
							new_picking.get_min_cost = total_price
							new_picking.carrier_tracking_ref = tracking_pin
							new_picking.carrier_id = return_wiz.carrier_id
							
							mesage_ept = ("%s Return Shipment Label !<br/> <b>Return Shipment Tracking Number : </b>%s") % (
								return_wiz.carrier_id.name, tracking_pin)
							new_picking.message_post(body=mesage_ept, attachments=[
								('NCS Return Label - %s.PDF' % tracking_pin,
								pdf_content)])
						else:
							print(f"Failed to download the PDF. Status code: {pdf_response.status_code}")
							raise ValidationError("Failed to download the PDF.")
					else:
						# Handle error responses
						print(f"Error {response.status_code}: {response.text}")
						message = f"Failed to generate return label. Error {response.status_code}: {response.text}"
						picking.message_post(body=message)
						raise ValidationError(message)
				except Exception as e:
					error_message = f"Failed to generate return label: {e}"
					print(error_message)
					picking.message_post(body=error_message)
					raise ValidationError(error_message)