from odoo import fields, models, api

class VendorProductCode(models.Model):
    _inherit = "stock.move"

    vendor_product_code = fields.Char('Vendor Product Code',  compute='_compute_product_code')

    @api.depends('product_id')
    def _compute_product_code(self):
        for rec in self:
            if rec.product_id:
                if rec.product_id.variant_seller_ids:
                    code = ""
                    for s_id in rec.product_id.variant_seller_ids:
                        if s_id.product_id and s_id.product_id.id == rec.product_id.id:
                            code = s_id.product_code
                            rec.vendor_product_code = s_id.product_code
                    if not code:
                        rec.vendor_product_code = rec.product_id.variant_seller_ids[0].product_code
                else:
                    rec.vendor_product_code = ''
            else:
                rec.vendor_product_code = ''

class VendorProductCodeMoveLine(models.Model):
    _inherit = "stock.move.line"

    vendor_product_code = fields.Char('Vendor Product Code',  compute='_compute_product_code')

    @api.depends('product_id')
    def _compute_product_code(self):
        for rec in self:
            if rec.product_id:
                if rec.product_id.variant_seller_ids:
                    code = ""
                    for s_id in rec.product_id.variant_seller_ids:
                        if s_id.product_id and s_id.product_id.id == rec.product_id.id:
                            code = s_id.product_code
                            rec.vendor_product_code = s_id.product_code
                    if not code:
                        rec.vendor_product_code = rec.product_id.variant_seller_ids[0].product_code
                else:
                    rec.vendor_product_code = ''
            else:
                rec.vendor_product_code = ''