# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError

class StockPicking(models.Model):
	_inherit = 'stock.picking'

	machship_cons_id = fields.Integer('Machship Cons. ID', copy=False)
	machship_status = fields.Char('MachShip Status', copy=False)
	machship_cons_number = fields.Char('Consignment #', copy=False)
	pen_cons = fields.Boolean('Pending Cons#', copy=False)
	tracking_url = fields.Char('Tracking Link', copy=False)

	def create_cons_machship(self):
		self.ensure_one()
		if not self.delivery_type == 'machship':
			raise UserError(_("Consignment can only be created for MachShip delivery orders"))
		if not self.package_ids:
			raise UserError(_("Please assign packages before processing"))
		return self.carrier_id.create_cons(self)

	@api.model
	def get_machship_status(self):
		#Cron function to update MachShip status
		picking_ids = self.search([('delivery_type', '=', 'machship'),
								   ('machship_cons_id', '!=', 0),
								   ('machship_status', '!=', 'Complete'),
								   ('pen_cons', '=', False)])
		for picking in picking_ids:
			if picking.carrier_id:
				picking.carrier_id.get_cons_status(picking)

	@api.model
	def process_complete_do(self):
		#Cron Job to process completed delivery orders
		picking_ids = self.search([('delivery_type', '=', 'machship'),
								   ('machship_cons_id', '!=', 0),
								   ('machship_status', '=', 'Complete'),
								   ('state', '=', 'assigned'),
								   ('pen_cons', '=', False)])
		for picking in picking_ids:
			picking.with_context(skip_backorder=True).button_validate()

	@api.model
	def check_pending_con_order_status(self):
		#Cron to check pending consignment status
		picking_ids = self.search([('delivery_type', '=', 'machship'),
								   ('machship_cons_id', '!=', 0),
								   ('carrier_tracking_ref', '=', False),
								   ('machship_cons_number', '!=', False),
								   ('pen_cons', '=', True)])
		for picking in picking_ids:
			picking.carrier_id.get_pen_cons_status(picking)

class StockMove(models.Model):
	_inherit = 'stock.move'

	def _get_new_picking_values(self):
		res = super(StockMove, self)._get_new_picking_values()
		partners = self.mapped('partner_id')
		location = self.mapped('location_dest_id')
		if location.usage == 'customer' and partners:
			carrier_id = partners[0].property_delivery_carrier_id and partners[0].property_delivery_carrier_id.id or False
			if not carrier_id:
				carrier_ids = self.env['delivery.carrier'].search([('delivery_type', '=', 'machship'), ('chep_fast', '!=', False)])
				if carrier_ids:
					carrier_id = carrier_ids[0].id
			res['carrier_id'] = carrier_id
		return res


class AccountMove(models.Model):
	_inherit = 'account.move'

	carrier_id = fields.Many2one('delivery.carrier',string='Carrier', copy=False, compute='get_tracking_link',inverse='_inverse_carrier')
	carrier_tracking_ref = fields.Char('Tracking Referance', copy=False, compute='get_tracking_link', inverse='_inverse_tracking_ref')
	machship_cons_number = fields.Char('Consignment #', copy=False ,compute='get_tracking_link', inverse='_inverse_cons_number')
	pen_cons = fields.Boolean('Pending Cons#', copy=False)
	tracking_url = fields.Char('Tracking Link', copy=False, store=True, compute='get_tracking_link' , inverse='_inverse_tracking_link')

	@api.depends('tracking_url','carrier_id','carrier_tracking_ref','machship_cons_number')
	def get_tracking_link(self):
		for record in self:
			sale_lines = record.invoice_line_ids.sale_line_ids
			stock_moves = sale_lines.move_ids.filtered(lambda r: r.state == 'done')
			
			for sm in stock_moves:
				if sm.picking_id.tracking_url:
					record.tracking_url = sm.picking_id.tracking_url
				if sm.picking_id.machship_cons_number:
					record.machship_cons_number = sm.picking_id.machship_cons_number
				if sm.picking_id.carrier_tracking_ref:
					record.carrier_tracking_ref = sm.picking_id.carrier_tracking_ref
				if sm.picking_id.carrier_id:
					record.carrier_id = sm.picking_id.carrier_id.id

			


	@api.onchange('tracking_url')
	def _inverse_tracking_link(self):
		for rec in self:
			sale_lines = rec.invoice_line_ids.sale_line_ids
			stock_moves = sale_lines.move_ids.filtered(lambda r: r.state == 'done')
			# picking_ids = stock_moves.picking_id
			# stock_move_lines = sale_lines.move_ids.filtered(lambda r: r.state == 'done').move_line_ids
			# for picking in picking_ids:
			# 	picking.tracking_url = rec.tracking_url

			for sm in stock_moves:
				sm.picking_id.tracking_url = rec.tracking_url

	@api.onchange('machship_cons_number')
	def _inverse_cons_number(self):
		for rec in self:
			sale_lines = rec.invoice_line_ids.sale_line_ids
			stock_moves = sale_lines.move_ids.filtered(lambda r: r.state == 'done')
			# picking_ids = stock_moves.picking_id
			# stock_move_lines = sale_lines.move_ids.filtered(lambda r: r.state == 'done').move_line_ids
			# for picking in picking_ids:
			# 	picking.machship_cons_number = rec.machship_cons_number

			for sm in stock_moves:
				sm.picking_id.machship_cons_number = rec.machship_cons_number

	@api.onchange('carrier_tracking_ref')
	def _inverse_tracking_ref(self):
		for rec in self:
			sale_lines = rec.invoice_line_ids.sale_line_ids
			stock_moves = sale_lines.move_ids.filtered(lambda r: r.state == 'done')
			# picking_ids = stock_moves.picking_id
			# stock_move_lines = sale_lines.move_ids.filtered(lambda r: r.state == 'done').move_line_ids
			# for picking in picking_ids:
			# 	picking.carrier_tracking_ref = rec.carrier_tracking_ref

			for sm in stock_moves:
				sm.picking_id.carrier_tracking_ref = rec.carrier_tracking_ref

	@api.onchange('carrier_id')
	def _inverse_carrier(self):
		for rec in self:
			sale_lines = rec.invoice_line_ids.sale_line_ids
			stock_moves = sale_lines.move_ids.filtered(lambda r: r.state == 'done')
			picking_ids = stock_moves.picking_id
			# stock_move_lines = sale_lines.move_ids.filtered(lambda r: r.state == 'done').move_line_ids
			# for picking in picking_ids:
			# 	picking.carrier_id = rec.carrier_id.id

			for sm in stock_moves:
				sm.picking_id.carrier_id = rec.carrier_id.id
