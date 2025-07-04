# -*- coding: utf-8 -*-
##########################################################################
# Author      : O2b Technologies Pvt. Ltd.(<www.o2btechnologies.com>)
# Copyright(c): 2016-Present O2b Technologies Pvt. Ltd.
# All Rights Reserved.
#
# This program is copyright property of the author mentioned above.
# You can`t redistribute it and/or modify it.
#
##########################################################################
from odoo import models, fields, api


class CallLog(models.Model):
    _inherit = 'res.call.log'
    _description = '3CX Call Log'

    ticket_id = fields.Many2one('helpdesk.ticket', 'Ticket')
    transcription = fields.Char('Transcription')
    audio_url = fields.Char('Audio URL')
    company_id = fields.Many2one('res.company', string="company")
    description = fields.Char(string="Call Transcript")
    call_description = fields.Char(string="Call Description", groups="o2b_3cx_extend.group_call_description_access")
    call_ticket = fields.Char(string="Call Ticket Id")
    call_email = fields.Char(string="Call E-mail")
    call_phone = fields.Char(string="Call Phone")
    call_alternate = fields.Char(string="Call Alternate Phone")
    number = fields.Char(string="Call Number")
    partner_name_ai = fields.Char(string="Partner Name")

    # Added
    missed_call_test = fields.Char('Missed Call Text')
    historyid = fields.Char('History Id')
    callid = fields.Char('Call Id')
    reason_terminated = fields.Char('Reason Terminated')
    from_dn = fields.Char('From DN')
    dial_no = fields.Char('Dial No.')
    reason_changed = fields.Char('Reason Changed')
    final_number = fields.Char('Final Number')
    final_dn = fields.Char('Final DN')
    bill_code = fields.Char('Bill Code')
    bill_rate = fields.Char('Bill Rate')
    bill_cost = fields.Char('Bill Cost')
    bill_name = fields.Char('Bill Name')
    chain = fields.Char('Chain')
    missed_queue_calls = fields.Char('Missed Queue Calls')
    from_type = fields.Char('From Type')
    to_type = fields.Char('To Type')
    final_type = fields.Char('Final Type')
    final_dispname = fields.Char('Final Dispname')
    from_dispname = fields.Char('From Dispnam')
    to_dispname = fields.Char('To Dispname')
    to_dn = fields.Char('To DN')
    created_at = fields.Char('Created At')

    def action_open_partner_wizard(self):
        self.ensure_one()
        return {
            'name': 'Link/Create Partner',
            'type': 'ir.actions.act_window',
            'res_model': 'res.partner',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_name': self.partner_name_ai if self.partner_name_ai else f"New contact from number: {self.number}",
                'default_phone': self.call_phone,
                'default_alternative_phone': self.number,
                'default_email': self.call_email,
                'call_log_id_to_update': self.id, 
            }
        }

    def action_create_or_update_ticket(self):
        self.ensure_one()

        ticket_model = self.env['helpdesk.ticket']
        call_log = self

        if not self.partner_id:
            raise UserError("Please add a contact before proceeding.")

        if self.ticket_id:
            # Update existing ticket
            self.ticket_id.write({
                'partner_id': self.partner_id.id,
                'description': self.description,
                'call_description': self.call_description,
            })
            call_log.write({'ticket_id': self.ticket_id.id})
        else:
            # Create new ticket
            team = self.env['helpdesk.team'].sudo().search([('company_id', '=', call_log.company_id.id)], limit=1)
            new_ticket = ticket_model.create({
                # 'name': f"Ticket from Call Log {call_log.name}",
                'name': f"3cx Ticket from number: {self.number}",
                'partner_id': self.partner_id.id,
                'description': self.description,
                'call_description': self.call_description,
                'company_id': call_log.company_id.id,
                'team_id': team.id,
            })
            call_log.write({'ticket_id': new_ticket.id})

class ResPartner(models.Model):
    _inherit = 'res.partner'

    @api.model
    def create(self, vals):
        partner = super().create(vals)

        call_log_id = self.env.context.get('call_log_id_to_update')
        if call_log_id:
            call_log = self.env['res.call.log'].browse(call_log_id)
            if call_log.exists():
                call_log.write({'partner_id': partner.id})

        return partner

