# -*- coding: utf-8 -*-

from odoo import models, api, tools


class IrUiMenu(models.Model):
    _inherit = 'ir.ui.menu'

    @api.model
    @tools.ormcache('frozenset(self.env.user.groups_id.ids)', 'debug')
    def _visible_menu_ids(self, debug=False):
        visible_ids = super(IrUiMenu, self)._visible_menu_ids(debug=debug)
        menus_to_hide = self.env.user.hide_ir_menu_access

        return visible_ids - set(menus_to_hide.ids)