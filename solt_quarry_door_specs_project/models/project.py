# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class Project(models.Model):
    _inherit = 'project.project'

    is_card_request_project = fields.Boolean('Is CAD request', help="Technical field to indicate if it is the CAD request project.")

    @api.constrains('is_card_request_project')
    def _check_is_card_request_project(self):
        for project in self:
            if project.is_card_request_project:
                projects = self.env['project.project'].search([('id', '!=', project.id), ('is_card_request_project', '=', True)])
                if projects:
                    raise ValidationError(_("There is already a project marked as CAD request."))


class ProjectTask(models.Model):
    _inherit = "project.task"

    specs_id = fields.Many2one('specs.sale', string='Specs Sheet')
    specs_count = fields.Integer('Specs count', compute='_compute_specs_count')
    is_card_request_project = fields.Boolean(related='project_id.is_card_request_project')

    @api.depends('specs_id')
    def _compute_specs_count(self):
        for task in self:
            task.specs_count = len(task.specs_id)

    def specs_call_view(self):
        self.ensure_one()
        if not self.specs_id:
            return {'type': 'ir.actions.act_window_close'}
        action = self.env['ir.actions.act_window']._for_xml_id('solt_quarry_door_sale.action_specs_sale')
        domain = [('id', 'in', self.specs_id.ids)]
        context = self.env.context.copy()
        if len(self.specs_id) == 1:
            form_view = [(self.env.ref('solt_quarry_door_sale.specs_sale_view_form').id, 'form')]
            if 'views' in action:
                action['views'] = form_view + [(state, view) for state, view in action['views'] if view != 'form']
            else:
                action['views'] = form_view
            action['res_id'] = self.specs_id.id

        if domain:
            action['domain'] = domain
        context.update({
            'create': False, 'edit': False, 'delete': False
        })
        action['context'] = context
        return action