from odoo import models, fields, api, _
import re

class HelpdeskTicket(models.Model):
    _inherit = 'helpdesk.ticket'

    phone_lost = fields.Char(string=_('Lost Phone Number'))
    is_user_assigned = fields.Boolean(string='current user assigned',compute="_compute_current_user_assigned")

    def _compute_current_user_assigned(self):
        for ticket in self:
            user_assign = False
            if ticket.user_id.id == self.env.uid:
                user_assign = True
            ticket.is_user_assigned = user_assign

    @api.model
    def extract_msg_details(self, msg):
        '''Extracts the phone number from the body of a msg and finds the contact with that number.'''
        emails = self.env['ir.config_parameter'].sudo().get_param('voip_email').split(',')
        if self.env['res.partner'].browse([msg['author_id']]).email_normalized in emails:
            r = re.compile(r'\d{10}')
            results = r.findall(msg['body'])
            if results:
                partners = self.env['res.partner'].search([('phone', 'like', '{}%{}%{}'.format(results[0][0:3], results[0][3:6], results[0][6:10]))])
                if partners:
                    oldest = partners.sorted(key='create_date')[0]
                    return {'phone_lost': results[0], 'partner_id': oldest.id, 'partner_email': oldest.email}
                else:
                    return {'phone_lost': results[0]}

    @api.model
    def message_new(self, msg, custom_values=None):
        emails = self.env['ir.config_parameter'].sudo().get_param('voip_email').split(',')
        if self.env['res.partner'].browse([msg['author_id']]).email_normalized in emails:
            ticket = super(HelpdeskTicket, self).message_new(msg, custom_values)
            partner_values = self.extract_msg_details(msg)
            if partner_values:
                ticket.write(partner_values)
            return ticket
        return False