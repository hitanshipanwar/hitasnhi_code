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
from odoo import models, fields, api

import logging
_logger = logging.getLogger(__name__)
from odoo.exceptions import UserError

class UpdateStockAisle(models.TransientModel):
    _name = 'update.stock.aisle'
    _description = 'Update Stock Aisle'

    product_id = fields.Many2one('product.product', string="Product")
    aisle_id = fields.Many2one('stock.aisle', string="Aisle")
    update_asile_line_ids = fields.One2many('update.aisle.line', 'line_id', string="Update Aisle")
    qty = fields.Float(string="Quantity")
    warehouse_form_id = fields.Many2one('stock.aisle', string="Aisle From")
    warehouse_to_id = fields.Many2one('stock.aisle', string="Aisle To")
    move_id = fields.Many2one('stock.move.line',string="Line")
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    barcode = fields.Char(string="Barcode")


    # def action_client_action(self):

    #     return {
    #         'type': 'ir.actions.act_window',
    #         'res_model': 'update.stock.aisle',
    #         'views': [[self.env.ref('o2b_stock_custom.update_i_view_form').id, 'form']],
    #         'res_id': self.id,
    #         'target': 'new',
    #     }

    # @api.onchange('aisle_id')
    # def onchange_aisle_id(self):
    #     if self.product_id and self.aisle_id:
    #         self.update_asile_line_ids.create({
    #             'product_id': self.product_id.id,
    #             'aisle_id': self.aisle_id.id,
    #             'line_id': self.id,
    #             })
    #         self.product_id = False
    #         self.aisle_id = False

    # def action_confirm(self):
    #     for line in self.update_asile_line_ids:
    #         self.env['product.aisle'].create({
    #             'product_id': line.product_id.id,
    #             'aisle_id': line.aisle_id.id,
    #         })
    #     return {'type': 'ir.actions.act_window_close'}

    # # def action_confirm(self):
    # #     _logger.info("Wizard confirmed!")

    # #     # Adjust the quantity in the 'from' aisle
    # #     stock_line_from = self.env['stock.move.line'].search([
    # #         ('product_id', '=', self.product_id.id),
    # #         ('stock_aisle', '=', self.warehouse_form_id.name)  # Assuming 'aisle' field is correctly set
    # #     ], limit=1)

    # #     if stock_line_from:
    # #         print('----wwwwwwww',stock_line_from)
    # #         stock_line_from.qty_done -= self.qty
    # #         stock_line_from.aisle_id = self.warehouse_form_id.id
    # #         _logger.info(f"Updated 'from' stock line: {stock_line_from.id} with new quantity: {stock_line_from.qty_done}")
    # #     else:
    # #         _logger.warning(f"No stock line found in 'from' aisle for product {self.product_id.id}")

    # #     # Adjust the quantity in the 'to' aisle
    # #     stock_line_to = self.env['stock.move.line'].search([
    # #         ('product_id', '=', self.product_id.id),
    # #         ('aisle_id', '=', self.warehouse_to_id.id)  # Assuming 'aisle' field is correctly set
    # #     ], limit=1)

    # #     if stock_line_to:
    # #         print('--------qar------',stock_line_to)
    # #         stock_line_to.qty_done += self.qty
    # #         _logger.info(f"Updated 'to' stock line: {stock_line_to.id} with new quantity: {stock_line_to.qty_done}")
    # #     else:
    # #         # Create a new stock.move.line record if it doesn't exist
    # #         print('-------qty--------   ',self.qty)
    # #         self.env['stock.move.line'].create({
    # #             'product_id': self.product_id.id,
    # #             'qty_done': self.qty,
    # #             'aisle_id': self.warehouse_to_id.id,
    # #             'location_id': stock_line_from.location_id.id,
    # #             'location_dest_id': stock_line_from.location_dest_id.id,
    # #             'product_uom_id': self.product_id.uom_id.id,
    # #             'company_id':   self.company_id.id     # Fetching the Unit of Measure from the product
    # #         })
    # #         _logger.info(
    # #             f"Created new stock line for product {self.product_id.id} in aisle {self.warehouse_to_id.id} with quantity {self.qty}")

    # #     return {'type': 'ir.actions.act_window_close'}


    # # def add_product_from_barcode(self):
    # #     if self.barcode:
    # #         product = self.env['product.product'].search([('barcode', '=', self.barcode)], limit=1)
    # #         if product:
    # #             self.product_ids |= product
    # #         else:
    # #             raise UserError("Product not found with the provided barcode.")
    # #     else:
    # #         raise UserError("Please scan a barcode.")

    # # def open_barcode_scanner(self):
    # #     return {
    # #         'type': 'ir.actions.client',
    # #         'tag': 'barcode_scanner',
    # #         'params': {
    # #             'model': 'update.stock.aisle',
    # #                 'callback': 'add_product_from_barcode',
    # #         }
    # #     }

class UpdateAisleLine(models.TransientModel):
    _name = 'update.aisle.line'
    _description = 'Update Aisle Line'

    line_id = fields.Many2one('update.stock.aisle')
    product_id = fields.Many2one('product.product')
    aisle_id = fields.Many2one('stock.aisle')


class EditStockAisle(models.TransientModel):
    _name = 'edit.stock.aisle'
    _description = 'Edit Stock Aisle'

    product_id = fields.Many2one('product.product')
    source_aisle_id = fields.Many2one('stock.aisle')
    destination_aisle_id = fields.Many2one('stock.aisle')
    edit_aisle_ids = fields.One2many('edit.stock.aisle.line', 'line_id', string="Edit Product Aisle")
    barcode = fields.Char("Barcode")

    # def action_edit_aisle_client_action(self):

    #     return {
    #         'type': 'ir.actions.act_window',
    #         'res_model': 'edit.stock.aisle',
    #         'views': [[self.env.ref('o2b_stock_custom.view_edit_stock_aisle_form').id, 'form']],
    #         'res_id': self.id,
    #         'target': 'new',
    #     }

    # @api.onchange('destination_aisle_id')
    # def onchange_destination_aisle_id(self):
    #     if self.product_id and self.source_aisle_id and self.destination_aisle_id:
    #         self.edit_aisle_ids.create({
    #             'product_id': self.product_id.id,
    #             'source_aisle_id': self.source_aisle_id.id,
    #             'destination_aisle_id': self.destination_aisle_id.id,
    #             'line_id': self.id,
    #             })
    #         self.product_id = False
    #         self.source_aisle_id = False
    #         self.destination_aisle_id = False

    # def action_edit_confirm(self):
    #     record_list = []
    #     for line in self.edit_aisle_ids:
    #         record = self.env['product.aisle'].search([('product_id', '=', line.product_id.id), ('aisle_id', '=', line.source_aisle_id.id)], limit=1)

    #         if record and record.product_id.id not in record_list:
    #             record.aisle_id = line.destination_aisle_id
    #             record_list.append(record.product_id.id)

    #     self.barcode = False

class EditStockAisleLine(models.TransientModel):
    _name = 'edit.stock.aisle.line'
    _description = 'Edit Stock Aisle'

    line_id = fields.Many2one('edit.stock.aisle')
    product_id = fields.Many2one('product.product')
    source_aisle_id = fields.Many2one('stock.aisle')
    destination_aisle_id = fields.Many2one('stock.aisle')


class ProductAisleRecord(models.Model):
    _name = 'product.aisle'
    _description = 'Product Aisle'
    _rec_name = 'aisle_id'

    product_id = fields.Many2one('product.product', string="Product")
    aisle_id = fields.Many2one('stock.aisle', string="Aisle")

