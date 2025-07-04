from odoo import fields, models, api

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    # @api.onchange('partner_id', 'company_id')
    # def onchange_partner_id(self):
    #     res = super(PurchaseOrder, self).onchange_partner_id()
    #     if self.partner_id:
    #         self.rep_template_id = self.partner_id.rep_template_id and self.partner_id.rep_template_id.id or False
    #     return res

    # rep_template_id = fields.Many2one('report.company', 'Templates to Print', required=True)
    rep_template_id = fields.Many2one('report.company', 'Templates to Print', related='partner_id.rep_template_id')

class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'
    
    @api.onchange('product_id')
    def onchange_product_id(self):
        res = super(PurchaseOrderLine, self).onchange_product_id()
        if self.product_id and self.partner_id:
            seller_ids = self.env['product.supplierinfo'].search([('name', '=', self.partner_id.id),
                                                                  ('product_code', '!=', False),
                                                                  '|', ('product_id', '=', self.product_id.id),
                                                                  ('product_tmpl_id', '=', self.product_id.product_tmpl_id.id)])
            if seller_ids:
                self.vendor_product_code = seller_ids[0].product_code
        return res
    
    vendor_product_code = fields.Char('Supplier Code')
    additional_info = fields.Text('Additional Information')
