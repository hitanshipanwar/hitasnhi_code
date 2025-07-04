# -*- coding: utf-8 -*-

from odoo import models, fields, api


class CallLog(models.Model):
    _name = 'res.call.log'
    _description = '3CX Call Log'

    name = fields.Char('Call System')
    partner_id = fields.Many2one('res.partner', 'Contact')
    date = fields.Char('Date')
    ttype = fields.Char('Call Type')
    entitytype = fields.Char('Entity Type')
    agentname = fields.Char('Agent')
    agent = fields.Char('Agent ext.')
    call_start = fields.Char('Call Start')
    call_established = fields.Char('Call Established')
    call_end = fields.Char('Call End')
    duration = fields.Char('Duration')
    details = fields.Char('Details')