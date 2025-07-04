# -*- coding: utf-8 -*-

from odoo import api, fields, models
from odoo.fields import Command

SPEC_FIELD_NOT_LOAD = [
            'name', 'stage_id', 'state', 'specs_sale_id', 'specs_opportunity_id', 'company_id', 'currency_id', 'salesman_id',
            'uom_id', 'specs_product_type_id', 'specs_type', 'creation_date', 'version', 'unit_id', 'specs_amount_total',
            'specs_mtrs', 'specs_mtrs_uom_name', 'specs_mtrs_uom_convert', 'specs_product_id', 'specs_product_id_domain',
            'specs_color_id_domain', 'specs_anchor_id_domain', 'specs_hinge_id_domain', 'specs_molding_int_id_domain', 'specs_molding_ext_id_domain',
            'specs_moce_id_domain', 'specs_tyarct_id_domain', 'specs_latchsup_id_domain', 'specs_latchin_id_domain',
            'specs_typeguar_id_domain', 'specs_flashing_id_domain', 'specs_board_id_domain', 'specs_forging_id_domain',
            'specs_jac_id_domain', 'specs_design_id', 'specs_suffix_id', 'specs_cost_total', 'specs_type_arc_id_domain',
            'from_duplicate', 'product_uom_qty', 'specs_opportunity_name', 'specs_sp_line_ids', 'specs_line_ids', 'amount_total_manufacturing',
            'sequence_name'
        ]


class DoorFamily(models.Model):
    _name = 'door.family'
    _inherit = 'door.family'

    @api.model
    def _get_default_spec_fields(self):
        return ['specs_total_ant', 'specs_total_alt']

    def load_default_spec_fields(self):
        self.ensure_one()
        command_list = [(Command.CLEAR, 0, 0)]
        fields_to_load_ids = self.env['ir.model.fields'].search([
            ('model', '=', 'specs.sale'), ('name', 'not in', SPEC_FIELD_NOT_LOAD), ('name', 'ilike', 'specs_%')
        ])

        command_list.extend((Command.CREATE, 0, {'field_id': field.id}) for field in fields_to_load_ids)
        return self.write({'door_family_field_line_ids': command_list})

    def duplicate_configuration_spec_fields(self):
        self.ensure_one()
        families_ids = self.env[self._name].search([('id', '!=', self.id)])
        door_family_field_line_ids = self.door_family_field_line_ids

        for family in families_ids:
            command_list = [(Command.CLEAR, 0, 0)]
            command_list.extend((Command.CREATE, 0, line._prepare_values()) for line in door_family_field_line_ids)
            family.write({'door_family_field_line_ids': command_list})


class DoorFamilyFieldLines(models.Model):
    _inherit = 'door.family.field.line'
    _order = 'door_family_id, sequence, id'

    def _domain_spec_fields(self):
        domain = [('model', '=', 'specs.sale'), ('name', 'not in', SPEC_FIELD_NOT_LOAD), ('name', 'ilike', 'specs_%')]
        return domain

    door_family_id = fields.Many2one('door.family', 'Door family', ondelete='cascade')
    field_id = fields.Many2one('ir.model.fields', 'Field',
                               domain=lambda self: self._domain_spec_fields())
    ttype = fields.Selection(related='field_id.ttype', string='Field Type')
    field_name = fields.Char(related='field_id.name', string='Field name')
    max_qty = fields.Integer('Maximum amount')
    required_in_specs = fields.Boolean('Required in Spec')
    editable_in_mrp = fields.Boolean('Editable in Manufactoring')
    product_id = fields.Many2one('product.product', 'Product')
    visible_in_spec_ids = fields.Many2many('door.configuration', 'family_product_visible_spec_rel', 'field_line_id', 'config_id',
                                       string='Editable for Setup', help='Fields visible in the Spec given the Setup, but editable in Manufacturing.')
    invisible_in_spec_ids = fields.Many2many('door.configuration', 'family_product_invisible_spec_rel', 'field_line_id',
                                       'config_id',
                                       string='Invisible in Spec', help='Fields invisible in the Spec given the Setup')
    required_in_spec_ids = fields.Many2many('door.configuration', 'family_product_required_spec_rel', 'field_line_id',
                                             'config_id',
                                             string='Required for Setup',
                                             help='Fields required in the Spec given the Setup')
    sequence = fields.Integer(string="Sequence", default=10)
    display_type = fields.Selection(
        selection=[
            ('line_section', "Section"),
        ],
        default=False)
    name = fields.Char('Description')

    def _prepare_values(self):
        self.ensure_one()
        return {
            'field_id': self.field_id.id,
            'max_qty': self.max_qty,
            'required_in_specs': self.required_in_specs,
            'editable_in_mrp': self.editable_in_mrp,
            'product_id': self.product_id.id or False,
            'visible_in_spec_ids': [(6, 0, self.visible_in_spec_ids.ids)],
            'invisible_in_spec_ids': [(6, 0, self.invisible_in_spec_ids.ids)],
            'required_in_spec_ids': [(6, 0, self.required_in_spec_ids.ids)],
            'cost_price_field': self.cost_price_field,
            'sale_price_field': self.sale_price_field,
            'sequence': self.sequence,
            'display_type': self.display_type,
            'name': self.name,
        }
