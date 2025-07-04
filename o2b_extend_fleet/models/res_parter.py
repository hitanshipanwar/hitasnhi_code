# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import date, timedelta

class ResPartner(models.Model):
    _inherit = 'res.partner'

    fine_count = fields.Integer(string='Fine Count', compute='_compute_fine_count')

    def _compute_fine_count(self):
        for record in self:
            record.fine_count = self.env['fleet.fine'].search_count([('driver_id', '=', record.id)])

    def action_view_fines(self):
        return {
            'name': 'Fines',
            'type': 'ir.actions.act_window',
            'res_model': 'fleet.fine',
            'view_mode': 'tree,form',
            'domain': [('driver_id', '=', self.id)],
            'context': {'default_driver_id': self.id, 'search_default_groupby_driver': 1},
        }
