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
from odoo.exceptions import AccessError
from odoo import api, Command, fields, models, tools, _, SUPERUSER_ID


class CustomChannel(models.Model):
    _inherit = 'mail.channel'

    @api.returns('mail.message', lambda value: value.id)
    def message_post(self, *, message_type='notification', **kwargs):
        if not self.env.user.has_group('o2b_Conversation_AccessRights.group_conversation_access'):
            raise AccessError(_("No tienes los derechos de acceso necesarios para enviar mensajes en esta conversación."))
        return super(CustomChannel, self).message_post(message_type=message_type, **kwargs)