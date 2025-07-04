# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools, _

class MenuAccessControl(models.Model):
    _inherit = 'ir.ui.menu'

    def _filter_visible_menus(self):
        """ Hide menus for a specific group """
        res = super(MenuAccessControl, self)._filter_visible_menus()
        restricted_employee_groups = self.env.ref('o2b_access_management.group_hide_menu_employee')
        restricted_manager_groups = self.env.ref('o2b_access_management.group_hide_menu_manager')
        restricted_manufacturing_groups = self.env.ref('o2b_access_management.group_hide_menu_manufacturing')

        if restricted_employee_groups and self.env.user in restricted_employee_groups.users:
            hidden_employee_menus = ['website.menu_website_configuration', 
                            'maintenance.menu_maintenance_title',
                            'mass_mailing.mass_mailing_menu_root',
                            'import_bridge_adv_axis.custom_dashboard_menu']
            
            res = res.filtered(lambda menu: menu.get_external_id().get(menu.id) not in hidden_employee_menus)

        if restricted_manager_groups and self.env.user in restricted_manager_groups.users:
            hidden_manager_menus = ['website.menu_website_configuration',
                                    'import_bridge_adv_axis.custom_dashboard_menu']
            
            res = res.filtered(lambda menu: menu.get_external_id().get(menu.id) not in hidden_manager_menus)        

        if restricted_manufacturing_groups and self.env.user in restricted_manufacturing_groups.users:
            hidden_manufacturing_menus = ['maintenance.menu_maintenance_title',
                            'mass_mailing.mass_mailing_menu_root',
                            'hr.menu_hr_root',
                            'hr_holidays.menu_hr_holidays_root',
                            'hr_expense.menu_hr_expense_root',
                            'contacts.menu_contacts',
                            'repair.menu_repair_order',
                            'note.menu_note_notes',
                            'im_livechat.menu_livechat_root',
                            'website.menu_website_configuration',
                            'hr_attendance.menu_hr_attendance_root',
                            'import_bridge_adv_axis.custom_dashboard_menu']
            
            res = res.filtered(lambda menu: menu.get_external_id().get(menu.id) not in hidden_manufacturing_menus)
        return res
