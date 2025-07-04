# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, _


class ProductPricelist(models.Model):
    _inherit = 'product.pricelist'
    
    def set_product_price_ept(self, product_id, price, min_qty=1):
        #Price imported from Woocommerce is including tax. Badger need price to be imported excluding tax.
        #FIXME Find a better method to find price excuding tax
        price = float(price)
        product_obj = self.env['product.product'].browse(product_id)
        tax_amount = 0.00
        for tax in product_obj.taxes_id:
            if tax.amount != 0.00:
                tax_amount += price - round(price / (1 + (tax.amount/100.00)), 2)
        price_excl = price - round(tax_amount, 2)
        res = super(ProductPricelist, self).set_product_price_ept(product_id, price_excl, min_qty)
        return res
