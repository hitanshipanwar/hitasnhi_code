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
from html import escape
from datetime import datetime, timedelta
from odoo.exceptions import AccessError, UserError, ValidationError
from lxml import etree
from odoo.tools.float_utils import float_compare, float_is_zero, float_round
from odoo.tools.misc import format_date
import logging
import base64

_logger = logging.getLogger(__name__)


class StockPicking(models.Model):
	_inherit = 'stock.picking'

	get_min_cost = fields.Float(string="Get Min. Delivery Charge", copy=False)
	shippment_comparison_rate = fields.Html(string="Shippment Comparison Rates", copy=False)
	barcode = fields.Char(string="Barcode")
	selected_package_id = fields.Many2one("stock.quant.package", string="Selected Package")
	selected_package_type_id = fields.Many2one(related='selected_package_id.package_type_id')
	is_pick_sequence = fields.Char(
		related='picking_type_id.sequence_code',
		string='Is PICK Sequence'
	)
	time_tracking_ids = fields.One2many('time.tracking', 'picking_id', string="Time Tracking")
	total_time_taken = fields.Char(string="Total Time Taken", compute="_compute_total_time_taken")
	carrier_id_name = fields.Char(related="carrier_id.name")
	note = fields.Html('Notes', related="sale_id.note", readonly=True, tracking=True)
	x_studio_field_F7ZDy = fields.Char(string="Customer Service Notes", tracking=True)
	x_studio_permanent_customer_notes = fields.Html(string="Premanent Customer Notes", related="partner_id.comment", readonly=True, tracking=True)
	shopify_instance_id = fields.Many2one("shopify.instance.ept", "Shopify Instance")
	tracking_num = fields.Char(string="CanadaPost Shipment-Id")
	is_reverted = fields.Boolean(string="Reverted")
	show_mo_validation = fields.Boolean(related='company_id.show_mo_validation')
	has_po_box_address = fields.Boolean(string="PO Box Address", default=False)
	carrier_id = fields.Many2one("delivery.carrier", string="Carrier", check_company=True, tracking=True)

	def action_open_return_with_label(self):
		"""Open Reverse Transfer form with is_with_label set to True"""
		return {
			'type': 'ir.actions.act_window',
			'name': 'Reverse Transfer (With Label)',
			'res_model': 'stock.return.picking',
			'view_mode': 'form',
			'context': {'default_is_with_label': True},
			'target': 'new',
		}

	def action_open_return_without_label(self):
		"""Open Reverse Transfer form with is_with_label set to False"""
		return {
			'type': 'ir.actions.act_window',
			'name': 'Reverse Transfer (Without Label)',
			'res_model': 'stock.return.picking',
			'view_mode': 'form',
			'context': {'default_is_with_label': False},
			'target': 'new',
		}

	def action_open_return_eo_company(self):
		"""Open Reverse Transfer form with is_with_label set to False"""
		return {
			'type': 'ir.actions.act_window',
			'name': 'Reverse Transfer (Without Label)',
			'res_model': 'stock.return.picking',
			'view_mode': 'form',
			'context': {'default_is_with_label': False},
			'target': 'new',
		}

	@api.model
	def create(self, vals):
		res = super(StockPicking, self).create(vals)
		po_box_keywords = [
			'po box', 'p.o. box', 'box', 'pobox', 'po boxes', 
			'po', 'boxes', 'po.box', 'po-box', 'po.boxes', 'po-boxes'
		]
		for picking in res:
			if picking.show_mo_validation:
				if picking.partner_id.street:
					address = picking.partner_id.street.lower()
					if any(keyword in address for keyword in po_box_keywords):
						picking.has_po_box_address = True
					else:
						picking.has_po_box_address = False
				else:
					picking.has_po_box_address = False
			else:
				picking.has_po_box_address = False
		return res

	@api.onchange('partner_id')
	def check_po_box_address(self):
		po_box_keywords = [
			'po box', 'p.o. box', 'box', 'pobox', 'po boxes', 
			'po', 'boxes', 'po.box', 'po-box', 'po.boxes', 'po-boxes'
		]
		for picking in self:
			if picking.show_mo_validation:
				if picking.partner_id.street:
					address = picking.partner_id.street.lower()
					if any(keyword in address for keyword in po_box_keywords):
						picking.has_po_box_address = True
					else:
						picking.has_po_box_address = False
				else:
					picking.has_po_box_address = False
			else:
				picking.has_po_box_address = False

	@api.model
	def fields_view_get(self, view_id=None, view_type='tree', toolbar=False, submenu=False):
		res = super(StockPicking, self).fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu)
		
		if view_type == 'search' and self.env.company.show_mo_validation:
			doc = etree.XML(res['arch'])
			my_transfers_node = doc.xpath("//search/filter[@name='my_transfers']")
			if my_transfers_node:
				po_box_filter = etree.Element('filter', 
											  string="PO Box Address", 
											  name="is_po_box_outbound", 
											  domain="[('has_po_box_address', '=', True)]")
				my_transfers_node[0].addnext(po_box_filter)
			res['arch'] = etree.tostring(doc, encoding='unicode')
		return res

		
	@api.depends('move_line_ids.result_package_id', 'move_line_ids.result_package_id.shipping_weight', 'weight_bulk')
	def _compute_shipping_weight(self):
		res = super(StockPicking, self)._compute_shipping_weight()
		for picking in self:
			if picking.is_pick_sequence != 'IN':
				if picking.package_ids:
					picking.shipping_weight = picking.weight_bulk + sum([pack.shipping_weight or pack.weight for pack in picking.package_ids])
				else:
					picking.shipping_weight = picking.weight
			else:
				picking.shipping_weight = picking.weight

		return res

	@api.onchange('x_studio_field_F7ZDy')
	def onchange_x_studio_field_F7ZDy(self):
		if self.sale_id:
			delivery_order = self.env['stock.picking'].search([('sale_id', '=', self.sale_id.id)])
			for order in delivery_order:
					order.x_studio_field_F7ZDy = self.x_studio_field_F7ZDy

	def button_validate(self):
		# self = self.with_context(is_unlock=True)
		for rec in self:
			if rec.picking_type_id and rec.picking_type_id.code == 'outgoing':
				if rec.scheduled_date and rec.scheduled_date < datetime.now():
					rec.scheduled_date = datetime.now()
				if rec.sale_id:
					picking = self.env['stock.picking'].search([('sale_id', '=', rec.sale_id.id), ('id', '!=', rec.id), ('is_reverted', '=', False)])
					picking.carrier_id = rec.carrier_id.id
				if rec.show_mo_validation and rec.carrier_id and rec.carrier_id.delivery_type == 'fixed' and rec.carrier_id.name not in ['Free Shipping','table.181132', 'Intuitive Shipping']:
					rec.carrier_id.generate_custom_label(rec)
		res = super(StockPicking, self).button_validate()

		for rec in self:
			if rec.picking_type_id.sequence_code == 'OUT':
				if rec.carrier_id.delivery_type == 'canada_post' and rec.carrier_id.ncs_manifest:
					rec.carrier_id.get_canadapost_manifest(rec)
			if rec.picking_type_id and rec.picking_type_id.code == 'outgoing' and rec.carrier_id.delivery_type in ['fedex_rest', 'canada_post', 'purolator'] and rec.picking_type_id.sequence_code == 'OUT':
				attachments = self.env['ir.attachment'].search([('res_id', '=', rec.id), ('res_model', '=', 'stock.picking')]).filtered(lambda attc: 'Manifest' not in attc.name and 'FedEx Shipping Label.zpl' not in attc.name)
				ncs_manifest_label = self.env['ir.attachment'].search([('res_id', '=', rec.id), ('res_model', '=', 'stock.picking'),('name', '=', 'NCS Manifest.PDF')])
				zpl_lable = self.env['ir.attachment'].search([('res_id', '=', rec.id), ('res_model', '=', 'stock.picking'),('name', '=', 'FedEx Shipping Label.zpl')])
				_logger.info("zpl_lable***%s" % str(zpl_lable))
				if attachments:
					for attachment in attachments:
						current_user = self.env.user
						printer_obj = current_user.printing_printer_id
						if printer_obj:
							datas= attachment.datas
							datas = base64.b64decode(datas)
							printer = printer_obj.sudo().print_document(report=None, content=datas, doc_format='Application/PDF')
				if ncs_manifest_label and rec.carrier_id.print_ncs_manifest:
					for ncs in ncs_manifest_label:
						current_user = self.env.user
						printer_obj = current_user.printing_printer_id
						if printer_obj:
							datas= ncs.datas
							datas = base64.b64decode(datas)
							printer = printer_obj.sudo().print_document(report=None, content=datas, doc_format='Application/PDF')
				if zpl_lable:
					for zpl in zpl_lable:
						current_user = self.env.user
						printer_obj = current_user.printing_printer_id
						if printer_obj:
							datas= zpl.datas
							datas = base64.b64decode(datas)
							printer = printer_obj.sudo().print_document(report=None, content=datas, doc_format='raw')
							_logger.info("printer***%s" % str(printer))

			if rec.show_mo_validation and rec.picking_type_id.sequence_code == 'OUT' and rec.carrier_id and rec.carrier_id.delivery_type == 'fixed' and rec.carrier_id.name not in ['Free Shipping','table.181132', 'Intuitive Shipping']:
				attachments = self.env['ir.attachment'].search([('res_id', '=', rec.id), ('res_model', '=', 'stock.picking')])
				_logger.info("Attachments***%s" % attachments)
				if attachments:
					for attachment in attachments:
						current_user = self.env.user
						printer_obj = current_user.printing_printer_id
						if printer_obj:
							datas= attachment.datas
							datas = base64.b64decode(datas)
							printer = printer_obj.sudo().print_document(report=None, content=datas, doc_format='Application/PDF')
							_logger.info("printer***%s" % str(printer))

		return res

	def _set_scheduled_date(self):
		for picking in self:
			if picking.state in ('cancel'):
				raise UserError(_("You cannot change the Scheduled Date on a done or cancelled transfer."))
			picking.move_lines.write({'date': picking.scheduled_date})
			

	def _get_fields_stock_barcode(self):
		""" List of fields on the stock.picking object that are needed by the
		client action. The purpose of this function is to be overridden in order
		to inject new fields to the client action.
		"""
		results = super(StockPicking, self)._get_fields_stock_barcode()
		results.append('selected_package_id')
		results.append('selected_package_type_id')
		return results
		# return [
		#     'move_line_ids',
		#     'picking_type_id',
		#     'location_id',
		#     'location_dest_id',
		#     'name',
		#     'state',
		#     'picking_type_code',
		#     'company_id',
		#     'immediate_transfer',
		#     'note',
		#     'picking_type_entire_packs',
		#     'use_create_lots',
		#     'use_existing_lots',
		# ]

	@api.depends('time_tracking_ids.time_taken')
	def _compute_total_time_taken(self):
		for rec in self:
			total_seconds = 0
			for line in rec.time_tracking_ids:
				if line.time_taken:
					time_parts = line.time_taken.split(':')
					hours, minutes, seconds = map(int, time_parts)
					total_seconds += hours * 3600 + minutes * 60 + seconds

			total_hours, remainder = divmod(total_seconds, 3600)
			total_minutes, total_seconds = divmod(remainder, 60)
			
			total_time = '{:02}:{:02}:{:02}'.format(int(total_hours), int(total_minutes), int(total_seconds))

			rec.total_time_taken = total_time

			
	# @api.model
	def get_tracking_data(self):
		for rec in self:
			if rec.scheduled_date and rec.scheduled_date < datetime.now():
				rec.scheduled_date = datetime.now()
			for line in rec.time_tracking_ids:
				if line.picking_id.id == rec.id:
					end_time = datetime.now()
					time_difference = end_time - line.start_time
					total_seconds = time_difference.total_seconds()
					hours, remainder = divmod(total_seconds, 3600)
					minutes, seconds = divmod(remainder, 60)
					line.write({
						'end_time': datetime.now(),
						'time_taken': '{:02}:{:02}:{:02}'.format(int(hours), int(minutes), int(seconds))
						})

	def add_packages_to_base_data(self, base_data, package_names):
		namespaces = {"ns": "http://www.canadapost.ca/ws/ship/rate-v3"}
		root = etree.fromstring(base_data.encode("utf-8"))
		parcel_characteristics = root.find(".//ns:parcel-characteristics", namespaces=namespaces)
		if parcel_characteristics is not None:
			for package_name in package_names:
				if package_name:
					new_package = etree.SubElement(parcel_characteristics, "package")
					new_package.text = package_name
		updated_base_data = etree.tostring(root, pretty_print=True).decode("utf-8")
		
		return updated_base_data


	def get_min_delivery_chrg(self):
		# self = self.with_context(is_unlock=True)
		for rec in self:
			if rec.picking_type_id and rec.picking_type_id.sequence_code == 'OUT' and not rec.carrier_tracking_ref:
				if rec.sale_id and rec.sale_id.carrier_id:
					carrier = rec.sale_id.carrier_id
					is_free_shipping = carrier.name in ('Free Shipping','table.181132', 'Intuitive Shipping')
					_logger.info("is_free_shipping***%s" % str(is_free_shipping))
					# if is_free_shipping:
					price_dict = {}
					price_dict_name = {}
					shipping_methods = self.env['delivery.carrier'].search([])
					if not is_free_shipping and rec.carrier_id:
						shipping_methods = rec.carrier_id
					elif not is_free_shipping and rec.sale_id.carrier_id:
						shipping_methods = rec.sale_id.carrier_id
					for package in rec.move_line_ids_without_package.mapped('result_package_id'):
						package.with_context(picking_id=rec.id)._compute_weight_new()
					_logger.info("shipping_methods***%s" % shipping_methods)
					canada_post_package_rate_dict = {}
					for shipment in shipping_methods:
						if shipment.delivery_type == 'purolator':
							result_package_ids = rec.move_line_ids_without_package.mapped('result_package_id')
							res = shipment.with_context(packages=result_package_ids).purolator_rate_shipment(rec.sale_id)
							price_dict[shipment.id] = res['price']
							price_dict_name[shipment.name] = res['price']

							base_data = res.get('base_data')
							namespaces = {
								"soapenv": "http://schemas.xmlsoap.org/soap/envelope/",
								"v2": "http://purolator.com/pws/datatypes/v2"
							}
							root = etree.fromstring(base_data)
							package_type = root.find(".//v2:TotalWeight", namespaces=namespaces)
							if package_type is not None:
								package_names = [line.result_package_id.name for line in rec.move_line_ids_without_package.filtered(lambda pack: pack.result_package_id)]
								for package_name in package_names:
									if package_name:
										new_package = etree.SubElement(package_type, "{http://purolator.com/pws/datatypes/v2}Package")
										new_package.text = package_name
							updated_base_data = etree.tostring(root, pretty_print=True).decode("utf-8")
							base_data = updated_base_data
						elif shipment.delivery_type == 'fedex_rest':
							result_package_ids = rec.move_line_ids_without_package.mapped('result_package_id')
							res = shipment.with_context(packages=result_package_ids).fedex_get_shipping_rate(rec.sale_id)
							if isinstance(res, dict):
								self.env.cr.commit()
								rec.message_post(body=res['warning'])
								self.env.cr.commit()
								raise ValidationError(res['warning'])
							else:
								price_dict[shipment.id] = res
								price_dict_name[shipment.name] = res
						elif shipment.delivery_type == 'canada_post':
							package_names = [line.result_package_id.name for line in rec.move_line_ids_without_package.filtered(lambda pack: pack.result_package_id)]
							non_false_packages = {name for name in package_names if name}  # Convert list to set to remove duplicates
							count_non_false_packages = len(non_false_packages)
							# canada_post_package_rate_dict = {}
							for package in rec.move_line_ids_without_package.mapped('result_package_id'):
								# res = shipment.canada_post_rate_shipment(rec.sale_id)
								res = shipment.canada_post_package_rate(rec.sale_id, package)
								if res['error_message']:
									self.env.cr.commit()
									rec.message_post(body=res['error_message'])
									self.env.cr.commit()
									raise ValidationError(res['error_message'])
								else:
									if shipment.id not in price_dict:
										price_dict[shipment.id] = res['price']
										price_dict_name[shipment.name] = res['price']
									else:
										price_dict[shipment.id] = price_dict[shipment.id] + res['price']
										price_dict_name[shipment.name] = price_dict_name[shipment.name] + res['price']
									if shipment.id not in canada_post_package_rate_dict:
										canada_post_package_rate_dict[shipment.id] = {package.name : res['price']}
									else:
										vals = canada_post_package_rate_dict[shipment.id]
										vals[package.name] = res['price']
										canada_post_package_rate_dict[shipment.id] = vals
									_logger.info("canada_post_package_rate_dict***%s" % str(canada_post_package_rate_dict))
									# shipment_weight = shipment.ncs_product_packaging_id.max_weight
									# shipper_address = rec.sale_id.warehouse_id.partner_id
									# recipient_address = rec.sale_id.partner_shipping_id
									# total_weight = sum([(line.product_id.weight * line.product_uom_qty) for line in rec.sale_id.order_line if not line.is_delivery])
									# result_dict = shipment.ncs_canada_post_get_shipping_rate(shipper_address, recipient_address, total_weight, picking_bulk_weight=False,
									# 		  packages=False, declared_value=False, declared_currency=False,
									# 		  company_id=False)
									# base_data = result_dict.get('base_data')
									# package_names = [line.result_package_id.name for line in rec.move_line_ids_without_package.filtered(lambda pack: pack.result_package_id)]

									# updated_base_data = self.add_packages_to_base_data(base_data, package_names)
									# base_data = updated_base_data
					if price_dict:
						min_shipment_id = min(price_dict, key=price_dict.get)
						min_price = price_dict[min_shipment_id]
						# if min_price:
						rec.get_min_cost = min_price
						rec.carrier_id = min_shipment_id
						if rec.get_min_cost:
							unique_packages = {}
							for line in rec.move_line_ids_without_package:
								package = line.result_package_id
								if package and package.name not in unique_packages:
									unique_packages[package.name] = package.id
							message = (
								"From all available shipments, we chose the minimum cost:<br/>"
								+ "<br/>".join([f"{escape(key)}: {escape(str(value))}" for key, value in price_dict_name.items()])
							)
							if not is_free_shipping:
								message = (
									"<br/>".join([f"{escape(key)}: {escape(str(value))}" for key, value in price_dict_name.items()])
								)
							package_links = "<br/>".join(
								[
									f'<a href="/web#id={unique_packages[package_name]}&model=stock.quant.package&view_type=form">{escape(package_name)}</a>'
									for package_name in unique_packages.keys()
								]
							)
							if len(canada_post_package_rate_dict):
								_logger.info("canada_post_package_rate_dict***%s" % str(canada_post_package_rate_dict))
								_logger.info("min_shipment_id***%s" % str(min_shipment_id))
								if min_shipment_id in canada_post_package_rate_dict:
									canada_post_package_rate_val = canada_post_package_rate_dict.get(min_shipment_id)
									_logger.info("canada_post_package_rate_val***%s" % str(canada_post_package_rate_val))
									package_links = "<br/>".join(
										[
											f'<a href="/web#id={unique_packages[package_name]}&model=stock.quant.package&view_type=form">{escape(package_name)}</a>: {canada_post_package_rate_val[package_name]}'
											for package_name in unique_packages.keys()
										]
									)
								# package_rate_message = (
								# 	"<br/>Package rate for canadapost:<br/>"
								# 	+ "<br/>".join([f"{escape(key)}: {escape(str(value))}" for key, value in canada_post_package_rate_val.items()])
								# )
								# message += package_rate_message
							comparison_rate = (
								"<br/>".join([f"{escape(key)}: {escape(str(value))}" for key, value in price_dict_name.items()])
							)
							rec.shippment_comparison_rate = comparison_rate
							message += "<br/>Packages:<br/>" + package_links
							rec._message_log(body=message)
	# @api.model
	def on_barcode_get_rate_scanned(self):
		picking = self
		if not picking:
			raise ValidationError("No matching stock picking found for this barcode.")
		picking.get_min_delivery_chrg()
		return {
			'message': 'Barcode processed successfully.',
			'picking_id': self.id,
		}

	def action_select_package(self):
		package = False
		for pick in self:
			move_lines_to_pack = self.env['stock.move.line']
			if not pick.selected_package_id:
				package = self.env['stock.quant.package'].create({})
				pick.selected_package_id = package.id
			else:
				# package = pick.selected_package_id
				res = self.action_put_in_pack()
				# package = self.env['stock.quant.package'].create({})
				# pick.selected_package_id = package.id
				return res
		return package

	def _put_in_pack_new(self, package, move_line_ids, create_package_level=True):
		# package = False
		for pick in self:
			total_weight = 0
			move_lines_to_pack = self.env['stock.move.line']
			for line in move_line_ids:
				qty_done = line.qty_done if line.qty_done > 0 else line.product_uom_qty
				line_weight = line.product_id.weight * qty_done
				total_weight += line_weight
			if not package:
				package = self.env['stock.quant.package'].create({
					'shipping_weight': total_weight
					})

			precision_digits = self.env['decimal.precision'].precision_get('Product Unit of Measure')
			if float_is_zero(move_line_ids[0].qty_done, precision_digits=precision_digits):
				for line in move_line_ids:
					line.qty_done = line.product_uom_qty

			for ml in move_line_ids:
				if float_compare(ml.qty_done, ml.product_uom_qty,
								 precision_rounding=ml.product_uom_id.rounding) >= 0:
					move_lines_to_pack |= ml
				else:
					quantity_left_todo = float_round(
						ml.product_uom_qty - ml.qty_done,
						precision_rounding=ml.product_uom_id.rounding,
						rounding_method='UP')
					done_to_keep = ml.qty_done
					new_move_line = ml.copy(
						default={'product_uom_qty': 0, 'qty_done': ml.qty_done})
					vals = {'product_uom_qty': quantity_left_todo, 'qty_done': 0.0}
					if pick.picking_type_id.code == 'incoming':
						if ml.lot_id:
							vals['lot_id'] = False
						if ml.lot_name:
							vals['lot_name'] = False
					ml.write(vals)
					new_move_line.write({'product_uom_qty': done_to_keep})
					move_lines_to_pack |= new_move_line
			if not package.package_type_id:
				package_type = move_lines_to_pack.move_id.product_packaging_id.package_type_id
				if len(package_type) == 1:
					package.package_type_id = package_type
			if len(move_lines_to_pack) == 1:
				default_dest_location = move_lines_to_pack._get_default_dest_location()
				move_lines_to_pack.location_dest_id = default_dest_location._get_putaway_strategy(
					product=move_lines_to_pack.product_id,
					quantity=move_lines_to_pack.product_uom_qty,
					package=package)
			move_lines_to_pack.write({
				'result_package_id': package.id,
			})
			if create_package_level:
				package_level = self.env['stock.package_level'].create({
					'package_id': package.id,
					'picking_id': pick.id,
					'location_id': False,
					'location_dest_id': move_lines_to_pack.mapped('location_dest_id').id,
					'move_line_ids': [(6, 0, move_lines_to_pack.ids)],
					'company_id': pick.company_id.id,
				})
		# package.shipping_weight = package.weight
		return package

	def action_put_in_pack(self):
		self.ensure_one()
		if self.state not in ('done', 'cancel'):
			picking_move_lines = self.move_line_ids
			if (
				not self.picking_type_id.show_reserved
				and not self.immediate_transfer
				and not self.env.context.get('barcode_view')
			):
				picking_move_lines = self.move_line_nosuggest_ids

			move_line_ids = picking_move_lines.filtered(lambda ml:
				float_compare(ml.qty_done, 0.0, precision_rounding=ml.product_uom_id.rounding) > 0
				and not ml.result_package_id
			)
			if not move_line_ids:
				move_line_ids = picking_move_lines.filtered(lambda ml: float_compare(ml.product_uom_qty, 0.0,
									 precision_rounding=ml.product_uom_id.rounding) > 0 and float_compare(ml.qty_done, 0.0,
									 precision_rounding=ml.product_uom_id.rounding) == 0)
			if move_line_ids:
				# res = self._pre_put_in_pack_hook(move_line_ids)
				# if not res:
				package = self.selected_package_id
				res = self._put_in_pack_new(package, move_line_ids)
				if not res.package_type_id and 'default_package_type_id' in self.env.context and self.env.context.get('default_package_type_id'):
					res.package_type_id = self.env.context.get('default_package_type_id')

				self.selected_package_id = False
				# res.shipping_weight = res.weight
				self.shipping_weight = res.shipping_weight
				return res
			else:
				raise UserError(_("Please add 'Done' quantities to the picking to create a new pack."))

	def action_regenerate_shipping_label(self):
		# self = self.with_context(is_unlock=True)
		for rec in self:
			if rec.show_mo_validation:
				if rec.is_pick_sequence == 'OUT':
					if rec.state == 'done':
						carrier = rec.sale_id.carrier_id
						is_free_shipping = carrier.name in ('Free Shipping','table.181132', 'Intuitive Shipping')
						if is_free_shipping:
							rec.get_min_delivery_chrg()
						if rec.carrier_id.delivery_type == 'fedex_rest':
							if rec.carrier_tracking_ref:
								rec.carrier_id.fedex_cancel_shippment(rec)
							rec.send_to_shipper()
							rec.manually_update_shipment()
						elif rec.carrier_id.delivery_type == 'purolator':
							if rec.carrier_tracking_ref:
								rec.carrier_id.purolator_cancel_shipment(rec)
							rec.carrier_id.purolator_send_shipping(rec)
							rec.manually_update_shipment()
						elif rec.carrier_id.delivery_type == 'canada_post':
							if rec.carrier_tracking_ref:
								rec.carrier_id.canada_post_cancel_shipment(rec)
							rec.carrier_id.canada_post_send_shipping(rec)
							rec.manually_update_shipment()
							if rec.carrier_id.ncs_manifest:
								rec.carrier_id.get_canadapost_manifest(rec)
					else:
						raise ValidationError(_("You can only Re-generate labels for validated delivery orders."))
				else:
					raise ValidationError(_("You can only Re-generate labels from 'OUT' delivery order."))
			else:
				raise ValidationError('Regenerating shipping labels is not allowed for your company.')


	def action_revert(self):
		for picking in self:
			if picking.state != 'done':
				raise UserError(('You can only revert a done picking.'))

			return_wizard = self.env['stock.return.picking'].with_context(skip_return_labels=True).create({
				'picking_id': picking.id,
				'move_dest_exists': False,
				'original_location_id': picking.location_dest_id.id,
				'parent_location_id': picking.location_dest_id.location_id.id,
				'location_id': picking.location_id.id,
			})

			return_wizard_lines = []
			for move in picking.move_lines:
				return_wizard_lines.append((0, 0, {
					'product_id': move.product_id.id,
					'quantity': move.quantity_done,
					'move_id': move.id,
					'to_refund': True,
				}))
			return_wizard.product_return_moves = return_wizard_lines

			return_wizard.is_return_wiz = True
			return_picking_id, _ = return_wizard._create_returns()
			return_picking = self.env['stock.picking'].browse(return_picking_id)
			if return_picking:
				return_picking.is_reverted = True
				picking.is_reverted = True

			pick_do = self.env['stock.picking'].search([('sale_id', '=', picking.sale_id.id), ('is_pick_sequence', '=', 'PICK')])
			if pick_do:
				pick_do.is_reverted = True

			for move_line in return_picking.move_line_ids:
				self.env['stock.move.line'].create({
					'move_id': move_line.move_id.id,
					'product_id': move_line.product_id.id,
					'product_uom_id': move_line.product_uom_id.id,
					'location_id': move_line.location_id.id,
					'location_dest_id': move_line.location_dest_id.id,
					'qty_done': move_line.product_uom_qty,
					'picking_id': return_picking.id,
				})
				
			return_picking.action_confirm()
			return_picking.action_assign()
			return_picking.button_validate()
			picking.message_post(body=('The out delivery order has been reverted'))

			new_picking = picking.copy({
				'move_lines': [],
				'state': 'draft',
				'is_reverted': False,
				'carrier_id': picking.sale_id.carrier_id.id,
				'origin': picking.origin,
				'move_type': picking.move_type,
				'location_id': picking.location_id.id,
				'location_dest_id': picking.location_dest_id.id,
			})

			for move in picking.move_lines:
				new_move = move.copy({
					'picking_id': new_picking.id,
					'state': 'draft',
					'quantity_done': 0,
					'procure_method': 'make_to_stock',
					'location_id': picking.location_id.id,
					'location_dest_id': picking.location_dest_id.id,
				})
				new_picking.write({'move_lines': [(4, new_move.id)]})

			new_picking.action_confirm()
			new_picking.action_assign()
			new_picking.message_post(body=("New outgoing delivery order created by revert action."))

			return {
				'type': 'ir.actions.act_window',
				'name': ('New Delivery Order'),
				'view_mode': 'form',
				'res_model': 'stock.picking',
				'res_id': new_picking.id,
				'target': 'current',
			}

class StockMove(models.Model):
	_inherit = 'stock.move'

	x_studio_coo = fields.Char()
	x_studio_po_line_lotnotes_1 = fields.Char()
	x_studio_organic_status = fields.Char()

class StockQuantPackage(models.Model):
	_inherit = "stock.quant.package"

	def _compute_weight_new(self):
		for package in self:
			weight = 0.0
			if self.env.context.get('picking_id'):
				# TODO: potential bottleneck: N packages = N queries, use groupby ?
				current_picking_move_line_ids = self.env['stock.move.line'].search([
					('result_package_id', '=', package.id),
					('picking_id', '=', self.env.context['picking_id'])
				])
				for ml in current_picking_move_line_ids:
					weight += ml.product_uom_id._compute_quantity(
						ml.qty_done, ml.product_id.uom_id) * ml.product_id.weight
			else:
				for quant in package.quant_ids:
					weight += quant.quantity * quant.product_id.weight
			package.shipping_weight = weight

class TimeTaking(models.Model):
	_name  = 'time.tracking'
	_description = 'Time Tracking'

	s_no = fields.Char(string="S.No.")
	picking_id = fields.Many2one('stock.picking', string="Picking ID", required=True)
	employee_id = fields.Many2one('hr.employee')
	start_time = fields.Datetime(string="Start Time")
	end_time = fields.Datetime(string="End Time")
	time_taken = fields.Char(string="Time Taken")
