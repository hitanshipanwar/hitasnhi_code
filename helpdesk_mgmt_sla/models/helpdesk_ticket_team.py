# -*- coding: utf-8 -*-

from odoo import fields, models


class HelpdeskTicketTeam(models.Model):
    _inherit = "helpdesk.ticket.team"

    use_sla = fields.Boolean(string="Use SLA")
    resource_calendar_id = fields.Many2one(
        "resource.calendar",
        "Working Hours",
        default=lambda self: self.env.company.resource_calendar_id,
    )
    # resource_calendar_id = fields.Many2one(
    #     "resource.calendar",
    #     "Working Hours",
    #     default=lambda self: self.env.company.resource_calendar_id,
    #     domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]",
    # )
