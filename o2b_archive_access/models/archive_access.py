from odoo import api, Command, fields, models,_
from odoo.exceptions import AccessError
from odoo.exceptions import UserError, AccessDenied



class HelpdeskTicketInherit(models.Model):
    _inherit = 'helpdesk.ticket'

    active = fields.Boolean(default=True  , tracking=True)
    def write(self, vals):

        res = super(HelpdeskTicketInherit, self).write(vals)
        if 'active' in vals:
            if self.env.user.has_group('helpdesk.group_helpdesk_manager') or self.env.user.has_group('base.group_system') or self.env.user.has_group('base.group_erp_manager'):
                return res
            else:
                raise AccessError("You do not have permission to Archive tickets.")   
        return res

class ResPartnerInherit(models.Model):
    _inherit = 'res.partner'

    active = fields.Boolean(default=True , tracking=True) 
    
    def write(self, vals):
        if 'active' in vals:
            if self.env.user.has_group('helpdesk.group_helpdesk_manager') or self.env.user.has_group('base.group_system') or self.env.user.has_group('base.group_erp_manager')  :
                return super(ResPartnerInherit, self).write(vals)
            else:
                raise AccessError("You do not have permission to Archive contact.")
        return super(ResPartnerInherit, self).write(vals)


    