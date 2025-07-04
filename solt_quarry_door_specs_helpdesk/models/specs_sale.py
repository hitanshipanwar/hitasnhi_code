# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class SpecsSale(models.Model):
    _inherit = 'specs.sale'

    ticket_id = fields.Many2one('helpdesk.ticket', 'Generated Ticket', index=True, copy=False)
    is_ticket_canceled = fields.Boolean(compute='_compute_is_ticket_canceled')

    def _get_name_for_ticket(self):
        self.ensure_one()
        qty = sum(self.specs_sale_id.order_line.filtered(lambda line: line.name == self.name).mapped('product_uom_qty'))
        name = f'{self.specs_sale_id.name} {qty} {self.name} {self.version}'
        return name

    def action_create_ticket(self):
        self.ensure_one()
        team_id = self.sudo().with_company(self.company_id)._get_card_request_team()
        if not team_id:
            raise UserError(_(f"There is no team configured as CAD request for the company {self.company_id.name}."))

        ticket_type_id = self.sudo().with_company(self.company_id)._get_card_request_ticket_type()
        if not ticket_type_id:
            raise UserError(_(f"There is no ticket type configured as CAD request for the company {self.company_id.name}."))

        self._create_card_request_ticket(team_id, ticket_type_id)

    def _get_card_request_team(self):
        return self.env['helpdesk.team'].search([('is_card_request_team', '=', True)]) or False

    def _get_card_request_ticket_type(self):
        return self.env['helpdesk.ticket.type'].search([('is_card_request_ticket_type', '=', True)]) or False

    def _create_card_request_ticket(self, team_id, ticket_type_id):
        """ Generate ticket helpdesk for the given Specs.
            :param team_id: record of helpdesk.team
            :param ticket_type_id: record of helpdesk.ticket.type
            :return ticket: record of the created ticket
        """
        if self.ticket_id and self.is_ticket_canceled:
            stage_new = self.env.ref('helpdesk.stage_new')
            self.write(
                {'stage_id': self.env.ref("solt_quarry_door_specs_helpdesk.stage_cad_request")})
            self.ticket_id.stage_id = stage_new
            ticket_msg = _("This ticket has been activated from: %s (%s)",
                           self._get_html_link(), self.name)
            ticket = self.ticket_id
        else:
            values = self._create_ticket_prepare_values(team_id, ticket_type_id)
            ticket = self.env['helpdesk.ticket'].sudo().create(values)
            ticket.message_unsubscribe(partner_ids=self.specs_sale_id.partner_id.ids)
            self.write({'ticket_id': ticket.id, 'stage_id': self.env.ref("solt_quarry_door_specs_helpdesk.stage_cad_request")})
            # post message on task
            ticket_msg = _("This ticket has been created from: %s (%s)",
                         self._get_html_link(), self.name)
        ticket.message_post(body=ticket_msg)
        return ticket

    def _create_ticket_prepare_values(self, team_id, ticket_type_id):
        self.ensure_one()
        return {
            'name': self._get_name_for_ticket(),
            'partner_id': self.specs_sale_id.partner_id.id,
            'team_id': team_id.id,
            'ticket_type_id': ticket_type_id.id,
            'specs_id': self.id,
        }

    def action_update_ticket_required(self):
        self.ensure_one()
        update_ticket_required_stage_id = self.env['helpdesk.stage'].search([('is_update_required_stage', '=', True)], limit=1)
        if not update_ticket_required_stage_id:
            raise UserError(_("There is no stage configured as CAD Update Required for the cad request."))
        if self.ticket_id:
            self.ticket_id.stage_id = update_ticket_required_stage_id

    def action_finish_ticket(self):
        self.ensure_one()
        update_ticket_finish_stage_id = self.env['helpdesk.stage'].search([('is_finished_stage', '=', True)],
                                                                              limit=1)
        if not update_ticket_finish_stage_id:
            raise UserError(_("There is no stage configured as CAD finish for the cad request."))
        if self.ticket_id:
            self.ticket_id.stage_id = update_ticket_finish_stage_id
            self.stage_id = self.env.ref("solt_quarry_door_sale.stage_planned", raise_if_not_found=False)

    def _get_state_list(self):
        states = super(SpecsSale, self)._get_state_list()
        return states + ['cad_request_stage']

    def _get_helpdesk_cancel_stage(self):
        cancel_stage_id = self.env.ref('solt_quarry_door_specs_helpdesk.helpdesk_stage_cancelled')
        if not cancel_stage_id:
            raise UserError(_("There is no stage configured as Canceled."))
        return cancel_stage_id

    def action_state_cancel(self):
        super(SpecsSale, self).action_state_cancel()
        cancel_stage_id = self._get_helpdesk_cancel_stage()
        for record in self:
            if record.ticket_id:
                record.ticket_id.stage_id = cancel_stage_id
                ticket_msg = _("This ticket has been canceled from: %s (%s)",
                               record._get_html_link(), record.name)
                record.ticket_id.message_post(body=ticket_msg)

    @api.depends('ticket_id')
    def _compute_is_ticket_canceled(self):
        for record in self:
            record.is_ticket_canceled = True if record.ticket_id and record.ticket_id.stage_id == record._get_helpdesk_cancel_stage() else False

