from odoo import models, fields, api

class ProjectTimesheetInherit(models.Model):
    _inherit = "project.project"

    user_id = fields.Many2one('res.users', string="Project Manager")
    project_user_id = fields.Many2many('res.users', string="Project Users")

class TimesheetInherit(models.Model):
    _inherit = "account.analytic.line"

    project_id = fields.Many2one('project.project', string="Project",
                                 domain="['|', ('project_user_id', '=', uid), ('user_id', '=', uid)]")