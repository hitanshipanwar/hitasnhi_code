# -*- coding: utf-8 -*-
from odoo import fields, models, api


class StockAisle(models.Model):
    _name = 'stock.aisle'

    name = fields.Char("Aisle Name")




