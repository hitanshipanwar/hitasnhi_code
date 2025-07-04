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
from odoo import fields, models, api, _
import base64
from PyPDF2 import PdfFileMerger
import base64
import io

class DeliveryCarrier(models.Model):
	_inherit = 'delivery.carrier'

	carrier_logo = fields.Binary(string="Carrier Logo")
	service_type = fields.Char(string="Service Type")
	weight_unit_custom = fields.Selection([("LB", "LB - pounds"),
                                    ("KG", "KG - kilogram")], string="Weight Unit")


	def generate_custom_label(self, pickings):
		for picking in pickings:
			if picking.show_mo_validation:
				pdf_merger = PdfFileMerger()
				packages = picking.move_line_ids_without_package.mapped('result_package_id')
				if packages:
					for package in packages:
						report_name = 'o2b_stock_api.action_report_custom_shipping_label'
						report_action = self.env.ref(report_name)
						if not report_action:
							raise ValueError(f"Report action {report_name} not found.")
						
						data = {
							'doc': picking,
							'origin': package.name,
							'ship_date': picking.scheduled_date.strftime("%Y-%m-%d"),
							'shipper_name': picking.sale_id.warehouse_id.partner_id.name,
							'shipper_phone': picking.sale_id.warehouse_id.partner_id.phone,
							'shipper_street': picking.sale_id.warehouse_id.partner_id.street,
							'shipper_street2': picking.sale_id.warehouse_id.partner_id.street2,
							"shipper_postalCode": picking.sale_id.warehouse_id.partner_id.zip,
							"shipper_countryCode": picking.sale_id.warehouse_id.partner_id.country_id.code,
							"shipper_city": picking.sale_id.warehouse_id.partner_id.city,
							"shipper_stateOrProvinceCode": picking.sale_id.warehouse_id.partner_id.state_id.code,
							"recipient_name": picking.partner_id.name,
							"recipient_phone": picking.partner_id.phone,
							"recipient_street": picking.partner_id.street,
							"recipient_street2": picking.partner_id.street2,
							"recipient_postalCode": picking.partner_id.zip,
							"recipient_countryCode": picking.partner_id.country_id.code,
							"recipient_city": picking.partner_id.city,
							"recipient_stateOrProvinceCode": picking.partner_id.state_id.code,
							"tracking_num": picking.carrier_tracking_ref,
							"totalWeight": package.shipping_weight,
							"Weight_unit": self.weight_unit_custom,
							"package_length": package.package_type_id.packaging_length,
							"package_width": package.package_type_id.width,
							"package_height": package.package_type_id.height,
							"requestedPackageLineItems": package.name
						}
						pdf, _ = report_action.sudo()._render_qweb_pdf([picking.id], data=data)
						pdf_merger.append(io.BytesIO(pdf))

					merged_pdf = io.BytesIO()
					pdf_merger.write(merged_pdf)
					pdf_merger.close()
					merged_pdf.seek(0)

					attachment = self.env['ir.attachment'].create({
						'name': f'{picking.carrier_id.name} shipping label.pdf',
						'type': 'binary',
						'datas': base64.b64encode(merged_pdf.read()).decode('utf-8'),
						'res_model': 'stock.picking',
						'res_id': picking.id,
						'mimetype': 'application/pdf'
					})

					picking.message_post(
						body="Shipment Created in %s." % picking.carrier_id.name,
						attachment_ids=[attachment.id]
					)

				return True

class ChooseDeliveryCarrier(models.TransientModel):
	_inherit = 'choose.delivery.carrier'

	def button_confirm(self):
		# self = self.with_context(is_unlock=True)
		res = super(ChooseDeliveryCarrier, self).button_confirm()

		return res
