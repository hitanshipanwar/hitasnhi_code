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


class Partner(models.Model):
    _inherit = 'helpdesk.ticket'

    description = fields.Char(string="Call Transcript")
    audio_url = fields.Char(string="3CX Audio URL")
    call_description = fields.Char(string="Call Description", groups="o2b_3cx_extend.group_call_description_access")

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        args = args or []
        if name:
            tickets = self.search([('ticket_ref', operator, name)] + args, limit=limit)
            if not tickets:
                tickets = self.search([('name', operator, name)] + args, limit=limit)
            return tickets.name_get()
        return super().name_search(name, args=args, operator=operator, limit=limit)