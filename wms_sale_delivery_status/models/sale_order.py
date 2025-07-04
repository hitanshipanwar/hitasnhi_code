# -*- coding: utf-8 -*-
##############################################################################
#                                                                            #
# Part of WMSSOFT. (Website: www.wmssoft.com.au).                            #
# See LICENSE file for full copyright and licensing details.                 #
#                                                                            #
##############################################################################

from odoo import fields, models, api


class SaleOrder(models.Model):
    _inherit = "sale.order"
    
    @api.depends('order_line','order_line.qty_delivered','order_line.product_uom_qty')
    def check_delivery_status(self):
        for rec in self:
            total_order_qty = total_deliver = 0.0
            if rec.order_line and rec.state =='sale':
                for line in rec.order_line:
                    if line.product_id.type == 'product' and line.product_uom_qty !=0.0:
                        total_order_qty += line.product_uom_qty
                        total_deliver += line.qty_delivered
                if total_order_qty == 0.0:
                    rec.delivery_status = 'full'
                elif total_deliver == 0.0:
                    rec.delivery_status = 'pending'
                elif total_deliver < total_order_qty:
                    rec.delivery_status = 'partial'
                else:
                    rec.delivery_status = 'full'
            else:
                rec.delivery_status = 'pending'


    delivery_status = fields.Selection([('pending','To Deliver'),
                                        ('partial','Partially Delivered'),
                                        ('full','Fully Delivered'),
                                        ], string="Delivery Status", compute="check_delivery_status", store=True)
