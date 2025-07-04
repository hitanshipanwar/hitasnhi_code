# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class HelpdeskTicket(models.Model):
    _inherit = 'helpdesk.ticket'

    warning_msg = fields.Text(compute="compute_warning_msg")
    specs_count = fields.Integer('Specs count', compute='_compute_specs_count')
    specs_id = fields.Many2one('specs.sale', string='Specs Sheet')

    @api.depends('team_id', 'ticket_type_id')
    def compute_warning_msg(self):
        for record in self:
            record = record.with_company(record.company_id)
            record.warning_msg = ''
            if record.team_id and record.team_id.is_card_request_team and (not record.ticket_type_id or not record.ticket_type_id.is_card_request_ticket_type):
                record.warning_msg = (_(f"The selected team is {record.team_id.name} team, so the ticket type must be set to: Is CAD request."))
            if record.ticket_type_id and record.ticket_type_id.is_card_request_ticket_type and (not record.team_id or not record.team_id.is_card_request_team):
                record.warning_msg = (_(f"The selected type is set like \"Is CAD request type\", so the ticket team must be set to: Is CAD request team."))

    @api.constrains('team_id', 'ticket_type_id')
    def _check_tickets(self):
        if self.warning_msg:
            raise ValidationError(self.warning_msg)

    @api.depends('specs_id')
    def _compute_specs_count(self):
        for ticket in self:
            ticket.specs_count = len(ticket.specs_id)

    def specs_call_view(self):
        self.ensure_one()
        if not self.specs_id:
            return {'type': 'ir.actions.act_window_close'}
        action = self.env['ir.actions.act_window']._for_xml_id('solt_quarry_door_sale.action_specs_sale')
        domain = [('id', 'in', self.specs_id.ids)]
        context = self.env.context.copy()
        if len(self.specs_id) == 1:
            form_view = [(self.env.ref('solt_quarry_door_sale.specs_sale_view_form').id, 'form')]
            if 'views' in action:
                action['views'] = form_view + [(state, view) for state, view in action['views'] if view != 'form']
            else:
                action['views'] = form_view
            action['res_id'] = self.specs_id.id

        if domain:
            action['domain'] = domain
        context.update({
            'create': False, 'edit': False, 'delete': False
        })
        action['context'] = context
        return action
