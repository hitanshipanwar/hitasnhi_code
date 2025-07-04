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
from odoo import models, fields, api


class AisleLocation(models.Model):
	_name = 'aisle.location'
	_description = 'Aisle Location'
	_rec_name = 'aisle_id'

	product_id = fields.Many2one('product.product', string="Product")
	aisle_id = fields.Many2one('stock.aisle', string="Aisle Name")
	company_id = fields.Many2one('res.company', required=True, readonly=True, default=lambda self: self.env.company)
	# in_aisle_id = fields.Many2one('stock.aisle', string="In Aisle")
	# out_aisle_id = fields.Many2one('stock.aisle', string="Out Aisle")

	def action_set_company(self):
		for rec in self:
			company_id = self.env['res.company'].search([('show_mo_validation', '=', True)])
			rec.company_id = company_id.id

	@api.model
	def create(self, vals):
		res = super(AisleLocation, self).create(vals)
		company_id = self.env.company
		sorted_locations = self.env['aisle.location'].search([('product_id', '=', vals['product_id']), ('company_id', '=', company_id.id)], order='id asc')
		if sorted_locations:
			if company_id.show_mo_validation == True:
				stock_moves = self.env['stock.move'].search([('product_id', '=', vals['product_id']), ('company_id', '=', company_id.id)])
				sorted_locations[0].product_id.write({'ca_aisle_id': sorted_locations[0].aisle_id.id})
				for move in stock_moves:
						move.stock_aisle = sorted_locations[0].aisle_id.name
			else:
				stock_moves = self.env['stock.move'].search([('product_id', '=', vals['product_id']), ('company_id', '=', company_id.id)])
				sorted_locations[0].product_id.write({'aisle': sorted_locations[0].aisle_id.id})
				for move in stock_moves:
						move.stock_aisle = sorted_locations[0].aisle_id.name
			self.env.cr.commit()
		return res

	def write(self, vals):
		res = super(AisleLocation, self).write(vals)
		for rec in self:
			company_id = self.env.company
			if 'product_id' in vals:
				product_id = vals['product_id']
			else:
				product_id = rec.product_id.id
			sorted_locations = self.env['aisle.location'].search([('product_id', '=', product_id), ('company_id', '=', company_id.id)], order='id asc')
			if sorted_locations:
				if company_id.show_mo_validation == True:
					stock_moves = self.env['stock.move'].search([('product_id', '=', product_id), ('company_id', '=', company_id.id)])
					sorted_locations[0].product_id.write({'ca_aisle_id': sorted_locations[0].aisle_id.id})
					for move in stock_moves:
							move.stock_aisle = sorted_locations[0].aisle_id.name
				else:
					stock_moves = self.env['stock.move'].search([('product_id', '=', product_id), ('company_id', '=', company_id.id)])
					sorted_locations[0].product_id.write({'aisle': sorted_locations[0].aisle_id.id})
					for move in stock_moves:
							move.stock_aisle = sorted_locations[0].aisle_id.name
				self.env.cr.commit()
		return res
		

	def unlink(self):
		for rec in self:
			sorted_locations = self.env['aisle.location'].search([('product_id', '=', rec.product_id.id), ('company_id', '=', rec.company_id.id)], order='id asc')

			ids_self = [record.id for record in self]
			ids_sorted_locations = [record.id for record in sorted_locations]

			unique_in_both = [id_ for id_ in ids_sorted_locations if id_ not in ids_self]
			unique_sorted_locations = sorted_locations.filtered(lambda loc: loc.id in unique_in_both)
			if unique_sorted_locations:
				if rec.company_id.show_mo_validation == True:
					stock_moves = self.env['stock.move'].search([('product_id', '=', rec.product_id.id), ('company_id', '=', rec.company_id.id)])
					unique_sorted_locations[0].product_id.write({'ca_aisle_id': unique_sorted_locations[0].aisle_id.id})
					for move in stock_moves:
							move.stock_aisle = unique_sorted_locations[0].aisle_id.name
				else:
					stock_moves = self.env['stock.move'].search([('product_id', '=', rec.product_id.id), ('company_id', '=', rec.company_id.id)])
					unique_sorted_locations[0].product_id.write({'aisle': unique_sorted_locations[0].aisle_id.id})
					for move in stock_moves:
							move.stock_aisle = unique_sorted_locations[0].aisle_id.name
			else:
				if rec.company_id.show_mo_validation == True:
					stock_moves = self.env['stock.move'].search([('product_id', '=', rec.product_id.id), ('company_id', '=', rec.company_id.id)])
					rec.product_id.write({'ca_aisle_id': False})
					for move in stock_moves:
							move.stock_aisle = ''
				else:
					stock_moves = self.env['stock.move'].search([('product_id', '=', rec.product_id.id), ('company_id', '=', rec.company_id.id)])
					rec.product_id.write({'aisle': False})
					for move in stock_moves:
							move.stock_aisle = ''
			self.env.cr.commit()

		res = super(AisleLocation, self).unlink()
		return res


class ProductProduct(models.Model):
	_inherit = 'product.product'

	aisle_location_count = fields.Integer(string="Aisle Locations", compute="count_aisle_location")

	@api.model
	def create_aisle_location(self, product, aisle):
		aisle_location = self.env['aisle.location'].create({
			'product_id': product,
			'aisle_id': aisle,
		})
		return {
			'type': 'ir.actions.client',
			'tag': 'reload',
		}

	@api.model
	def update_aisle(self, product):
		company_id = self.env.company
		sorted_locations = self.env['aisle.location'].search([('product_id', '=', product.id), ('company_id', '=', company_id.id)], order='id asc')
		if sorted_locations:
			if company_id.show_mo_validation == True:
				stock_moves = self.env['stock.move'].search([('product_id', '=', product.id), ('company_id', '=', company_id.id)])
				sorted_locations[0].product_id.write({'ca_aisle_id': sorted_locations[0].aisle_id.id})
				for move in stock_moves:
						move.stock_aisle = sorted_locations[0].aisle_id.name
			else:
				stock_moves = self.env['stock.move'].search([('product_id', '=', product.id), ('company_id', '=', company_id.id)])
				sorted_locations[0].product_id.write({'aisle': sorted_locations[0].aisle_id.id})
				for move in stock_moves:
						move.stock_aisle = sorted_locations[0].aisle_id.name
			self.env.cr.commit()

	@api.model
	def count_aisle_location(self):
		record = self.env['aisle.location'].search([('product_id', '=', self.id)])
		self.aisle_location_count = len(record)

	def view_product_aisle_location(self):
		return {
			'type': 'ir.actions.act_window',
			'name': 'Aisle Location',
			'view_mode': 'tree,form',
			'res_model': 'aisle.location',
			'domain': [('product_id', '=', self.id)],
			'context': {'create': False},
		}