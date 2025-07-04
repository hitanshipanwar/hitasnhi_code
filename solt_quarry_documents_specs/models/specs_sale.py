# -*- coding: utf-8 -*-

import ast

from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.tools import frozendict


class SpecsSale(models.Model):
    _name = 'specs.sale'
    _inherit = ['specs.sale', 'documents.mixin']

    use_documents = fields.Boolean("Use Documents", default=True)
    documents_folder_id = fields.Many2one('documents.folder', string="Workspace",
                                          domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]",
                                          copy=False, company_dependent=True, store=True,
                                          help="Workspace in which all of the documents of this spec will be categorized. All of the attachments of your spec will be automatically added as documents in this workspace as well.")
    documents_tag_ids = fields.Many2many('documents.tag', 'spec_documents_tag_rel', string="Default Tags",
                                         domain="[('folder_id', 'parent_of', documents_folder_id)]", copy=True, company_dependent=True, store=True)
    document_count = fields.Integer(compute='_compute_attached_document_count', string="Number of documents in Spec",
                                    groups='documents.group_documents_user')

    def _compute_attached_document_count(self):
        Document = self.env['documents.document']
        spec_document_read_group = Document._read_group(
            [('res_model', '=', 'specs.sale'), ('res_id', 'in', self.ids)],
            ['res_id'],
            ['__count'],
        )
        document_count_per_spec_id = dict(spec_document_read_group)
        for spec in self:
            spec.document_count = document_count_per_spec_id.get(spec.id, 0)

    @api.onchange('documents_folder_id')
    def _onchange_documents_folder_id(self):
        self.env['documents.document'].search([
            ('res_model', '=', 'specs.sale'),
            ('res_id', 'in', self.ids),
            ('folder_id', '=', self._origin.documents_folder_id.id),
        ]).folder_id = self.documents_folder_id
        self.documents_tag_ids = False

    def _create_missing_folders(self):
        folders_to_create_vals = []
        specs_with_folder_to_create = []
        documents_project_folder_id = self.env.ref('solt_quarry_documents_specs.documents_specs_folder').id

        for specs in self:
            if not specs.documents_folder_id and specs.name:
                folder_vals = {
                    'name': specs.name,
                    'parent_folder_id': documents_project_folder_id,
                    'company_id': specs.company_id.id,
                }
                folders_to_create_vals.append(folder_vals)
                specs_with_folder_to_create.append(specs)

        created_folders = self.env['documents.folder'].sudo().create(folders_to_create_vals)
        for specs, folder in zip(specs_with_folder_to_create, created_folders):
            specs.sudo().documents_folder_id = folder

    @api.model_create_multi
    def create(self, vals_list):
        specs = super().create(vals_list)
        if not self.env.context.get('no_create_folder'):
            specs.filtered(lambda specs: specs.use_documents)._create_missing_folders()
        return specs

    def write(self, vals):
        if 'company_id' in vals:
            for spec in self:
                if spec.documents_folder_id and spec.documents_folder_id.company_id and len(spec.documents_folder_id.specs_ids) > 1:
                    other_specs = spec.documents_folder_id.specs_ids - self
                    if other_specs and other_specs.company_id.id != vals['company_id']:
                        lines = [f"- {spec.name}" for spec in other_specs]
                        raise UserError(_(
                            'You cannot change the company of this spec, because its workspace is linked to the other following spces that are still in the "%s" company:\n%s\n\n'
                            'Please update the company of all specs so that they remain in the same company as their workspace, or leave the company of the "%s" workspace blank.',
                            other_specs.company_id.name, '\n'.join(lines), spec.documents_folder_id.name))

        if 'name' in vals and len(self.documents_folder_id.specs_ids) == 1 and self.name == self.documents_folder_id.name:
            self.documents_folder_id.sudo().name = vals['name']
        res = super().write(vals)
        if 'company_id' in vals:
            for spec in self:
                if spec.documents_folder_id and not spec.documents_folder_id.company_id:
                    spec.documents_folder_id.company_id = spec.company_id
        if not self.env.context.get('no_create_folder'):
            self.filtered('use_documents')._create_missing_folders()
        return res

    @api.returns('self', lambda value: value.id)
    def copy(self, default=None):
        # We have to add no_create_folder=True to the context, otherwise a folder
        # will be automatically created during the call to create.
        # However, we cannot use with_context, as it intanciates a new recordset,
        # and this copy would call itself infinitely.
        previous_context = self.env.context
        self.env.context = frozendict(self.env.context, no_create_folder=True)
        spec = super().copy(default)
        self.env.context = previous_context

        if not self.env.context.get('no_create_folder') and spec.use_documents and self.documents_folder_id:
            spec.documents_folder_id = self.documents_folder_id.copy({'name': spec.name})
        return spec

    def _get_document_tags(self):
        return self.documents_tag_ids

    def _get_document_folder(self):
        return self.documents_folder_id

    def _check_create_documents(self):
        return self.use_documents and super()._check_create_documents()

    def action_view_documents_specs(self):
        self.ensure_one()
        action = self.env['ir.actions.act_window']._for_xml_id('solt_quarry_documents_specs.action_view_documents_project_task')
        action['context'] = {
            **ast.literal_eval(action['context'].replace('active_id', str(self.id))),
            'default_tag_ids': self.documents_tag_ids.ids,
            'default_documents_folder_id': self.documents_folder_id.id
        }
        return action

