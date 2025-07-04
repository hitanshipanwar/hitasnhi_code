# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    sale_specs_id = fields.Many2one('specs.sale', 'Specs sale')
    sale_specs_name = fields.Char('Specs name')