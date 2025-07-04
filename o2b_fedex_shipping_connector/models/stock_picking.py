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
import base64
import requests

class StockPicking(models.Model):
	_inherit = 'stock.picking'

	def send_to_shipper(self):
		if self.carrier_id.delivery_type == 'fedex_rest':
			sale_order_id = self.env['sale.order'].search([('id', '=', self.sale_id.id)])
			tracking_number, label_content, carrier_price = self.carrier_id.fedex_create_shipment(self, sale_order_id)
			if label_content:
				if not isinstance(tracking_number, list):
					tracking_number = [str(tracking_number)]
				if len(tracking_number) > 1:
					all_tracking_numbers = ','.join(tracking_number)
				else:
					all_tracking_numbers = tracking_number[0]
				self.carrier_tracking_ref = all_tracking_numbers
				self.carrier_price = carrier_price

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

				elif label_content and label_content.startswith('/tmp/'):
					try:
						with open(label_content, 'rb') as file:
							label_content = base64.b64encode(file.read()).decode('utf-8')
					except Exception as e:
						raise UserError(f"Error reading local label file: {e}")

				if self.carrier_id.fedex_label_file_type == "ZPLII":
					attachment = self.env['ir.attachment'].create({
						'name': 'FedEx Shipping Label.zpl',
						'type': 'binary',
						'datas': label_content,
						'res_model': 'stock.picking',
						'res_id': self.id,
						'mimetype': 'application/zpl',
					})
				else:
					attachment = self.env['ir.attachment'].create({
						'name': 'FedEx Shipping Label.pdf',
						'type': 'binary',
						'datas': label_content,
						'res_model': 'stock.picking',
						'res_id': self.id,
						'mimetype': 'application/pdf',
					})


				self.message_post(body="Shipment created into Fedex<br/>"
									   "<b>Tracking Numbers:</b> %s<br/>" % (all_tracking_numbers),
					  attachment_ids=[attachment.id])
				order_currency = self.sale_id.currency_id or self.company_id.currency_id
				msg = _(
					"Shipment sent to carrier %(carrier_name)s for shipping with tracking number %(ref)s<br/>Cost: %(price).2f %(currency)s",
					carrier_name=self.carrier_id.name,
					ref=self.carrier_tracking_ref,
					price=self.carrier_price,
					currency=order_currency.name
				)
				self.message_post(body=msg)
		else:
			res = super(StockPicking, self).send_to_shipper()

			return res

	def cancel_shipment(self):
		if self.carrier_id.delivery_type == 'fedex_rest':
			self.carrier_id.fedex_cancel_shippment(self)
		res = super(StockPicking, self).cancel_shipment()
		return res



class SaleOrder(models.Model):
	_inherit = 'sale.order'

	fedex_rate = fields.Float(string='Fedex Rate')
