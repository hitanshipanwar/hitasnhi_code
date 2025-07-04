# -*- coding: utf-8 -*-
from odoo import fields, models, api, exceptions, _
from odoo.exceptions import AccessError
from datetime import date, datetime, timedelta

class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    order_number = fields.Char(string="Order Number")
    payment_reference = fields.Char(string="Payment Reference ID")
    payment_date = fields.Datetime(string="Payment Date")
    payment_amt = fields.Float(string="Payment Amount")
    payment_method_type = fields.Char(string="Payment Method Type")
    seller_vat_num = fields.Char(string="Seller VAT Number", relate="partner_id.vat")


class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    part_number = fields.Char(string="Part Number", related='product_id.part_number')

class Product(models.Model):
    _inherit = "product.product"

    part_number = fields.Char(string="Part Number")