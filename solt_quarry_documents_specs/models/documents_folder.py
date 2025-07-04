# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.osv import expression


class DocumentFolder(models.Model):
    _inherit = 'documents.folder'

    def default_get(self, fields):
        res = super().default_get(fields)
        if self.env.context.get('documents_specs') and not res.get('parent_folder_id'):
            res['parent_folder_id'] = self.env.ref('solt_quarry_documents_specs.documents_specs_folder').id
        return res

    specs_ids = fields.One2many('specs.sale', 'documents_folder_id')

    @api.model
    def _name_search(self, name, domain=None, operator='ilike', limit=None, order=None):
        domain = domain or []
        if 'specs_documents_template_folder' in self.env.context:
            template_folder_id = self.env.context.get('specs_documents_template_folder')
            domain = expression.AND([
                domain,
                ['!', ('id', 'child_of', template_folder_id)]
            ])
        return super()._name_search(name, domain, operator, limit, order)

    @api.ondelete(at_uninstall=False)
    def unlink_except_specs_folder(self):
        specs_folder = self.env.ref('solt_quarry_documents_specs.documents_specs_folder')
        if specs_folder in self:
            raise UserError(_('The "%s" workspace is required by the Specs application and cannot be deleted.', specs_folder.name))

    @api.constrains('company_id')
    def _check_no_company_on_specs_folder(self):
        if not self.company_id:
            return
        specs_folder = self.env.ref('solt_quarry_documents_specs.documents_specs_folder')
        if specs_folder in self:
            raise UserError(_("You cannot set a company on the %s workspace.", specs_folder.name))

    @api.constrains('company_id')
    def _check_company_is_specs_company(self):
        for folder in self:
            if folder.specs_ids and folder.specs_ids.company_id:
                different_company_specs = folder.specs_ids.filtered(lambda spec: spec.company_id != self.company_id)
                if not different_company_specs:
                    continue
                if len(different_company_specs) == 1:
                    spec = different_company_specs[0]
                    message = _('This workspace should remain in the same company as the "%s" specs to which it is linked. Please update the company of the "%s" specs, or leave the company of this workspace empty.', spec.name, spec.name),
                else:
                    lines = [f"- {project.name}" for project in different_company_specs]
                    message = _('This workspace should remain in the same company as the following specs to which it is linked:\n%s\n\nPlease update the company of those specs, or leave the company of this workspace empty.', '\n'.join(lines)),
                raise UserError(message)

    def _copy_and_merge(self, vals=None):
        if not self:
            return self.env['documents.folder']
        if vals is None:
            vals = {}

        if 'name' not in vals:
            vals['name'] = _('Merged Workspace')
        merged_folder = self.create(vals)
        descriptions = []

        for folder in self:
            if folder.description:
                descriptions.append(folder.description)
            for facet in folder.facet_ids:
                facet.copy({'folder_id': merged_folder.id})
            self.env['documents.tag'].flush_model(['folder_id'])

            old_facet_id_to_new_facet_id, old_tag_id_to_new_tag_id = folder._get_old_id_to_new_id_maps(merged_folder)
            folder._copy_workflow_rules_and_actions(merged_folder, old_facet_id_to_new_facet_id, old_tag_id_to_new_tag_id)

            for child_folder in folder.children_folder_ids:
                child_folder.with_context({
                    'ancestors_facet_map': old_facet_id_to_new_facet_id,
                    'ancestors_tag_map': old_tag_id_to_new_tag_id,
                }).copy({'parent_folder_id': merged_folder.id})

        merged_folder.description = '<br/>'.join(descriptions)
        return merged_folder

    def _get_spec_from_closest_ancestor(self):
        """
        If the current folder is linked to exactly one spec, this method returns
        that spec.

        If the current folder doesn't match the criteria, but one of its ancestors
        does, this method will return the spec linked to the closest ancestor
        matching the criteria.

        :return: The spec linked to the closest valid ancestor, or an empty
        recordset if no spec is found.
        """
        self.ensure_one()
        eligible_specs = self.env['specs.sale'].sudo()._read_group(
            [('documents_folder_id', 'parent_of', self.id)],
            ['documents_folder_id'],
            having=[('__count', '=', 1)],
        )
        if not eligible_specs:
            return self.env['specs.sale']

        # dict {folder_id: position}, where position is a value used to sort speccs by their folder_id
        folder_id_order = {int(folder_id): i for i, folder_id in enumerate(reversed(self.parent_path[:-1].split('/')))}
        eligible_specs.sort(key=lambda spec_group: folder_id_order[spec_group[0].id])
        return self.env['specs.sale'].sudo().search([('documents_folder_id', '=', eligible_specs[0][0].id)], limit=1)
