# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    classification_type = fields.Selection([('door', 'Door'), ('windows', 'Windows')],
                                           string="Classification Type", required=False)
    product_spec_ok = fields.Boolean('Can be use in Specs', default=False,
                                     help="Specify whether the product can be selected in the Specs")

