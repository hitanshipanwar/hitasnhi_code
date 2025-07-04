# -*- coding: utf-8 -*-

from odoo import models, fields
from markupsafe import Markup
import uuid
import base64


class Config3CX(models.TransientModel):
    _inherit = 'config.3cx'

    company_id = fields.Many2one('res.company', string="Company", required="1")


    def generate_configuration(self):
        api_key = self._get_db_token()
        if self.db_token != api_key:
            api_key = self.db_token
            self.env['ir.config_parameter'].set_param('3cx.api.token', api_key)
        base_url = self.env['ir.config_parameter'].get_param('web.base.url')
        base_url = base_url.rstrip('/') + '/'
        config_template = Markup('<?xml version="1.0"?>' + "\n")
        config_template += self.env['ir.qweb']._render('nalios_3cx_full.3cx_template', {'base_url': base_url, 'api_key': api_key, 'rse_company': self.company_id})
        self.configuration = base64.encodebytes(config_template.encode('utf-8'))
        return {
            'type': 'ir.actions.act_window',
            'name': '3CX Configuration',
            'view_mode': 'form',
            'res_model': 'config.3cx',
            'res_id': self.id,
            'target': 'new',
        }