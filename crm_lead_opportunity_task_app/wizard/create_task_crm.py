# -*- coding: utf-8 -*-


from odoo import fields, models, api, _
from odoo.exceptions import UserError

class CreateTaskCRM(models.TransientModel):
    _name = "task.crm"
    _description = "Create Task CRM"

    crm_id = fields.Many2one('crm.lead','Name')
    project_id = fields.Many2one('project.project', 'Project')
    user_id = fields.Many2one('res.users', 'Assigned to')
    date_deadline = fields.Date('Deadline')
    partner_id = fields.Many2one('res.partner','Partner')
    tag_ids = fields.Many2many('project.tags', string='Tags')
    assigning_date = fields.Date('Assigning Date', default=fields.Date.context_today)
    company_id = fields.Many2one('res.company','Company')
    description = fields.Char('Description')
    stage_id = fields.Many2one('project.task.type','Stage')

    @api.model
    def default_get(self , fields):
        res = super(CreateTaskCRM, self).default_get(fields)
        crm_id = self.env['crm.lead'].browse(self._context.get('active_id'))
        res['crm_id'] = crm_id.id,
        res['user_id'] = crm_id.user_id.id,
        res['partner_id'] = crm_id.partner_id.id,
        res['company_id'] = crm_id.company_id.id,
        return res


    def create_task(self):
        task_obj = self.env['project.task']
        task_create_obj = task_obj.create({
                                    'name': self.crm_id.name,
                                    'project_id': self.project_id.id,
                                    'user_ids': self.user_id.ids,
                                    'date_deadline': self.date_deadline,
                                    'tag_ids': [(6, 0, self.tag_ids.ids)],
                                    'partner_id': self.partner_id.id,
                                    'description': self.description,
                                    'date_assign': self.assigning_date,
                                    'company_id': self.company_id.id,
                                    'stage_id': self.stage_id.id,
                                    'crm_id': self.crm_id.id,
                                    })
        crm_lead = self.env['crm.lead'].browse(self._context.get('active_id'))
        crm_lead.write({
                    'task_ids'  : [(4, task_create_obj.id)]
                    })
        kanban_view_id = self.env.ref('project.view_task_kanban').id
        form_view_id = self.env.ref('project.view_task_form2').id
        return {
            'name': _('Tasks'),
            'view_type': 'kanban',
            'view_mode': 'kanban,form',
            'views': [(kanban_view_id, 'kanban'),(form_view_id, 'form')],
            'res_model': 'project.task',
            'domain': [('id', '=', task_create_obj.id)],
            'type': 'ir.actions.act_window',
            }

