# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class CrmTeam(models.Model):
    _inherit = 'crm.team'

    code = fields.Char("Short name")
    team_sequence_id = fields.Many2one('ir.sequence', 'Team sequence', copy=False)
    sale_journal_id = fields.Many2one('account.journal', 'Sales journal', domain="[('type', '=', 'sale')]")
    pricelist_id = fields.Many2one('product.pricelist', 'Pricelist')
    spec_team_sequence_id = fields.Many2one('ir.sequence', 'Spec sequence', copy=False)

    _sql_constraints = [('code_uniq', 'unique (code)', "This short name already exists!")]

    @api.model_create_multi
    def create(self, vals_list):
        teams = super(CrmTeam, self).create(vals_list)
        teams._create_team_sequences()
        return teams

    def _create_team_sequences(self):
        for team in self:
            if not team.team_sequence_id:
                team.team_sequence_id = self.env['ir.sequence'].sudo().create({
                    'name': f"[{team.code}] {team.name}",
                    'prefix': f"EST-{team.code}",
                    'implementation': 'standard',
                    'code': f"{team._name}.{team.code.lower()}",
                    'padding': 6,
                    'number_increment': 1,
                    'company_id': team.company_id.id
                })
            if not team.spec_team_sequence_id:
                team.spec_team_sequence_id = self.env['ir.sequence'].sudo().create({
                    'name': f"[{team.code}] Specs {team.name}",
                    'prefix': f"{team.code}",
                    'implementation': 'standard',
                    'code': f"{team._name}.{team.code.lower()}.specs.sale",
                    'padding': 6,
                    'number_increment': 1,
                    'company_id': team.company_id.id
                })

    def write(self, vals):
        for record in self:
            if 'code' in vals and (record.team_sequence_id or record.spec_team_sequence_id):
                raise UserError(_("Invalid operation. The short name can not be changed because a sequence has already been created for it."))

        res = super(CrmTeam, self).write(vals)
        self._create_team_sequences()
        return res
