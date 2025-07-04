# -*- coding: utf-8 -*-
from odoo import fields, models, api


class StockPicker(models.Model):
    _name = 'stock.picker'

    name = fields.Char("Picker Name")




