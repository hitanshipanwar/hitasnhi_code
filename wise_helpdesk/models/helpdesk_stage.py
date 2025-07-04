from odoo import api, fields, models


class helpdeskStage(models.Model):
    _inherit = 'helpdesk.stage'

    old_id = fields.Char(string='old id')
    is_solved = fields.Boolean(string="Is Solved")

class helpdeskTeam(models.Model):
    _inherit = 'helpdesk.team'

    old_id = fields.Char(string='old id')
    