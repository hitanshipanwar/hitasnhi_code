from odoo import models, api

class HelpdeskTicket(models.Model):
    _inherit = 'helpdesk.ticket'

    @api.model
    def _find_or_create_partner(self, partner_name, partner_email, company=False):
        if company:
            company = False
        return super(HelpdeskTicket, self)._find_or_create_partner(partner_name, partner_email, company)