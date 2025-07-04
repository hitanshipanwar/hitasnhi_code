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
from odoo import  fields, models ,api
import logging

_logger = logging.getLogger(__name__)

class OnlyModifyTickets(models.Model):
    _inherit = 'helpdesk.ticket'

    desafiliaciones_numero_control = fields.Text(string='Desafiliaciones - Numero de Control')
    desafiliaciones_beneficios = fields.Many2many( 'add.list.value',string="Desafiliaciones - Beneficios" )
    
    
    @api.model
    def _get_view_cache_key(self, view_id=None, view_type='form', **options):
        key = super()._get_view_cache_key(view_id, view_type, **options)
        key = key + (self.env.user.has_group('o2b_missing_fields.helpdesk_educational_call'),)
        _logger.info("key user <%s> to <%s>", self.env.user.login, key)
        return key

    @api.model
    def _get_view(self, view_id=None, view_type='form', **options):
        arch, view = super()._get_view(view_id, view_type, **options)
        restrict_group = self.env.ref('o2b_missing_fields.helpdesk_educational_call')
        _logger.info("restrict_group user <%s> to <%s>", self.env.user.login, restrict_group)
        if  self.env.user.has_group('o2b_missing_fields.helpdesk_educational_call'):
            if view_type == 'tree':
                for node in arch.xpath("//tree"):
                    node.set('create', '0')
            elif view_type == 'form':
                for node in arch.xpath("//form"):
                    node.set('create', '0')
            elif view_type == 'kanban':
                for node in arch.xpath("//kanban"):
                    node.set('create', '0')          
        return arch, view


class HelpdeskAddValue(models.Model):

    _name = "add.list.value"
    _description = "Add List Value"
    _order = 'add_value'

    add_value = fields.Text(string='List Items' , required=True)

    def name_get(self):
        result = []
        for record in self:
            name = f"{record.add_value}"
            result.append((record.id, name))
        return result