# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, _
from odoo.exceptions import UserError

class ResPartner(models.Model):
    _inherit = 'res.partner'
    
    
    def get_partner_parent(self):
        parent = self.parent_id or False
        if self.is_company or not parent:
            return self
        return parent.get_partner_parent()
