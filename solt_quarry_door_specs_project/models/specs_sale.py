# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class SpecsSale(models.Model):
    _inherit = 'specs.sale'

    task_id = fields.Many2one('project.task', 'Generated Task', index=True, copy=False)

    def action_create_task(self):
        self.ensure_one()
        project_id = self.sudo().with_company(self.company_id)._get_card_request_project()
        if not project_id:
            raise UserError(_("There is no project configured as CAD request."))

        self._create_card_request_task(project_id)

    def _get_card_request_project(self):
        return self.env['project.project'].search([('is_card_request_project', '=', True)]) or False

    def _create_card_request_task(self, project):
        """ Generate task for the given Specs, and link it to the project.
            :param project: record of project.project in which the task should be created
            :return task: record of the created task
        """
        values = self._create_task_prepare_values(project)
        task = self.env['project.task'].sudo().create(values)
        self.write({'task_id': task.id})
        # post message on task
        task_msg = _("This task has been created from: %s (%s)",
                     self._get_html_link(), self.name)
        task.message_post(body=task_msg)
        return task

    def _create_task_prepare_values(self, project):
        return {
            'name': self.name,
            'partner_id': self.specs_sale_id.partner_id.id,
            'project_id': project.id,
            'company_id': project.company_id.id,
            'specs_id': self.id,
            'user_ids': False,  # force non assigned task, as created as sudo()
        }

