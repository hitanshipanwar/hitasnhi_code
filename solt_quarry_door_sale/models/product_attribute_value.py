# -*- coding: utf-8 -*-

from odoo import api, fields, models


class ProductAttributeValue(models.Model):
    _inherit = 'product.attribute.value'

    @api.depends('attribute_id')
    @api.depends_context('show_attribute', 'not_show_attribute_specs')
    def _compute_display_name(self):
        """Override because in general the name of the value is confusing if it
        is displayed without the name of the corresponding attribute.
        Eg. on product list & kanban views, on BOM form view

        However during variant set up (on the product template form) the name of
        the attribute is already on each line so there is no need to repeat it
        on every value.
        """
        if not self.env.context.get('not_show_attribute_specs', False):
            return super()._compute_display_name()
        for value in self:
            value.display_name = f"{value.name}"