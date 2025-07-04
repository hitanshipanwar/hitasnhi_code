# -*- coding: utf-8 -*-
from odoo import fields, models, api


class Product(models.Model):
    _inherit = 'product.product'

    aisle = fields.Many2one('stock.aisle', string="Aisle")
    ca_aisle_id = fields.Many2one('stock.aisle', string="CA Aisle")
    # aisle = fields.Many2one('stock.aisle', string="Aisle", company_dependent=True)
