from odoo import api, fields, models


class helpdeskTicketType(models.Model):
    _inherit = 'helpdesk.ticket.type'

    old_id = fields.Char(string='old id')
    