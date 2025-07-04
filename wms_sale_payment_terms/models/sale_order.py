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

    @api.model
    def create(self, vals):
        result = super(SaleOrder, self).create(vals)
        print("result==============",result)
        print("result==property_payment_term_id============",result.partner_id.property_payment_term_id)
        print("result==property_payment_term_id==Name==========",result.partner_id.property_payment_term_id.name)
        if result.partner_id and result.partner_id.property_payment_term_id:
            result.payment_term_id = result.partner_id.property_payment_term_id
            print("result====test==========",result.payment_term_id)
            print("result=======name=======",result.payment_term_id.name)
        return result

