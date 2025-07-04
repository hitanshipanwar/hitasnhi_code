# -*- coding: utf-8 -*-
##########################################################################
# Author      : O2b Technologies Pvt. Ltd.(<www.o2btechnologies.com>)
# Copyright(c): 2016-Present O2b Technologies Pvt. Ltd.
# All Rights Reserved.
#
# This program is copyright property of the author mentioned above.
# You can`t redistribute it and/or modify it.
#
##########################################################################
from odoo import models, fields


class StockMove(models.Model):
    _inherit = 'stock.move'
    _order = 'stock_aisle asc'

    # aisle = fields.Many2one('stock.aisle', related='product_id.aisle', string="Aisle",store=True)
    # stock_aisle = fields.Char(string="Aisle", related='product_id.aisle')
    # stock_aisle = fields.Char(string="Aisle")


class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    aisle_id = fields.Many2one('stock.aisle')

    # stock_aisle = fields.Char(string="Aisle")

    # def update_aisle(self):
    #     print('-----update aisle----wwww-----', self)
    #     aisle_id = self.env['stock.aisle'].search([('name','=',self.stock_aisle)])
    #
    #     print("------aisle_id-------",aisle_id)
    #     return {
    #         'type': 'ir.actions.act_window',
    #         'name': 'Update Aisle',
    #         'res_model': 'update.stock.aisle',
    #         'view_mode': 'form',
    #         'target': 'new',
    #         'context': {'default_warehouse_form_id': aisle_id.id, 'default_qty': self.qty_done,'default_product_id': self.product_id.id}
    #     }
