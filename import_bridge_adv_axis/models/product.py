 # -*- coding: utf-8 -*-

from odoo import api, fields, models, tools, _


class ProductProduct(models.Model):
    _inherit = 'product.product'

    # pricelist = fields.Char(string='Pricelist')
    # price = fields.Integer(string='Price')
    # ax_min_quantity = fields.Integer(string='Min Quantity')
    # ax_start_date = fields.Date(string='Start Date')
    # end_date = fields.Date(string='End Date')

class InheritPurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    purchase_add_details_id = fields.One2many("purchase.additional.detail","purchase_id",string="Additional Detail ID")        


class PurchaseAdditionalDetail(models.Model):
    _name = "purchase.additional.detail"

    purchase_id = fields.Many2one("purchase.order")

    product_id = fields.Many2one('product.product')
    partner_name = fields.Char("Partner Name")
    attributes_name = fields.Char("Attributes Name")
    imp_note = fields.Char("IMP Note")
    other_details = fields.Char("Other Details")
    yes_no = fields.Boolean("Yes/No")


class HrAttendance(models.Model):
    _inherit = 'hr.attendance'

    partner_name = fields.Char("Partner Name")
    extra_color = fields.Char("Color")


class ProjectTask(models.Model):
    _inherit = 'project.task'

    partner_name = fields.Char("Partner Name")
    extra_color = fields.Char("Color")
    extra_bool = fields.Boolean("Boolean")
    extra_amount = fields.Float("Amount")
    extra_notes = fields.Char("Notes")
