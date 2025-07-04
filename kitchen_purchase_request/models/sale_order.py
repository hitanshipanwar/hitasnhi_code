# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _

class SaleOrder(models.Model):
	_inherit = "sale.order"

	# @api.model
	# def create(self, vals):
	# 	res = super(User, self).create(vals)
	# 	if self.env.user.has_group('sales_team.group_sale_salesman'):
	# 	 self.env['res.users'].create({
	# 	 'groups_id': 'sales_team.group_sale_salesman_all_leads',
	# 	 })
	# 	return res

	# @api.model
	# def _search(self, args, offset=0, limit=None, order=None, count=False, access_rights_uid=None):
	# 	# TDE FIXME: strange
	# 	print('access rights >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>', self)
	# 	print('access rights >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>', self.id)
	# 	# print('access rights >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>', access_rights_uid)
	# 	res = super(SaleOrder, self)._search(args, offset=offset, limit=limit, order=order, count=count, access_rights_uid=access_rights_uid)
	# 	print('res ===================================', res)
	# 	print('\n\n\n aregs\n\n\n', args)
	# 	# if self._context.get('search_default_categ_id'):
	# 		# args.append((('categ_id', 'child_of', self._context['search_default_categ_id'])))
	# 	return res


	# @api.model
	# def _search(self, args, offset=0, limit=None, order=None, count=False, access_rights_uid=False):
	# 	args = [(1, '=', 1)]
	# 	# all_sale_orders = self.env['sale.order'].sudo().search([])
	# 	# self.sale_order_ref_id = all_sale_orders.id
	# 	# print('>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>', all_sale_orders)
	# 	print('>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>', args)
	# 	return super(SaleOrder, self)._search(args, offset=offset, limit=limit, order=order, count=count, access_rights_uid=access_rights_uid)

