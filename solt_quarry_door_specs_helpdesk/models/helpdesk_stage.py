# -*- coding: utf-8 -*-

from odoo import models, fields, api


class HelpdeskStage(models.Model):
    _inherit = 'helpdesk.stage'

    is_update_required_stage = fields.Boolean(
        'CAD Update Required',
        help='Indicate if the stage is the Update Required.')
    is_finished_stage = fields.Boolean(
        'CAD Finish stage',
        help='Indicate if the stage is the CAD Finish.')
    has_cad_request_team = fields.Boolean(compute='_compute_has_cad_request_team')

    @api.depends('team_ids')
    def _compute_has_cad_request_team(self):
        for record in self:
            record.has_cad_request_team = False
            if record.team_ids and record.team_ids.filtered(lambda t: t.is_card_request_team):
                record.has_cad_request_team = True