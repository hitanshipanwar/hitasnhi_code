from odoo import api, fields, models


class ProductProduct(models.Model):
    _inherit = 'product.product'
    
    aisle_name = fields.Char('Aisle Name', compute='_compute_aisle_name')

    @api.depends('aisle.name', 'ca_aisle_id.name')
    def _compute_aisle_name(self):
        for record in self:
            if record.env.company.show_mo_validation:
                record.aisle_name = record.ca_aisle_id.name
            else:
                record.aisle_name = record.aisle.name
                
    @api.model
    def _get_fields_stock_barcode(self):
        res = super()._get_fields_stock_barcode()
        res.append('aisle_name')
        return res
