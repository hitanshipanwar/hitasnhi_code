# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from collections import OrderedDict

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools import SQL


class Document(models.Model):
    _inherit = 'documents.document'

    specs_id = fields.Many2one('specs.sale', compute='_compute_specs_id', search='_search_specs_id')

    @api.depends('res_id', 'res_model')
    def _compute_specs_id(self):
        for record in self:
            if record.res_model == 'specs.sale':
                record.specs_id = self.env['specs.sale'].browse(record.res_id)
            else:
                record.specs_id = False

    @api.model
    def _search_specs_id(self, operator, value):
        if operator in ('=', '!=') and isinstance(value, bool): # needs to be the first condition as True and False are instances of int
            if not value:
                operator = operator == "=" and "!=" or "="
            comparator = operator == "=" and "|" or "&"
            return [
                ("res_model", operator, "specs.sale"),
            ]
        elif operator in ('=', '!=', "in", "not in") and (isinstance(value, int) or isinstance(value, list)):
            return [
                ("res_model", "=", "specs.sale"), ("res_id", operator, value),
            ]
        elif operator in ("ilike", "not ilike", "=", "!=") and isinstance(value, str):
            query_spec = self.env["specs.sale"]._search([(self.env["specs.sale"]._rec_name, operator, value)])
            spec_select, spec_where_params = query_spec.select()
            # We may need to flush `res_model` `res_id` if we ever get a flow that assigns + search at the same time..
            # We only apply security rules to specs as security rules on documents will be applied prior
            # to this leaf.
            return [
                ("id", "inselect", (f"""
                    WITH helper as (
                        {spec_select}
                    )
                    SELECT document.id
                    FROM documents_document document
                    LEFT JOIN specs_sale spec ON spec.id=document.res_id AND document.res_model = 'specs.sale'
                    WHERE COALESCE(spec.id, NULL ) IN (SELECT id FROM helper)
                """, spec_where_params))
            ]
        else:
            raise ValidationError(_("Invalid specs search"))

    @api.model
    def search_panel_select_range(self, field_name, **kwargs):
        if field_name != 'folder_id' or not self._context.get('limit_folders_to_specs'):
            return super().search_panel_select_range(field_name, **kwargs)

        res_model = self._context.get('active_model')
        if res_model not in ('specs.sale'):
            return super().search_panel_select_range(field_name, **kwargs)

        res_id = self._context.get('active_id')
        fields = ['display_name', 'description', 'parent_folder_id', 'has_write_access']

        active_record = self.env[res_model].browse(res_id)
        if not active_record.exists():
            return super().search_panel_select_range(field_name, **kwargs)
        spec = active_record if res_model == 'specs.sale' else active_record.sudo().specs_id

        document_read_group = self.env['documents.document']._read_group(kwargs.get('search_domain', []), [], ['folder_id:array_agg'])
        folder_ids = document_read_group[0][0]
        records = self.env['documents.folder'].with_context(hierarchical_naming=False).search_read([
            '|',
                ('id', 'child_of', spec.documents_folder_id.id),
                ('id', 'in', folder_ids),
        ], fields)
        available_folder_ids = set(record['id'] for record in records)

        values_range = OrderedDict()
        for record in records:
            record_id = record['id']
            if record['parent_folder_id'] and record['parent_folder_id'][0] not in available_folder_ids:
                record['parent_folder_id'] = False
            value = record['parent_folder_id']
            record['parent_folder_id'] = value and value[0]
            values_range[record_id] = record

        return {
            'parent_field': 'parent_folder_id',
            'values': list(values_range.values()),
        }
