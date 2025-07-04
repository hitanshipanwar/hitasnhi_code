# -*- coding: utf-8 -*-

from odoo import models, fields, exceptions, api, _
from odoo.exceptions import UserError, ValidationError

class projecttask(models.Model):
    _inherit = "project.task"

    crm_id = fields.Many2one('crm.lead','CRM Pipeline/Lead')


class crm_lead(models.Model):
    _inherit = 'crm.lead'

    crm_count = fields.Integer(string="Tasks",compute="get_quotation_count")
    task_ids = fields.Many2many('project.task', string='Tasks')
    project_ids = fields.One2many('project.project', 'crm_id', string="Projects")
    has_project = fields.Boolean(string="Has Project", compute="_compute_has_project")

    @api.depends('project_ids')
    def _compute_has_project(self):
        for rec in self:
            rec.has_project = bool(rec.project_ids)

    def open_task_from_view_action(self):
        action = self.env["ir.actions.actions"]._for_xml_id("project.action_view_all_task")
        action['domain'] = [('crm_id','=',self.id)]
        return action


    def get_quotation_count(self):
        count = self.env['project.task'].search_count([('crm_id','=',self.id)])
        self.crm_count = count

    def action_open_project_form(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Create Project',
            'res_model': 'project.project',
            'view_mode': 'form',
            'target': 'new',
            'view_id': self.env.ref('crm_lead_opportunity_task_app.custom_project_creation_form_view').id,
            'context': {
                'default_partner_id': self.partner_id.id,
                'default_crm_id': self.id,
            }
        }

    def open_related_projects(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Projects',
            'view_mode': 'tree,form',
            'res_model': 'project.project',
            'domain': [('crm_id', '=', self.id)],
            'context': {'default_crm_id': self.id},
        }

class ProjectProject(models.Model):
    _inherit = 'project.project'

    partner_id = fields.Many2one('res.partner', string="Customer")
    crm_id = fields.Many2one('crm.lead', string="Lead")

    def action_save(self):
        return {
            'type': 'ir.actions.act_window_close',
        }



