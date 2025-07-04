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
from bs4 import BeautifulSoup

class SaleOrder(models.Model):
	_inherit = 'sale.order'

	def action_confirm(self):
		# self = self.with_context(is_unlock=True)
		res = super(SaleOrder, self).action_confirm()
		delivery_order = self.env['stock.picking'].search([('sale_id', '=', self.id)])
		for rec in delivery_order:
			rec.carrier_id = self.carrier_id.id
		return res

	@api.model
	def create(self, vals):
		"""
		Override the create method to add a note if the customer has 'x_studio_requires_paper_invoice' set to True.
		"""
		# Get the customer (partner) information
		res = super(SaleOrder, self).create(vals)
		paper_invoice_note = "ATTN SHIPPING: Include PAPER invoice with shipment"

		if res.partner_id:
			if res.partner_id.x_studio_requires_paper_invoice:
				existing_note = vals.get('note', '')
				if existing_note:
					res.note = f"{existing_note}\n{paper_invoice_note}"
				else:
					res.note = paper_invoice_note

		# Call the original create method
		return res

	def write(self, vals):
	    old_sign = ""
	    if 'note' in vals:
	        if self.note:
	            soup = BeautifulSoup(self.note, 'html.parser')
	            old_sign = soup.get_text().strip()

	    res = super(SaleOrder, self).write(vals)

	    if 'note' in vals:
	        if vals['note']:
	            soup = BeautifulSoup(vals['note'], 'html.parser')
	            new_sign = soup.get_text().strip()
	            self.message_post(body="%s changed Notes from %s to %s." % (self.env.user.name, old_sign, new_sign))

	    return res

	def action_blank_delivery_method(self):
		for rec in self:
			rec.carrier_id = False
			if rec.picking_ids:
				pickings = rec.picking_ids.filtered(lambda p: p.state != 'done')
				for picking in pickings:
					picking.carrier_id = False


class Respartner(models.Model):
	_inherit = 'res.partner'

	def write(self, vals):
		old_sign = ''
		if 'comment' in vals and self.comment:
			soup = BeautifulSoup(self.comment, 'html.parser')
			old_sign = soup.get_text().strip()

		res = super(Respartner, self).write(vals)

		if 'comment' in vals:
			new_sign = ''
			soup = BeautifulSoup(vals['comment'], 'html.parser')
			new_sign = soup.get_text().strip()
			self.message_post(body="%s changed Comment from %s to %s."% (self.env.user.name, old_sign, new_sign))

		return res

class SaleOrderLine(models.Model):
	_inherit = 'sale.order.line'

	@api.depends('move_ids.state', 'move_ids.scrapped', 'move_ids.quantity_done', 'move_ids.product_uom')
	def _compute_qty_delivered(self):
		super(SaleOrderLine, self)._compute_qty_delivered()

		for line in self:  # TODO: maybe one day, this should be done in SQL for performance sake
			if line.qty_delivered_method == 'stock_move':
				qty = 0.0
				outgoing_moves, incoming_moves = line._get_outgoing_incoming_moves()
				for move in outgoing_moves:
					if move.state != 'done':
						continue
					qty += move.product_uom._compute_quantity(move.quantity_done, line.product_uom, rounding_method='HALF-UP')
				for move in incoming_moves:
					if not move.picking_id.is_reverted:
						if move.state != 'done':
							continue
						qty -= move.product_uom._compute_quantity(move.quantity_done, line.product_uom, rounding_method='HALF-UP')
				line.qty_delivered = qty


	def _get_outgoing_incoming_moves(self):
		outgoing_moves, incoming_moves = super(SaleOrderLine, self)._get_outgoing_incoming_moves()
		outgoing_moves = self.env['stock.move']
		incoming_moves = self.env['stock.move']

		moves = self.move_ids.filtered(lambda r: r.state != 'cancel' and not r.scrapped and self.product_id == r.product_id)
		if self._context.get('accrual_entry_date'):
			moves = moves.filtered(lambda r: fields.Date.context_today(r, r.date) <= self._context['accrual_entry_date'])
		for move in moves:
			if move.location_dest_id.usage == "customer":
				if not move.origin_returned_move_id or (move.origin_returned_move_id and move.to_refund):
					if not move.picking_id.is_reverted:
						outgoing_moves |= move
			elif move.location_dest_id.usage != "customer" and move.to_refund:
				incoming_moves |= move
		return outgoing_moves, incoming_moves