# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError, ValidationError

class ResUeser(models.Model):
    _inherit = 'res.company'


    fax = fields.Char(string="FAX")