from odoo import fields, models


class StockPackageType(models.Model):
    _inherit = 'stock.package.type'
    
    is_carton = fields.Boolean('Is Carton')