# -*- coding: utf-8 -*-
##############################################################################
#                                                                            #
# Part of WMSSOFT. (Website: www.wmssoft.com.au).                            #
# See LICENSE file for full copyright and licensing details.                 #
#                                                                            #
##############################################################################

from odoo import fields, models, api


class ProductPricelist(models.Model):
    _inherit = 'product.pricelist'

    def remove_duplicate_product_items(self):
        for rec in self:
            uniqItem = []
            for line in rec.item_ids:
                uniqRec = self.env['product.pricelist.item'].search([
                        ('product_id', '=', line.product_id.id),
                        ('pricelist_id', '=', line.pricelist_id.id)
                    ], limit=1, order='write_date desc')
                if uniqRec.id not in uniqItem:
                    uniqItem.append(uniqRec.id)

            delDuplicateRec = self.env['product.pricelist.item'].search([('id','not in',uniqItem), ('pricelist_id', '=', rec.id)])
            delzeroPriceRec = self.env['product.pricelist.item'].search([('fixed_price','=',0), ('pricelist_id', '=', rec.id)])
            delDuplicateRec.unlink()
            delzeroPriceRec.unlink()
