# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class SpcsType(models.Model):
    _name = 'specs.type'
    _description = 'Specs Stage'
    _order = 'sequence, id'

    name = fields.Char(string='Stage name', required=True)
    active = fields.Boolean(string='Active', default=True)
    sequence = fields.Integer(string='Sequence')
    description = fields.Text(string='Description')
    rating_template_id = fields.Many2one('mail.template', string='Rating Email Template')
    code = fields.Char('Code')
    done = fields.Boolean('Done', help='If enabled, the specs in a done stage are considered as closed.')

