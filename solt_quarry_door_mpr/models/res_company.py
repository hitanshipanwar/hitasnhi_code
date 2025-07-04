# -*- coding: utf-8 -*-

from odoo import api, exceptions, fields, models, _


class ResCompany(models.Model):
    _inherit = 'res.company'

    create_draft_mo = fields.Boolean(string='Create MO in draft', readonly=False)