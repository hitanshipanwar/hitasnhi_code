# -*- coding: utf-8 -*-

from odoo import api, fields, models
from datetime import datetime, date, time

class AccountMove(models.Model):
	_inherit = 'account.move'

	zone = fields.Char(string="Zone")
	buyer_id = fields.Char(string="Buyer ID")
	invoice_value = fields.Char(string="Invoice Value")
	invoice_dt = fields.Char(string="Invoice Detail")
	additional_detail_ref = fields.Char(string="Additional Detail Ref")
	delivery_dt = fields.Char(string="Deliver Detail")
	vehicle_no = fields.Char(string="Vehicle No")
	path_with_hyperlink = fields.Char("Path With Hyperlink")
	value_or_per = fields.Float(string="Value Or %")

	autocomplete = fields.Char(string="Auto-Compelte")
	purchase_ref = fields.Char(string="Purchase Ref.", compute='_compute_is_po')
	is_po = fields.Boolean(string="Is PO", compute="_compute_is_po")

	def _compute_is_po(self):
		for rec in self:
			if rec.purchase_order_count >= 1:
				rec.is_po = True
				rec.purchase_ref = rec.line_ids.purchase_line_id.order_id.name
			else:
				rec.is_po = False
				rec.purchase_ref = False


class PurchaseOrder(models.Model):
	_inherit = 'purchase.order'

	is_po = fields.Boolean(string="Is PO", default=True)


class SalesCommission(models.Model):
	_name = 'sales.commission.rule'
	_description = 'Sales Commission Rule'

	name = fields.Char(string="Name")
	min_sales_amount = fields.Float(string="Min Sales Amount")
	commission_per = fields.Float(string="Commission %")


class SaleOder(models.Model):
	_inherit = 'sale.order'

	sales_commission = fields.Many2one('sales.commission.rule', string="Sales Commission")
	total_com = fields.Float(string="Commission Amt", compute="_compute_total_com")

	@api.depends('sales_commission')
	def _compute_total_com(self):
		for rec in self:
			if rec.amount_total <= rec.sales_commission.min_sales_amount:
				rec.total_com = rec.amount_total*rec.sales_commission.commission_per/100
			else:
				rec.total_com = 0.0

