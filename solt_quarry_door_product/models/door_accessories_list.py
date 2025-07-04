from odoo import _, api, fields, models


class DoorAccessoriesList(models.Model):
    _name = 'door.accessories.list'
    _inherit = 'door.abstract'
    _description = 'Door Accessories List'

    def _domain_product_id(self):
        company = self.env.company
        domain = [
            ('type', 'in', ['product', 'consu']), '|', ('company_id', '=', False), ('company_id', '=', company.id)
        ]
        return domain

    name = fields.Char('Name', related='product_id.name', required=True)
    product_id = fields.Many2one('product.product', 'Product', required=False, domain=lambda self: self._domain_product_id())
    pricelist_id = fields.Many2one('product.pricelist', string="Pricelist", required=False)