# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools, _
from odoo.exceptions import AccessError

class ResGroups(models.Model):
    _inherit = 'res.groups'    

    @api.model
    def get_application_groups(self, domain):
        group_ids = []
        for xml_id in [
            'o2b_access_management.group_hide_menu_manager',
        ]:
            group = self.env.ref(xml_id, raise_if_not_found=False)
            if group:
                group_ids.append(group.id)

        domain.append(('id', 'not in', group_ids))
        return super().get_application_groups(domain)
