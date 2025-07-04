# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
# from .connection import BillComService
import json


class Company(models.Model):
    _inherit = 'res.company'

    create_batch_payment = fields.Boolean(string="Create Bill.Com Payments Batch", readonly=False)

    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None, order=None):
        if 'is_company_check' in self._context:
            company_configure_parameter = self.env['bill.com.config'].search([('company_ids', '!=',[])])
            args += [('id', 'in', company_configure_parameter.company_ids.ids)]
        return super(Company, self)._name_search(name, args, operator, limit, name_get_uid)
