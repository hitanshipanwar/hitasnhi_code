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
from odoo import fields, models,api
from odoo.exceptions import ValidationError


class StockIWarehouse(models.Model):
    _name = 'stock.aisle.warehouse'
    _description = 'Stock I Warehouse'

    name = fields.Char(required=True)
    sequence = fields.Integer(default=10, index=True)
    stock_eyes_line_ids = fields.One2many('stock.aisle.line', 'warehouse_id', string="Stock Lines")


class StockEyesLine(models.Model):
    _name = 'stock.aisle.line'

    product_id = fields.Many2one('product.product', string="Product")
    qty = fields.Integer(string="Quantity")
    warehouse_id = fields.Many2one('stock.aisle.warehouse', string="Warehouse")


class StockAisle(models.Model):
    _inherit = 'stock.aisle'

    barcode = fields.Char(string="Barcode")
    quantity = fields.Float(string="quantity")
    product_uom_id = fields.Many2one('uom.uom', string='Product UoM')
    company_id = fields.Many2one('res.company', required=True, default=lambda self: self.env.company)

    def action_set_company(self):
        for rec in self:
            company_id = self.env['res.company'].search([('show_mo_validation', '=', True)])
            rec.company_id = company_id.id

    def _get_stock_barcode_data(self):
        stock_aisle = self.env['stock.aisle'].search([
            ('barcode', '=', self.barcode),
        ], limit=1)
        return stock_aisle

    @api.model
    def create(self, vals):
        if 'barcode' in vals and vals['barcode']:
            existing_record = self.search([('barcode', '=', vals['barcode'])])
            if existing_record:
                raise ValidationError("A barcode can only be assigned to one Aisle Location!")
        return super(StockAisle, self).create(vals)

    def write(self, vals):
        if 'barcode' in vals and vals['barcode']:
            for record in self:
                existing_record = self.search([
                    ('barcode', '=', vals['barcode']),
                    ('id', '!=', record.id)
                ])
                if existing_record:
                    raise ValidationError("A barcode can only be assigned to one Aisle Location!")
        return super(StockAisle, self).write(vals)

    # def action_client_action(self):
    #     """ Open the mobile view specialized in handling barcodes on mobile devices.
    #     """
    #     action = self.env.ref('o2b_stock_custom.stock_barcode_aisle_client_action').read()[0]
    #     # action = self.env['ir.actions.actions']._for_xml_id('o2b_stock_custom.update_stock_i_warehouse_action')
    #     return dict(action, target='fullscreen')

    def action_client_action(self):
        """ Open the mobile view specialized in handling barcodes on mobile devices. """
        action = self.env['ir.actions.actions']._for_xml_id('o2b_stock_custom.stock_barcode_aisle_client_action')
        return dict(action, target='fullscreen')
        # action = self.env.ref('o2b_stock_custom.stock_barcode_aisle_client_action').read()[0]
        # action.update({
        #     'res_model': 'stock.aisle',
        #     'context': {'active_id': self.id},
        # })
        # return dict(action, target='fullscreen')

    @api.model
    def _get_stock_barcode_data(self):
        # Assuming that the barcode data is related to the aisle itself
        return {
            'id': self.id,
            'name': self.name,
            'barcode': self.barcode
        }

    @api.model
    def update_product_qty(self, from_aisle_id, to_aisle_id, product_id, quantity):
        # Implement the logic to update product quantity from one aisle to another
        pass

    @api.model
    def free_aisle_location(self, aisle):
        company_id = self.env.company
        records = self.env['aisle.location'].search([('aisle_id', '=', aisle)])

        if not records:
            return False

        product_ids = records.mapped('product_id')
        try:
            records.unlink()
        except Exception as e:
            _logger.error("Failed to unlink aisle locations: %s", e)
            raise ValidationError("Failed to delete some aisle locations due to: %s" % e)

        for product_id in product_ids:
            sorted_locations = self.env['aisle.location'].search(
                [('product_id', '=', product_id.id), ('company_id', '=', company_id.id)]
            )

            if sorted_locations:
                if company_id.show_mo_validation:
                    stock_moves = self.env['stock.move'].search(
                        [('product_id', '=', product_id.id), ('company_id', '=', company_id.id)]
                    )
                    sorted_locations[0].product_id.write({'ca_aisle_id': sorted_locations[0].aisle_id.id})
                    for move in stock_moves:
                        move.stock_aisle = sorted_locations[0].aisle_id.name
                else:
                    stock_moves = self.env['stock.move'].search(
                        [('product_id', '=', product_id.id), ('company_id', '=', company_id.id)]
                    )
                    sorted_locations[0].product_id.write({'aisle': sorted_locations[0].aisle_id.id})
                    for move in stock_moves:
                        move.stock_aisle = sorted_locations[0].aisle_id.name
            else:
                if company_id.show_mo_validation:
                    product_id.ca_aisle_id = False
                else:
                    product_id.aisle = False

        return True

    def print_label(self):
        return self.env.ref('o2b_stock_custom.action_report_label').report_action(self)
