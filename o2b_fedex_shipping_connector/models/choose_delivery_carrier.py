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
from odoo import api, fields, models,_
from odoo.exceptions import ValidationError, UserError

class ChooseDeliveryCarrier(models.TransientModel):
    _inherit = 'choose.delivery.carrier'
    _description = 'Delivery Carrier Selection Wizard'


    def _get_shipment_rate(self):
        vals = self.carrier_id.rate_shipment(self.order_id)
        if vals:
            if vals.get('success'):
                self.delivery_message = vals.get('warning_message', False)
                self.delivery_price = vals['price']
                self.display_price = vals['carrier_price']
                return {}
        else:
            return {}
        return {'error_message': vals['error_message']}


    def update_price(self):
        if self.carrier_id.delivery_type == 'fedex_rest':
            active_id = self.env['sale.order'].browse(self.env.context.get('active_id'))
            vals = self.carrier_id.fedex_get_shipping_rate(active_id)
            self.display_price = vals
            self.delivery_price = vals
            active_id.fedex_rate = vals
            return {
                'name': _('Add a shipping method'),
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'res_model': 'choose.delivery.carrier',
                'res_id': self.id,
                'target': 'new',
            }
        else:
            vals = self._get_shipment_rate()
            if vals.get('error_message'):
                raise UserError(vals.get('error_message'))
            return {
                'name': _('Add a shipping method'),
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'res_model': 'choose.delivery.carrier',
                'res_id': self.id,
                'target': 'new',
            }