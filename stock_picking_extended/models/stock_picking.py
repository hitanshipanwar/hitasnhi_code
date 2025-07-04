# -*- coding: utf-8 -*-
from odoo import fields, models, api


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    picker_id = fields.Many2one('stock.picker', string="Picker")




