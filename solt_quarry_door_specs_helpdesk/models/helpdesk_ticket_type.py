# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from odoo.exceptions import ValidationError


class HelpdeskTicketType(models.Model):
    _inherit = 'helpdesk.ticket.type'

    is_card_request_ticket_type = fields.Boolean('Is CAD request',
                                          help="Technical field to indicate if it is the CAD request ticket type.")

    @api.constrains('is_card_request_ticket_type')
    def _check_is_card_request_ticket_type(self):
        for ticket_type in self:
            if ticket_type.is_card_request_ticket_type:
                teams = self.env['helpdesk.ticket.type'].search(
                    [('id', '!=', ticket_type.id), ('is_card_request_ticket_type', '=', True)])
                if teams:
                    raise ValidationError(
                        _(f"There is already a team marked as CAD request."))