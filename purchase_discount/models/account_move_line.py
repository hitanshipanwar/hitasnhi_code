# -*- coding: utf-8 -*-

from odoo import fields, api, models


class AccountMoveLine(models.Model):
	_inherit = "account.move.line"

	#just pass the value to minus subtotal
	discount = fields.Float(string="Discount", digits="Discount")
	discount_selection = fields.Selection(string='Discount Type', selection=[('by_percent', 'By Percent'), ('by_price', 'By Price')], default="by_percent")
	discount_amount = fields.Float(string="Discount Calculation", compute="_compute_discount_calculation")
