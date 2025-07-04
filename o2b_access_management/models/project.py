# -*- coding: utf-8 -*-
from odoo import models, api, exceptions, _
from odoo.exceptions import AccessError

class ProjectTask(models.Model):
    _inherit = "project.task"

    @api.model
    def create(self, vals):
        """Restrict creation for users in project.group_project_user."""
        if self.env.user.has_group('project.group_project_user') and not self.env.user.has_group('project.group_project_manager'):
            raise AccessError(_("You are not allowed to create tasks."))
        return super(ProjectTask, self).create(vals)

    def unlink(self):
        """Restrict deletion for users in project.group_project_user."""
        if self.env.user.has_group('project.group_project_user') and not self.env.user.has_group('project.group_project_manager'):
            raise AccessError(_("You are not allowed to delete tasks."))
        return super(ProjectTask, self).unlink()
