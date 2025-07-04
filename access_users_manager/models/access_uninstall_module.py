# -*- coding: utf-8 -*-

from odoo import models


class accessBaseModuleUninstall(models.TransientModel):
    _inherit = "base.module.uninstall"

    def action_uninstall(self):
        """ Delete group which is created for user profiles and Domain access"""
        if self.module_id.name == 'access_users_manager':
            self.env['res.groups'].sudo().search([('custom', '=', True)]).unlink()
            self.env['res.groups'].sudo().search(
                [('category_id', '=', self.env.ref('access_users_manager.ir_module_category_profiles').id)]).unlink()
        res = super(accessBaseModuleUninstall, self).action_uninstall()
        return res