# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError, ValidationError

class ProductPublicCategory(models.Model):
    _inherit = 'product.public.category'


    group_ids = fields.Many2many('res.groups', string='Visible Groups',
                                 help="User need to be at least in one of these groups to see the menu")
    visible = fields.Boolean(
        compute='_compute_visible', 
        string='Visible',
        store=False
    )

    @api.depends('group_ids')
    def _compute_visible(self):
        user_groups = self.env.user.groups_id.ids
        for category in self:
            # If no group is set, category is visible to everyone.
            if not category.group_ids:
                category.visible = True
            else:
                # Check if user is in any of the groups specified for this category.
                category.visible = bool(set(category.group_ids.ids) & set(user_groups))
