from odoo import models, fields, api

class ProductTemplateAttributeValue(models.Model):
    _inherit = ["product.template.attribute.value"]
    _description = 'variante'

    price_sd = fields.Float(
        string='Precio Single Door'
    )
    price_dd = fields.Float(
        string='Precio Double Door'
    )
    price_bifolds = fields.Float(
        string='Precio Bifolds / Sliding'
    )
    price_unique = fields.Float(
        string='Precio unico',
        help='Aqui van los precios de las variantes que no tienen relacion con la configuración de productos'
    )
    price_mol_arq = fields.Float(
        string='Precio Moldura Arqueada'
    )
    price_mol_cua = fields.Float(
        string='Precio Moldura Cuadrada'
    )