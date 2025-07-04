
from odoo import api, Command, fields, models, _
from odoo.exceptions import ValidationError


class HelpdeskTeam(models.Model):
    _inherit = "helpdesk.team"

    is_card_request_team = fields.Boolean('Is CAD request',
                                             help="Technical field to indicate if it is the CAD request team.")

    @api.constrains('is_card_request_team')
    def _check_is_card_request_team(self):
        for team in self:
            if team.is_card_request_team:
                teams = self.env['helpdesk.team'].search(
                    [('id', '!=', team.id), ('is_card_request_team', '=', True), ('company_id', '=', team.company_id.id)])
                if teams:
                    raise ValidationError(_(f"There is already a team marked as CAD for the company {team.company_id.name}."))