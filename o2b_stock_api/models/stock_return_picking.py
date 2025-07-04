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
from datetime import datetime, timedelta
from odoo.exceptions import AccessError, UserError, ValidationError
import logging
from lxml import etree
import xml.etree.ElementTree as etree
import xml.etree.ElementTree as ET
from odoo.tools.float_utils import float_round

_logger = logging.getLogger(__name__)


class StockReturnPicking(models.TransientModel):
	_inherit = 'stock.return.picking'

	shipping_carrier_ids = fields.One2many('shipping.carrier', 'return_picking_id', string="Delivery Methods")
	carrier_id = fields.Many2one('delivery.carrier', string="Delivery Method", domain="[('id', 'in', available_carrier_ids)]")
	is_return_wiz = fields.Boolean(string="Is Return Wiz")
	available_carrier_ids = fields.Many2many('delivery.carrier', string="Available Carriers", compute="_compute_available_carriers")
	package_qty = fields.Integer(string="Package Count")
	show_mo_validation = fields.Boolean(related='company_id.show_mo_validation')
	is_with_label = fields.Boolean(string='Is with Label', default=lambda self: self.env.context.get('default_is_with_label', False))

	@api.onchange('picking_id')
	def _onchange_picking_id(self):
		res = super(StockReturnPicking, self)._onchange_picking_id()
		if self.show_mo_validation:
			active_id = self.env.context.get('active_id')
			out_picking = self.env['stock.picking'].search([('id', '=', active_id)])
			pick_do = self.env['stock.picking'].search([('sale_id', '=', out_picking.sale_id.id), ("is_pick_sequence", '=', 'PICK')])
			if out_picking.is_pick_sequence == 'OUT':
				self.original_location_id = pick_do.location_id.id
				self.location_id = pick_do.location_id.id
		return res

	@api.depends('shipping_carrier_ids.carrier_id')
	def _compute_available_carriers(self):
		for record in self:
			carrier_ids = record.shipping_carrier_ids.mapped('carrier_id.id')
			record.available_carrier_ids = [(6, 0, carrier_ids)]

	def get_rate(self):
		# self = self.with_context(is_unlock=True)
		active_id = self.env.context.get('active_id')
		out_picking = self.env['stock.picking'].search([('id', '=', active_id)])
		carrier = self.env['delivery.carrier'].search([('name', 'in', ['Free Shipping', 'table.181132', 'Intuitive Shipping'])], limit=1)
		if carrier:
			self.carrier_id = carrier.id

		if self.carrier_id:
			carrier = self.carrier_id
			is_free_shipping = carrier.name in ('Free Shipping','table.181132', 'Intuitive Shipping')
			_logger.info("is_free_shipping***%s" % str(is_free_shipping))
			price_dict = {}
			price_dict_name = {}
			shipping_methods = self.env['delivery.carrier'].search([])
			for package in out_picking.move_line_ids_without_package.mapped('result_package_id'):
				package.with_context(picking_id=out_picking.id)._compute_weight_new()
			canada_post_package_rate_dict = {}
			for shipment in shipping_methods:
				if shipment.delivery_type == 'purolator':
					res = shipment.purolator_return_rate_shipment(out_picking.sale_id, self, out_picking)
					price_dict[shipment.id] = res['price']
					price_dict_name[shipment.name] = res['price']

					base_data = res.get('base_data')
					namespaces = {
						"soapenv": "http://schemas.xmlsoap.org/soap/envelope/",
						"v2": "http://purolator.com/pws/datatypes/v2"
					}
				if shipment.delivery_type == 'fedex_rest':
					res = shipment.fedex_get_shipping_return_rate(out_picking.sale_id, self)
					price_dict[shipment.id] = res
					price_dict_name[shipment.name] = res
				elif shipment.delivery_type == 'canada_post':
					res = shipment.canada_post_return_rate_shipment(out_picking.sale_id, self)
					
					if shipment.id not in price_dict:
						price_dict[shipment.id] = res['price']
						price_dict_name[shipment.name] = res['price']
					else:
						price_dict[shipment.id] = price_dict[shipment.id] + res['price']
						price_dict_name[shipment.name] = price_dict_name[shipment.name] + res['price']
			self.carrier_id = False
			if price_dict:
				existing_records = self.env['shipping.carrier'].search([
					('return_picking_id', '=', self.id),
					('carrier_id', 'in', list(price_dict.keys()))
				])

				existing_dict = {(record.return_picking_id.id, record.carrier_id.id) for record in existing_records}

				carrier_values = []

				for carrier_id, min_cost in price_dict.items():
					existing_record = existing_records.filtered(lambda rec: rec.carrier_id.id == carrier_id)
					if existing_record:
						existing_record.write({'min_cost': min_cost})
					else:
						carrier_values.append({
							'return_picking_id': self.id,
							'min_cost': min_cost,
							'carrier_id': carrier_id,
						})

				if carrier_values:
					self.env['shipping.carrier'].create(carrier_values)
				
		return {
			'type': 'ir.actions.act_window',
			'res_model': 'stock.return.picking',
			'view_mode': 'form',
			'res_id': self.id,
			'target': 'new',
			'context': self.env.context,
		}


	def _create_returns(self):
		if self.show_mo_validation and not self.carrier_id and not self.is_return_wiz and self.is_with_label:
			raise ValidationError("Please provide delivery method.")
		# res = super(StockReturnPicking, self)._create_returns()
		# Prevent copy of the carrier and carrier price when generating return picking
		# (we have no integration of returns for now)
		new_picking, pick_type_id = super(StockReturnPicking, self)._create_returns()
		picking = self.env['stock.picking'].browse(new_picking)
		if picking and self.show_mo_validation:
			picking.move_line_ids_without_package.write({'package_id': False})
			picking.move_line_ids_without_package.write({'result_package_id': False})
		active_id = self.env.context.get('active_id')
		out_picking = self.env['stock.picking'].search([('id', '=', active_id)])
		pick_do = self.env['stock.picking'].search([('sale_id', '=', picking.sale_id.id), ("is_pick_sequence", '=', 'PICK')])
		if not self.env.context.get('skip_return_labels'):
			if self.carrier_id.delivery_type == 'canada_post':
				self.carrier_id.canada_post_return_shipment(out_picking, picking, self)
				picking.is_return_picking = True
			if self.carrier_id.delivery_type == 'purolator':
				self.carrier_id.purolator_create_return_shipment(out_picking, picking, self)
				picking.is_return_picking = True
			if self.carrier_id.delivery_type == 'fedex_rest':
				self.carrier_id.fedex_return_shippment(out_picking, out_picking.sale_id, picking, self)
				picking.is_return_picking = True
		return new_picking, pick_type_id


class ShippingCarrier(models.TransientModel):
	_name = 'shipping.carrier'

	return_picking_id = fields.Many2one('stock.return.picking',string='Return Picking')
	min_cost = fields.Float(string='Minimum Cost')
	carrier_id = fields.Many2one('delivery.carrier', string='Delivery Method')


class ReturnPickingLine(models.TransientModel):
	_inherit = "stock.return.picking.line"

	show_mo_validation = fields.Boolean(related='move_id.company_id.show_mo_validation')
	is_with_label = fields.Boolean(string='Is with Label', default=lambda self: self.env.context.get('default_is_with_label', False))

	@api.constrains('quantity')
	def _check_quantity(self):
		for line in self:
			if line.show_mo_validation and not line.is_with_label:
				if not line.move_id:
					continue
				quantity = line.move_id.product_qty
				for move in line.move_id.move_dest_ids:
					if not move.origin_returned_move_id or move.origin_returned_move_id != line.move_id:
						continue
					if move.state in ('partially_available', 'assigned'):
						quantity -= sum(move.move_line_ids.mapped('product_qty'))
					elif move.state in ('done'):
						quantity -= move.product_qty
				quantity = float_round(quantity, precision_rounding=line.move_id.product_id.uom_id.rounding)
				if line.move_id:
					if quantity != 0:
						if line.quantity > quantity:
							raise ValidationError("Return quantity cannot exceed the ordered quantity.")
