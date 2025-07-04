# -*- coding: utf-8 -*-

from odoo import models, fields, api


class Users(models.Model):
    _inherit = 'res.users'

    hide_ir_menu_access = fields.Many2many('ir.ui.menu', 'hide_ir_ui_menu_user_rel', 'hide_user_id', 'menu_id',
                                        string='Ocultar Menu')
    is_admin_user = fields.Boolean(compute="compute_is_admin_user")

    @api.depends_context('uid')
    @api.depends('groups_id')
    def compute_is_admin_user(self):
        for user in self:
            groups_ids = user.groups_id
            admin_groups = self.env.ref('base.group_erp_manager') | self.env.ref('base.group_system')
            user.is_admin_user = True if any(admin_gid.id in groups_ids.ids for admin_gid in admin_groups) else False