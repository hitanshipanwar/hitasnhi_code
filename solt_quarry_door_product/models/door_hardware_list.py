
import json
from odoo import _, api, fields, models


class DoorHardwareList(models.Model):
    _name = 'door.hardware.list'
    _description = 'Door Hardware List'

    def _domain_product_id(self):
        company = self.env.company
        category_ids = self.env['product.category'].search([('is_hardware_categ', '=', 'True')]).ids
        domain = [
            '&', ('categ_id', 'child_of', category_ids), ('type', 'in', ['product', 'consu']), '|', ('company_id', '=', False), ('company_id', '=', company.id)
        ]
        return domain

    name = fields.Char('Name', related='product_id.name', required=True)
    product_id = fields.Many2one('product.product', 'Product', required=False, domain=lambda self: self._domain_product_id())
    pricelist_ids = fields.Many2many('product.pricelist', 'hardware_list_pricelist_rel', 'hardware_list_id', 'pricelist_id',
                                     string="Pricelist", required=False)
