# -*- coding: utf-8 -*-
from odoo import api, fields, models, _

class CustomerEnquiry(models.Model):
	_name = 'customer.enquiry'
	_description = 'Customer Enquiry'

	name = fields.Char(string="Name")
	email = fields.Char(string="Email")
	phone = fields.Char(string="Phone")
	product_id = fields.Many2one('product.product', string="Product")
	quantity = fields.Float(string="Quantity")
	unit_price = fields.Float(string="Unit Price")
	expected_pur_date = fields.Date(string="Expected Purchase date")