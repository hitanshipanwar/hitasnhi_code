# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class ProjectTask(models.Model):
	_inherit = 'project.task'

	@api.model
	def create(self, vals):
		if not self.env.user.has_group('project.group_project_manager'):
			raise ValidationError("You are not allowed to create tasks.")
		return super(ProjectTask, self).create(vals)
