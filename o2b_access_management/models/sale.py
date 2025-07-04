# -*- coding: utf-8 -*-
from odoo import fields, models, api, exceptions, _
from odoo.exceptions import AccessError

class SaleOrder(models.Model):
    _inherit = "sale.order"

    def unlink(self):
        """Restrict deletion for record."""
        if self.env.user.has_group('sales_team.group_sale_salesman'):
            if self.create_uid != self.env.user:
                raise AccessError(_("You are not allowed to delete record created by other user."))
        
        return super(SaleOrder, self).unlink()


class CrmLeads(models.Model):
    _inherit = "crm.lead"

    def unlink(self):
        """Restrict deletion for record."""
        if self.env.user.has_group('sales_team.group_sale_salesman'):
            if self.create_uid != self.env.user:
                raise AccessError(_("You are not allowed to delete record created by other user."))
        
        return super(CrmLeads, self).unlink()
