from odoo import api, fields, models


class ResUsers(models.Model):
    _inherit = 'res.users'

    is_nurse = fields.Boolean(string="Is Nurse")
    old_id = fields.Char(string="Old ID")
    old_partner_id = fields.Char(string="Old Partner id")
    