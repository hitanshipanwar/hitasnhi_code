# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    product_spec_ok = fields.Boolean('Can be use in Specs', default=False, help="Specify whether the product can be selected in the Specs")
    product_spec_roller_latche = fields.Boolean('Is roller latches product?', default=False)
    product_spec_ball_catche = fields.Boolean('Is ball catche product?', default=False)

    @api.constrains('product_spec_roller_latche')
    def _check_is_product_spec_roller_latche(self):
        for product in self:
            if product.product_spec_roller_latche:
                products = self.env['product.template'].search(
                    [('id', '!=', product.id), ('product_spec_roller_latche', '=', True)])
                if products:
                    raise ValidationError(
                        _(f"There is already a product marked as Roller latches."))

    @api.constrains('product_spec_ball_catche')
    def _check_is_product_spec_ball_catche(self):
        for product in self:
            if product.product_spec_ball_catche:
                products = self.env['product.template'].search(
                    [('id', '!=', product.id), ('product_spec_ball_catche', '=', True)])
                if products:
                    raise ValidationError(
                        _(f"There is already a team marked as Ball catche."))


class ProductProduct(models.Model):
    _inherit = 'product.product'

    specs_dc_ids = fields.Many2many('door.configuration', 'product_template_spec_dc_rel', 'product_temp_id',
                                    'config_id', string='Setup',
                                    help='Indicates the products that will be used as components in the BoM based on the Setup.')

