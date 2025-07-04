from odoo import api, fields, models


class HelpdeskCategory(models.Model):
    _name = 'helpdesk.category'
    _description = 'category'

    name = fields.Char(string='Name')
    ticket_type_id = fields.Many2one(comodel_name='helpdesk.ticket.type', string="helpdesk Ticket Type")
    is_contacted = fields.Boolean(string='Contacted')
    old_id = fields.Char(string='old id')
    