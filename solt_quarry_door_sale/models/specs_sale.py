# -*- coding: utf-8 -*-

import json
import logging
from odoo import models, fields, api, tools, _
from odoo.fields import Command
from odoo.exceptions import ValidationError
from .door_family import SPEC_FIELD_NOT_LOAD

_logger = logging.getLogger(__name__)


def _get_factor_convert_in_to_m(self):
    """ 1in = 0.0254m """
    return 0.0254


def _get_factor_convert_ft2_to_in2(self):
    """ 1ft2 = 144.0in2 """
    return 144.0


class SpecsSale(models.Model):
    _name = 'specs.sale'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Specs sale'
    _check_company_auto = True
    _order = 'version desc, id desc'

    @api.model
    def _read_group_stage_ids(self, stages, domain, order):
        return self.env['specs.type'].search([], order=order)

    def _default_stage_id(self):
        return self.env.ref("solt_quarry_door_sale.stage_in_progress")

    def _get_specs_product_type_domain(self):
        domain = [('product_spec_ok', '=', True)]
        return domain

    @tools.ormcache()
    def _get_default_uom_id(self):
        # Deletion forbidden (at least through unlink)
        return self.env.ref('uom.uom_square_meter')

    def _domain_product_deadbolt_id(self):
        company = self.env.company
        category = self.env.company.specs_deadbolt_categ_id
        domain = [
            '&', ('categ_id', 'child_of', category.ids), ('type', 'in', ['product', 'consu']), '|',
            ('company_id', '=', False), ('company_id', '=', company.id)
        ]
        return domain

    name = fields.Char('Name', tracking=True)
    sequence_name = fields.Char('Spec folio', default=lambda self: _('New'), copy=True, tracking=True)
    stage_id = fields.Many2one('specs.type', string='Stage', group_expand='_read_group_stage_ids',
                               default=_default_stage_id, tracking=True, copy=False)
    state = fields.Char('Stage code', related='stage_id.code', store=True)
    specs_sale_id = fields.Many2one('sale.order', string='Order No.', copy=True, company_dependent=True, store=True)
    # Order-related fields
    specs_opportunity_id = fields.Many2one('crm.lead', string='Opportunity',
                                           copy=True, store=True, company_dependent=True)
    specs_opportunity_name = fields.Char(string='Opportunity', tracking=True, copy=True, store=True, required=False)
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company,
        store=True, index=True, company_dependent=True)
    currency_id = fields.Many2one('res.currency',
        store=True, company_dependent=True)
    salesman_id = fields.Many2one('res.users',
        string="Salesperson",
        store=True, company_dependent=True)

    specs_product_type_id = fields.Many2one('product.template', 'Product type', tracking=True, copy=True,
                                            domain="[('product_spec_ok', '=', True)]")
    uom_id = fields.Many2one(
        'uom.uom', 'Unit of Measure',
        default=_get_default_uom_id, required=True,
        domain=lambda self: [('id', 'in', [self.env.ref('uom.uom_square_meter').id, self.env.ref('uom.uom_square_foot').id])])
    specs_type = fields.Selection(related='specs_product_type_id.classification_type', string="Classification Type")
    creation_date = fields.Date('Creation date', default=lambda self: fields.Date.context_today(self), copy=False)
    create_uid = fields.Many2one('res.users', 'Saved by', index=True, readonly=True, default=lambda self: self.env.user)
    version = fields.Integer('Version', default=0, copy=False, tracking=True)
    unit_id = fields.Char('Unit id', copy=True, tracking=True)
    specs_amount_total = fields.Float(string='Total Price', digits='Product Unit of Measure', store=True,
                                      copy=True, tracking=True, compute="_compute_specs_amount_total")
    specs_cost_total = fields.Float(string='Total Cost', digits='Product Unit of Measure', store=True,
                                      copy=True, tracking=True, compute="_compute_specs_cost_total")
    amount_total_manufacturing = fields.Float(string='Total Price manufacturing', digits='Product Unit of Measure', copy=True, readonly=True)

    # HEADER FIELDS
    specs_product_id = fields.Many2one('door.family', 'Product Family', tracking=True)
    specs_design_id = fields.Many2one('door.design', string='Design')
    specs_suffix_id = fields.Many2one('door.suffix', string='Suffix')
    specs_color_id = fields.Many2one('product.attribute.value', string='Color')
    specs_mtrs = fields.Float(string='Square meters', compute='_compute_specs_mtrs', digits='Specs Measures', tracking=True)
    specs_mtrs_uom_name = fields.Char('UoM name', compute='_compute_specs_mtrs')
    specs_mtrs_uom_convert = fields.Float('Square feet', compute='_compute_specs_mtrs', digits='Specs Measures')
    specs_dc_id = fields.Many2one('door.configuration', string='Setup')

    # GENERALS FIELDS
    specs_handing_id = fields.Many2one('door.handing', string='Handing')
    specs_forging_id = fields.Many2one('product.attribute.value', string='WroughtIron')  # Forja
    specs_type_arc_id = fields.Many2one('product.attribute.value', string='Arch Type')  # Tipo de Arco
    specs_fixed_glass = fields.Selection([('yes', 'Yes'), ('No', 'No')], string='Fixed Glass')
    specs_type_glass_id = fields.Many2one('door.type.glass', string='Door Glass Type', domain="[('type', '=', 'door')]")
    specs_total_ant = fields.Float(string='Total Width', digits='Specs Measures', copy=True)  # Ancho total
    specs_total_alt = fields.Float(string='Total Height', digits='Specs Measures', copy=True)  # Altura total
    specs_antmarc = fields.Float(string='Door Width', digits='Specs Measures',
                                 copy=True)  # Ancho puerta con marco
    specs_altmarc = fields.Float(string='Door Height', digits='Specs Measures',
                                 copy=True)  # Altura puerta con marco
    specs_bast = fields.Float(string='Stile Width', digits='Specs Measures', copy=True)  # Ancho de Bastidor
    specs_porfbast = fields.Float(string='Stile Depth', digits='Specs Measures', copy=True)  # Profundidad de Bastidor
    specs_antleaft = fields.Float(string='Leaf Width', digits='Specs Measures', copy=True)  # Ancho de la Hoja
    specs_altleaft = fields.Float(string='Leaf Height', digits='Specs Measures', copy=True)  # Altura de hoja
    specs_altboard = fields.Float(string='Bottom Panel Height', digits='Specs Measures', copy=True)  # Altura tablero
    specs_altarc = fields.Float(string='Arch Raise', digits='Specs Measures', copy=True)  # Altura de Arco
    specs_tolsup = fields.Float(string='Tolerance Top', digits='Specs Measures',
                                copy=True)  # Tolerancia Superior (hoja y marco sup)
    specs_tolcen = fields.Float(string='Tolerance Central', digits='Specs Measures',
                                copy=True)  # Tolerancia Central (entre hoja y hoja)
    specs_tollat = fields.Float(string='Tolerance Sides',
                                digits='Specs Measures',
                                copy=True)  # Tolerancia de los Lados (entre hoja y marco izq y der)
    specs_board_id = fields.Many2one('product.attribute.value', string='Bottom Panel')  # Tablero
    specs_operable = fields.Selection([('yes', 'Yes'), ('No', 'No')], string='Operable')  # Operable
    specs_huacal = fields.Selection([('yes', 'Yes'), ('No', 'No')], string='Crate')  # Huacal

    # FRAME FIELDS
    specs_anchor_id = fields.Many2one('product.attribute.value', string='Anchors')
    specs_hinges_id = fields.Many2one('product.attribute.value', string='Hinges')
    specs_molding_int_id = fields.Many2one('product.attribute.value', string='FrameBrickmoldInt')  # Moldura Interna
    specs_molding_ext_id = fields.Many2one('product.attribute.value', string='FrameBrickmoldExt')  # Moldura Externa
    specs_traslape_int_id = fields.Many2one('door.traslape', string='FrameOverlapInt', domain=[('type', '=', 'internal')])  # Traslape Interna
    specs_traslape_ext_id = fields.Many2one('door.traslape', string='FrameOverlapExt', domain=[('type', '=', 'external')])  # Traslape Externa
    specs_ancmarc = fields.Float(string='Frame Width', digits='Specs Measures', copy=True)  # Ancho de Marco
    specs_profmarc = fields.Float(string='Frame Depth', digits='Specs Measures',
                                  copy=True)  # Profundidad de Marco
    specs_amount_hinges = fields.Integer(string='Hinge Quantity', copy=True, help="Number of Hinges")  # Cantidad de Bisagras

    # PULL HANDLES FIELDS
    specs_jac_id = fields.Many2one('product.attribute.value', string='PH Act-Ext')  # Jaladera Activa Exterior
    specs_jacin_id = fields.Many2one('product.attribute.value', string='PH Act-Int')  # Jaladera Activa Interior
    specs_jin_id = fields.Many2one('product.attribute.value', string='PH Inac-Ext')  # Jaladera Inactiva Exterior
    specs_jinin_id = fields.Many2one('product.attribute.value', string='PH Inac-Int')  # Jaladera Inactiva Interior

    # DEADBOLT FIELDS
    specs_moce_id = fields.Many2one('product.product', string='Deadbolt Type', domain=lambda self: self._domain_product_deadbolt_id())  # modelo de cerradura
    specs_pch_id = fields.Many2one('door.metal', string='Preparation')  # Preparación de Chapa
    specs_altce = fields.Float(string='Deadbolt Height', digits='Specs Measures', copy=True)  # Altura de Cerradura
    specs_mbas = fields.Float(string='Rail Top Width',
                              digits='Specs Measures', copy=True)  # Medidas Bastidor Superior
    specs_mbai = fields.Float(string='Rail Bottom Width', digits='Specs Measures', copy=True)  # Medidas Bastidor Interior
    specs_rlat = fields.Integer(string='Roller Latches', copy=True)  # Cerraduras con rodillo
    specs_bac = fields.Integer(string='Ball Catches', copy=True)  # Cerradura de bola

    # TRANSFORM FIELDS
    specs_tyarct_id = fields.Many2one('product.attribute.value', string='Arch Type in Transom')  # Tipo de Arco en Transom
    specs_taltarc = fields.Float(string='Transom Arch Raise', digits='Specs Measures', copy=True)  # Altura del Arco de Transom
    specs_antra = fields.Float(string='Transom Width', digits='Specs Measures', copy=True)  # Ancho de Transom
    specs_altra = fields.Float(string='Transom Height',
                               digits='Product Unit of Measure', copy=True)  # Altura de Transom
    specs_ddm = fields.Selection(
        [('yes', 'Yes'),
         ('no', 'No')], string='Transom Double Frame')
    specs_typet_glass_id = fields.Many2one('door.type.glass', string='Transom Glass Type', domain="[('type', '=', 'transom')]")  # Tipo de vidrio para transom

    # SIDELIGHT FIELDS
    specs_board_type_id = fields.Many2one('door.board.type', string='Sidelight Bottom Panel Type')  # Tipo de Tablero de Fijos
    specs_posfi_id = fields.Many2one('door.position', string=' Sidelight Position')  # Posición del Fijo
    specs_anfi = fields.Float(string='Sidelight Width', digits='Specs Measures', copy=True)  # Ancho de Fijos
    specs_alfi = fields.Float(string='Sidelight Height', digits='Specs Measures', copy=True)  # Altura de Fijos

    specs_saltboard_type = fields.Float(string='Sidelight Bottom Panel Height', digits='Specs Measures', copy=True)  # Altura de Tablero de Fijos
    specs_sidelight_glassf = fields.Selection([('yes', 'Yes'), ('No', 'No')], string='Sidelight Glass Fixed',)  # Vidrio Fijo en Fijos
    specs_ddmf = fields.Selection([('yes', 'Yes'), ('no', 'No')], string='Sidelight Double Frame',)  # Doble Marco de Fijos
    specs_typef_glass_id = fields.Many2one('door.type.glass', string='Sidelight Glass Type', domain="[('type', '=', 'sidelight')]")  # Tipo de vidrio para fijos

    # LATCH FIELDS
    specs_latchsup_id = fields.Many2one('product.attribute.value', string='Upper latch',)  # Picaporte Superior
    specs_latchin_id = fields.Many2one('product.attribute.value', string='Lower latch')  # Picaporte Inferior
    specs_typeguar_id = fields.Many2one('product.attribute.value', string='Threshold Type')  # Tipo de Guardapolvo
    specs_flashing_id = fields.Many2one('product.attribute.value', string='Flashing/Sill Pan',)  # Tipo de Flashing
    specs_assembly_id = fields.Many2one('door.assembly', string='Assembly Preparation')  # Preparación de Ensamble
    specs_cls = fields.Integer(string='Qty Upper latch')  # Cantidad Picaporte Superior
    specs_cli = fields.Integer(string='Qty Lower latch')  # Cantidad Picaporte Inferior
    specs_tolerance = fields.Float(string='Threshold tolerance', digits='Specs Measures')  # Tolerancia Guardapolvo

    # GLASS
    specs_glass_line_ids = fields.One2many('door.glass.specs', 'specs_id', string='Glass Specifications')
    description = fields.Text(string='Comments', copy=True)

    specs_line_ids = fields.One2many('door.accessories', 'specs_id', string='Accesory Type')  # Accesorios
    specs_sp_line_ids = fields.One2many('door.special.preparations', 'specs_id', string='Special preparations ')  # Preparaciones Especiales
    specs_hardware_line_ids = fields.One2many('door.hardware', 'specs_id', string='Hardware Type')  # Hardware

    # DOMAIN FIELDS
    specs_product_id_domain = fields.Char(compute='_compute_specs_domain')
    specs_color_id_domain = fields.Char(compute='_compute_specs_domain')
    specs_anchor_id_domain = fields.Char(compute='_compute_specs_domain')
    specs_hinge_id_domain = fields.Char(compute='_compute_specs_domain')
    specs_molding_int_id_domain = fields.Char(compute='_compute_specs_domain')
    specs_molding_ext_id_domain = fields.Char(compute='_compute_specs_domain')
    specs_moce_id_domain = fields.Char(compute='_compute_specs_domain')
    specs_tyarct_id_domain = fields.Char(compute='_compute_specs_domain')
    specs_latchsup_id_domain = fields.Char(compute='_compute_specs_domain')
    specs_latchin_id_domain = fields.Char(compute='_compute_specs_domain')
    specs_typeguar_id_domain = fields.Char(compute='_compute_specs_domain')
    specs_flashing_id_domain = fields.Char(compute='_compute_specs_domain')
    specs_board_id_domain = fields.Char(compute='_compute_specs_domain')
    specs_forging_id_domain = fields.Char(compute='_compute_specs_domain')
    specs_jac_id_domain = fields.Char(compute='_compute_specs_domain')
    specs_type_arc_id_domain = fields.Char(compute='_compute_specs_domain')

    block_changes = fields.Boolean(string='Registro Bloqueado', compute="_compute_block_changes",
                                   help="Technical field to indicate whether the specs is editable or not")
    field_ui_modifications = fields.Char(compute="_compute_field_visibility")
    field_ui_invisible = fields.Char(compute="_compute_field_visibility")
    field_ui_readonly = fields.Char(compute="_compute_field_visibility")
    message_warning = fields.Text(compute="_compute_message_warning")
    can_edit_spec_in_manufacturing = fields.Boolean(compute="_compute_can_edit_spec_in_manufacturing")
    from_duplicate = fields.Boolean(copy=False)
    product_uom_qty = fields.Float(string="Quantity of products", help="Quantity of products in the sales order line",
        digits='Product Unit of Measure', default=1.0, required=True)
    can_show_button_update_cost = fields.Boolean(help="Can show update cost")
    can_show_sale_field = fields.Boolean(compute="_compute_can_edit_spec_in_manufacturing", help="Can show sales fields")
    confirmed_spec = fields.Boolean(copy=False)

    @api.depends('specs_product_type_id')
    def _compute_specs_domain(self):
        for record in self:
            record = record.with_company(record.company_id)
            record.onchange_specs_product_type_id()

            family_ids = record._get_attribute_ids('family').mapped('value_ids.family_product_id')
            color_ids = record._get_attribute_ids('color').mapped('value_ids')
            anchor_ids = record._get_attribute_ids('anchor').mapped('value_ids')
            hinge_ids = record._get_attribute_ids('hinge').mapped('value_ids')
            molding_int_ids = record._get_attribute_ids('molding').mapped('value_ids')
            molding_ext_ids = record._get_attribute_ids('molding').mapped('value_ids')
            pch_ids = record._get_attribute_ids('deadbolt').mapped('value_ids')
            tyarct_ids = record._get_attribute_ids('arc').mapped('value_ids')
            latchsup_ids = record._get_attribute_ids('latch').mapped('value_ids')
            latchin_ids = record._get_attribute_ids('latch').mapped('value_ids')
            typeguar_ids = record._get_attribute_ids('dust_guard').mapped('value_ids')
            flashing_ids = record._get_attribute_ids('flashing').mapped('value_ids')
            board_ids = record._get_attribute_ids('panel').mapped('value_ids')
            forging_ids = record._get_attribute_ids('forge').mapped('value_ids')
            jac_ids = record._get_attribute_ids('handle').mapped('value_ids')
            specs_type_arc_ids = record._get_attribute_ids('arc').mapped('value_ids')

            record.specs_product_id_domain = json.dumps([('id', 'in', family_ids.ids)])
            record.specs_color_id_domain = json.dumps([('id', 'in', color_ids.ids)])
            record.specs_anchor_id_domain = json.dumps([('id', 'in', anchor_ids.ids)])
            record.specs_hinge_id_domain = json.dumps([('id', 'in', hinge_ids.ids)])
            record.specs_molding_int_id_domain = json.dumps([('id', 'in', molding_int_ids.ids)])
            record.specs_molding_ext_id_domain = json.dumps([('id', 'in', molding_ext_ids.ids)])
            record.specs_moce_id_domain = json.dumps([('id', 'in', pch_ids.ids)])
            record.specs_tyarct_id_domain = json.dumps([('id', 'in', tyarct_ids.ids)])
            record.specs_latchsup_id_domain = json.dumps([('id', 'in', latchsup_ids.ids)])
            record.specs_latchin_id_domain = json.dumps([('id', 'in', latchin_ids.ids)])
            record.specs_typeguar_id_domain = json.dumps([('id', 'in', typeguar_ids.ids)])
            record.specs_flashing_id_domain = json.dumps([('id', 'in', flashing_ids.ids)])
            record.specs_board_id_domain = json.dumps([('id', 'in', board_ids.ids)])
            record.specs_forging_id_domain = json.dumps([('id', 'in', forging_ids.ids)])
            record.specs_jac_id_domain = json.dumps([('id', 'in', jac_ids.ids)])
            record.specs_type_arc_id_domain = json.dumps([('id', 'in', specs_type_arc_ids.ids)])

    @api.depends('specs_total_ant', 'specs_total_alt', 'uom_id')
    def _compute_specs_mtrs(self):
        uom_square_foot = self.env.ref('uom.uom_square_foot')
        for record in self:
            record = record.with_company(record.company_id)
            record.specs_mtrs_uom_convert = (record.specs_total_ant * record.specs_total_alt) / _get_factor_convert_ft2_to_in2(record)  # feet
            record.specs_mtrs_uom_name = uom_square_foot.name

            factor_m = _get_factor_convert_in_to_m(record)
            specs_ant_converted = record.specs_total_ant * factor_m
            specs_alt_converted = record.specs_total_alt * factor_m
            record.specs_mtrs = specs_ant_converted * specs_alt_converted

    @api.depends(lambda self: (
            'specs_mtrs_uom_convert',
             'specs_mtrs',
             'specs_product_type_id',
             'specs_dc_id',
             'specs_product_id',
             'specs_product_id.door_family_field_line_ids',
             *self._get_sale_price_field()
    ))
    def _compute_specs_amount_total(self):
        for record in self:
            record = record.with_company(record.company_id)
            if record.company_id == self.env.company.specs_sale_company_id:
                # calculo por el precio configurado en la familia del producto
                uom_square_foot = self.env.ref('uom.uom_square_foot')

                sale_price_field_names = record._get_sale_price_field(door_family_id=record.specs_product_id.id)
                sale_dict = record._get_cost_fields_dict(sale_price_field_names)

                # get family product price
                family_product_id = record._get_family_product()
                pricelist = record.specs_product_id.pricelist_ids.filtered(lambda p: p.id == record.specs_sale_id.pricelist_id.id)
                price = family_product_id.list_price
                if pricelist and family_product_id:
                    price = pricelist._get_product_price(family_product_id, quantity=record.specs_mtrs_uom_convert, currency=record.currency_id, uom=uom_square_foot)

                # compute sale price
                sale_price = sum(sale_dict.values())

                record.specs_amount_total = record.specs_mtrs_uom_convert * price + sale_price
            else:
                record.specs_amount_total = record.amount_total_manufacturing

    @api.depends(lambda self: (
            'specs_mtrs_uom_convert',
             'specs_mtrs',
             'specs_product_type_id',
             'specs_dc_id',
             'specs_product_id',
             'specs_product_id.door_family_field_line_ids',
             *self._get_fields_cost_specs()
    ))
    def _compute_specs_cost_total(self):
        for record in self:
            record = record.with_company(record.company_id)
            cost_price_field_names = record._get_fields_cost_specs(door_family_id=record.specs_product_id.id)
            cost_dict = record._get_cost_fields_dict(cost_price_field_names, cost=True)

            # get cost family product
            family_product_id = record._get_family_product(cost=True)
            family_product_cost = 1 if not family_product_id else family_product_id.standard_price

            # compute cost
            cost = sum(cost_dict.values())
            record.specs_cost_total = record.specs_mtrs_uom_convert * family_product_cost + cost

    def _get_cost_fields_dict(self, field_names, cost=False):
        self.ensure_one()
        cost_dict = dict.fromkeys(field_names, 0)
        setup_attribute_id = self.specs_dc_id.product_attribute_id.value_ids.filtered(
                lambda v: v.config_id == self.specs_dc_id)
        pricelist = self.specs_sale_id.pricelist_id
        for name, value in cost_dict.items():
            # trim
            if name in ['specs_molding_int_id', 'specs_molding_ext_id']:
                fvalue = self[name]
                if fvalue and self.specs_type_arc_id:
                    cost_dict[name] = self.get_field_cost(fvalue, pricelist, second_attribute_value=self.specs_type_arc_id, cost=cost)
            # pull
            if name in ['specs_jac_id', 'specs_jacin_id', 'specs_jin_id', 'specs_jinin_id']:
                fvalue = self[name]
                if fvalue:
                    cost_dict[name] = self.get_field_cost(fvalue, pricelist, cost=cost)
            # Threshold
            if name in ['specs_typeguar_id']:
                fvalue = self[name]
                if fvalue:
                    cost_dict[name] = self.get_field_cost(fvalue, pricelist, second_attribute_value=setup_attribute_id, cost=cost)
            # Flashing
            if name in ['specs_flashing_id']:
                fvalue = self[name]
                if fvalue:
                    cost_dict[name] = self.get_field_cost(fvalue, pricelist, second_attribute_value=setup_attribute_id, cost=cost)
            # Deadbolt
            if name in ['specs_moce_id']:
                fvalue = self[name]
                if fvalue and not cost:
                    cost_dict[name] = pricelist._get_product_price(fvalue, quantity=1, currency=self.currency_id)

            # Glasses
            if name in ['specs_glass_line_ids']:
                fvalue = self[name]
                if fvalue:
                    cost_dict[name] = sum(
                            [line.glass_qty * self.get_field_cost(line.glass_type_id, pricelist, cost=cost) for line in fvalue])
            # Hardwares
            if name in ['specs_hardware_line_ids']:
                fvalue = self[name]
                if fvalue:
                    # sale
                    if not cost:
                        values = []
                        items = fvalue.filtered(lambda i: i.include_in_spec_price)
                        price = 1.0
                        for item in items:
                            if item.hardware_id:
                                pricelist = item.hardware_id.pricelist_ids.filtered(
                                    lambda p: p.id == self.specs_sale_id.pricelist_id.id)
                                price = pricelist._get_product_price(item.hardware_id.product_id,
                                                                     quantity=item.amount,
                                                                     currency=self.currency_id)
                            sale_price = item.amount * price
                            values.append(sale_price)
                        cost_dict[name] = sum(values)
                    else:
                        cost_dict[name] = sum(
                            [line.amount * line.hardware_id.product_id.standard_price for line in fvalue])

        return cost_dict

    def get_field_cost(self, fvalue, pricelist, second_attribute_value=None, cost=False):
        self.ensure_one()
        company_id = self._get_company(cost=cost)
        if second_attribute_value:
            attribute_id = second_attribute_value.attribute_id
            attribute_id1 = fvalue.attribute_id
            product = self.env['product.product'].sudo().with_company(company_id).search([
                ('product_template_variant_value_ids.attribute_id', '=', attribute_id1.id),
                ('product_template_variant_value_ids.product_attribute_value_id', '=', fvalue.id),
                ('company_id', '=', company_id.id),
            ])
            product = product.filtered(lambda p: attribute_id.id in p.product_template_variant_value_ids.attribute_id.ids and second_attribute_value.id in p.product_template_variant_value_ids.product_attribute_value_id.ids)
        else:
            domain = [
                ('product_template_variant_value_ids.attribute_id', '=', fvalue.attribute_id.id),
                ('product_template_variant_value_ids.product_attribute_value_id', '=', fvalue.id),
                ('company_id', '=', company_id.id),
            ]
            product = self.env['product.product'].sudo().with_company(company_id).search(domain)

        if not cost:  # sale
            price = 0
            if product:
                price = pricelist._get_product_price(product, quantity=1, currency=self.currency_id)
            return price if price > 0 else product.lst_price
        else:
            return product.standard_price

    def _get_family_product(self, cost=False):
        self.ensure_one()
        company_id = self._get_company(cost=cost)
        family_attribute_value_id = self.specs_product_id.product_attribute_id.value_ids.filtered(
            lambda v: v.family_product_id == self.specs_product_id)
        family_product_id = self.env['product.product'].sudo().with_company(company_id).search([
            ('product_template_variant_value_ids.attribute_id', '=', family_attribute_value_id.attribute_id.id),
            ('product_template_variant_value_ids.product_attribute_value_id', '=', family_attribute_value_id.id),
            ('company_id', '=', company_id.id),
        ])
        if cost:
            setup_attribute_id = self.specs_dc_id.product_attribute_id.value_ids.filtered(
                lambda v: v.config_id == self.specs_dc_id)
            attribute_id = setup_attribute_id.attribute_id
            family_product_id = family_product_id.filtered(lambda
                                           p: attribute_id.id in p.product_template_variant_value_ids.attribute_id.ids and setup_attribute_id.id in p.product_template_variant_value_ids.product_attribute_value_id.ids)
        return family_product_id

    @api.depends(
        'specs_product_id',
        'specs_dc_id',
        'specs_product_id.door_family_field_line_ids',
        'specs_product_id.door_family_field_line_ids.required_in_specs',
        'specs_product_id.door_family_field_line_ids.editable_in_mrp',
        'specs_product_id.door_family_field_line_ids.visible_in_spec_ids',
        'specs_product_id.door_family_field_line_ids.invisible_in_spec_ids',
        'specs_product_id.door_family_field_line_ids.required_in_spec_ids',
        'can_edit_spec_in_manufacturing'
    )
    def _compute_field_visibility(self):
        for record in self:
            record = record.with_company(record.company_id)
            # reset if change the product family
            if record.id and (record._origin.specs_product_id != record.specs_product_id or record._origin.specs_dc_id != record.specs_dc_id):
                record._reset_specs_fields()

            record.field_ui_modifications = ''
            record.field_ui_invisible = ''
            record.field_ui_readonly = ''
            door_family_field_line_ids = record.specs_product_id.door_family_field_line_ids
            if door_family_field_line_ids:
                setup = record.specs_dc_id
                # fields configured in product family
                required_field_names = door_family_field_line_ids.filtered(lambda l: l.required_in_specs and setup.id in l.required_in_spec_ids.ids).mapped('field_name')
                readonly_field_names = door_family_field_line_ids.filtered(lambda l: l.editable_in_mrp and setup.id in l.visible_in_spec_ids.ids).mapped('field_name')
                invisible_field_names = door_family_field_line_ids.filtered(lambda l: len(l.invisible_in_spec_ids) > 0 and setup.id in l.invisible_in_spec_ids.ids).mapped('field_name')

                # mark required
                record.field_ui_modifications = json.dumps(','.join(required_field_names).split(','))
                # mark invisible
                record.field_ui_invisible = json.dumps(','.join(invisible_field_names).split(','))
                # mark readonly
                record.field_ui_readonly = json.dumps(','.join(readonly_field_names).split(','))

    @api.depends('state')
    def _compute_block_changes(self):
        for record in self:
            record = record.with_company(record.company_id)
            if record.state in record._get_state_list():
                record.block_changes = True
            else:
                record.block_changes = False

    @api.depends_context('uid', 'company_id')
    @api.depends(
        'specs_product_id',
        'specs_dc_id',
        'specs_product_id.door_family_field_line_ids',
        'specs_product_id.door_family_field_line_ids.visible_in_spec_ids',
        'specs_product_id.door_family_field_line_ids.editable_in_mrp'
    )
    def _compute_can_edit_spec_in_manufacturing(self):
        for record in self:
            record = record.with_company(record.company_id)
            try:
                company_id = record._get_company()
            except ValidationError as e:
                company_id = False
            record.can_edit_spec_in_manufacturing = bool(self.user_has_groups('solt_quarry_door_sale.group_quarry_modify_spec_manufacturing'))
            record.can_show_sale_field = bool(company_id == self.env.company)

    @api.depends('specs_sale_id', 'specs_opportunity_name')
    def _compute_message_warning(self):
        for record in self:
            record = record.with_company(record.company_id)
            record.message_warning = ""
            if not record.specs_sale_id.opportunity_id and not record.specs_opportunity_name:
                record.message_warning = _("The order {} do not have a opportunity.".format(record.specs_sale_id.name))

    @api.constrains(lambda self: self._get_specs_fields())
    def check_valid_specs_product_id(self):
        for record in self:
            errors = []
            door_family_field_line_ids = record.specs_product_id.door_family_field_line_ids
            setup = record.specs_dc_id
            fields = record._fields

            required_numeric_fields = door_family_field_line_ids.filtered(lambda l: l.ttype in ['integer', 'float'] and l.required_in_specs and setup.id in l.required_in_spec_ids.ids).mapped(lambda f: (f.field_name, f.max_qty))
            nrequired_numeric_fields = door_family_field_line_ids.filtered(lambda l: l.ttype in ['integer'] and not l.required_in_specs and setup.id not in l.invisible_in_spec_ids.ids).mapped(lambda f: (f.field_name, f.max_qty))

            for numericf, max_qty in required_numeric_fields:
                if int(record[numericf]) == 0:
                     errors.append(_(f"Field {fields[numericf].string} is required and its value is 0."))
                elif record[numericf] > max_qty and fields[numericf].type == 'integer':
                    errors.append(_(f"The value of field {fields[numericf].string} is greater than the maximum allowed amount {max_qty}."))
            for nnumericf, max_qty in nrequired_numeric_fields:
                if record[nnumericf] > max_qty and fields[nnumericf].type == 'integer':
                    errors.append(_(f"The value of field {fields[nnumericf].string} is greater than the maximum allowed amount {max_qty}."))
            if errors:
                raise ValidationError('\n'.join(errors))

    ### ONCHANGE ###
    @api.onchange('specs_sale_id')
    def onchange_specs_sale_id(self):
        if self.specs_sale_id and not self.specs_opportunity_name:
            self.specs_opportunity_name = self.specs_opportunity_id.name if self.specs_opportunity_id else ''

    def onchange_specs_product_type_id(self):
        if self.specs_product_type_id and self.specs_product_type_id.default_code:
            setup_id = self.env['door.configuration'].search([('name', '=', self.specs_product_type_id.default_code)])
            self.specs_dc_id = setup_id

    @api.model
    def _get_no_reset_fields(self):
        return SPEC_FIELD_NOT_LOAD + ['specs_dc_id', 'specs_color_id']

    @api.model
    def _get_specs_fields(self):
        return [fname for fname, field_data in self.fields_get(attributes={'name'}).items() if
                           fname.startswith('specs_')]

    @api.model
    def _get_fields_cost_specs(self, door_family_id=None):
        """
        Obtener los campos marcados para el calculo del costo del Specs
        :return: list
        """
        domain = [('cost_price_field', '=', True), ('display_type', '=', False)]
        if door_family_id:
            domain.append(('door_family_id', '=', door_family_id))

        field_names = self.env['door.family.field.line'].search(domain).mapped('field_name')
        return list(set(field_names))

    @api.model
    def _get_sale_price_field(self, door_family_id=None):
        """
        Obtener los campos marcados para el calculo del precio de venta del Specs
        :return: list
        """
        domain = [('sale_price_field', '=', True), ('display_type', '=', False)]
        if door_family_id:
            domain.append(('door_family_id', '=', door_family_id))

        field_names = self.env['door.family.field.line'].search(domain).mapped('field_name')
        return list(set(field_names))

    @api.model_create_multi
    def create(self, vals_list):
        company_id = self.env.company.specs_sale_company_id
        for vals in vals_list:
            if 'company_id' in vals:
                self = self.with_company(vals['company_id'])

                if vals['company_id'] == company_id.id and vals.get('sequence_name', _("New")) == _("New") and 'from_duplicate' not in vals:
                    team_id = vals.get('specs_sale_id') and self.env['sale.order'].browse(vals.get('specs_sale_id')).team_id
                    if not team_id.spec_team_sequence_id:
                        raise ValidationError(_(f"The team {team_id.name} do not have a sequence for the Spec."))
                    code = f"{team_id._name}.{team_id.code.lower()}.{self._name}"
                    vals['sequence_name'] = self.env['ir.sequence'].next_by_code(code) or _("New")
        records = super().create(vals_list)
        records = records.sorted(key=lambda r: r.id, reverse=False)
        # give version to the records
        for record in records:
            if not self._context.get('not_update_specs_version', False):
                record.name = record._sync_specs()
                if record.from_duplicate:
                    specs = self.env['specs.sale'].search([
                        ('specs_sale_id', '=', record.specs_sale_id.id),
                        ('specs_product_type_id', '=', record.specs_product_type_id.id),
                    ])
                    version = specs.mapped('version')
                    record.version = max(version, default=0) + 1
                    to_cancel_specs = specs - record
                    for cancel_specs in to_cancel_specs:
                        cancel_specs.action_state_cancel()
                else:
                    record.version = 1
        return records

    def write(self, values):
        FIELS_SPECS_NAME = ['specs_sale_id', 'specs_opportunity_name', 'version', 'product_uom_qty', 'specs_dc_id', 'unit_id', 'specs_product_type_id']
        res = super(SpecsSale, self).write(values)
        for record in self:
            if any(field in values for field in FIELS_SPECS_NAME):
                record.name = record._sync_specs()

            # can show update_cost button
            if record.can_edit_spec_in_manufacturing and 'specs_cost_total' in values or 'specs_glass_line_ids' in values:
                record.can_show_button_update_cost = True
        return res

    def _sync_specs(self):
        self.ensure_one()
        name = _(
            "%(folio)s/V%(version)s/%(product_qty)s/%(opportunity_name)s/%(setup_name)s/%(unit_id)s",
            folio=self.sequence_name,
            version=self.version,
            product_qty=int(self.product_uom_qty),
            opportunity_name=self.specs_opportunity_name,
            setup_name=self.specs_dc_id.name,
            unit_id=self.unit_id)
        return name

    def action_save_total_specs(self):
        self.ensure_one()
        for rec in self:
            command_list = []
            values = rec._prepare_order_line_values(self.specs_product_type_id)
            command_list.append((Command.CREATE, 0, values))
            if rec.specs_hardware_line_ids:
               for hardware in rec.specs_hardware_line_ids.filtered(lambda h: not h.include_in_spec_price):
                   product_id = hardware.hardware_id.product_id
                   pricelist = hardware.hardware_id.pricelist_ids.filtered(
                       lambda p: p.id == rec.specs_sale_id.pricelist_id.id)
                   price = pricelist._get_product_price(product_id,
                                                        quantity=hardware.amount,
                                                        currency=rec.currency_id)
                   if not price:
                       price = product_id.lst_price
                   sale_price = hardware.amount * price
                   values = rec._prepare_order_line_values(product_id, qty=hardware.amount, price=sale_price)
                   command_list.append((Command.CREATE, 0, values))

            rec.specs_sale_id.write({'order_line': command_list})
            rec.confirmed_spec = True
            rec.amount_total_manufacturing = rec.specs_amount_total

    def action_state_cancel(self):
        for record in self:
            line_to_delete_id = record.specs_sale_id.order_line.filtered(lambda l: l.sale_specs_id == record)
            if line_to_delete_id and line_to_delete_id.state != 'sale':
                record.specs_sale_id.write({'order_line': [(Command.DELETE, line_to_delete_id.id, 0)]})
            record.stage_id = self.env.ref("solt_quarry_door_sale.stage_cancel", raise_if_not_found=False)
            record.confirmed_spec = False

    def action_state_return(self):
        stage_cancel = self.env.ref("solt_quarry_door_sale.stage_cancel", raise_if_not_found=False)
        for rec in self:
            rec.stage_id = self.env.ref("solt_quarry_door_sale.stage_in_progress", raise_if_not_found=False)
            specs = self.env['specs.sale'].search([
                ('specs_sale_id', '=', rec.specs_sale_id.id),
                ('specs_product_type_id', '=', rec.specs_product_type_id.id),
                ('stage_id', '!=', stage_cancel.id),
                ('id', '!=', rec.id)
            ])
            if specs:
                specs.action_state_cancel()

    def _prepare_order_line_values(self, product, qty=None, price=None):
        self.ensure_one()
        if product._name == 'product.template':
            product_id = self.env['product.product'].search([('product_tmpl_id', '=', self.specs_product_type_id.id),
                                                         ('name', '=', self.specs_product_type_id.name)])
            product_tmpl_id = product
        elif product._name == 'product.product':
            product_id = product
            product_tmpl_id = product.product_tmpl_id
        product_uom_qty = qty
        if product_uom_qty is None:
            product_uom_qty = self.product_uom_qty
        price_unit = price
        if price_unit is None:
            price_unit = self.specs_amount_total
        return {
                # 'order_id': self.specs_sale_id.id,
                'product_id': product_id and product_id[0].id,
                'product_template_id': product_tmpl_id.id,
                'price_unit': price_unit,
                'name': self.name,
                'product_uom': product_tmpl_id._get_default_uom_id().id,
                'customer_lead': 1.00,
                'sale_specs_id': self.id,
                'sale_specs_name': self.name,
                'product_uom_qty': product_uom_qty
            }

    def copy_data(self, default=None):
        if default is None:
            default = {}
        if 'specs_hardware_line_ids' not in default:
            default['specs_hardware_line_ids'] = [
                Command.create(line.copy_data()[0])
                for line in self.specs_hardware_line_ids
            ]
        if 'from_duplicate' not in default:
            default['from_duplicate'] = True
        if 'company_id' not in default:
            default['company_id'] = self.env.company.id
        default['confirmed_spec'] = False
        return super(SpecsSale, self).copy_data(default)

    def _get_state_list(self):
        return ['price', 'sale_confirm', 'cancel']

    def _get_attribute_line(self, attribute_line_ids, type):
        self.ensure_one()
        attribute_id = False
        if type == 'color':
            attribute_id = attribute_line_ids.mapped('attribute_id').filtered(lambda a: a.attribute_type == 'color')
        elif type == 'forge':
            attribute_id = attribute_line_ids.mapped('attribute_id').filtered(lambda a: a.attribute_type == 'forge')
        elif type == 'anchor':
            attribute_id = attribute_line_ids.mapped('attribute_id').filtered(lambda a: a.attribute_type == 'anchor')
        elif type == 'hinge':
            attribute_id = attribute_line_ids.mapped('attribute_id').filtered(lambda a: a.attribute_type == 'hinge')
        elif type == 'molding':
            attribute_id = attribute_line_ids.mapped('attribute_id').filtered(lambda a: a.attribute_type == 'molding')
        elif type == 'handle':
            attribute_id = attribute_line_ids.mapped('attribute_id').filtered(lambda a: a.attribute_type == 'handle')
        elif type == 'deadbolt':
            attribute_id = attribute_line_ids.mapped('attribute_id').filtered(lambda a: a.attribute_type == 'deadbolt')
        elif type == 'arc':
            attribute_id = attribute_line_ids.mapped('attribute_id').filtered(lambda a: a.attribute_type == 'arc')
        elif type == 'family':
            attribute_id = attribute_line_ids.mapped('attribute_id').filtered(lambda a: a.attribute_type == 'family')
        elif type == 'dust_guard':
            attribute_id = attribute_line_ids.mapped('attribute_id').filtered(lambda a: a.attribute_type == 'dust_guard')
        elif type == 'latch':
            attribute_id = attribute_line_ids.mapped('attribute_id').filtered(lambda a: a.attribute_type == 'latch')
        elif type == 'flashing':
            attribute_id = attribute_line_ids.mapped('attribute_id').filtered(lambda a: a.attribute_type == 'flashing')
        elif type == 'preparations':
            attribute_id = attribute_line_ids.mapped('attribute_id').filtered(lambda a: a.attribute_type == 'preparations')
        elif type == 'panel':
            attribute_id = attribute_line_ids.mapped('attribute_id').filtered(lambda a: a.attribute_type == 'panel')
        elif type == 'setup':
            attribute_id = attribute_line_ids.mapped('attribute_id').filtered(lambda a: a.attribute_type == 'setup')

        return attribute_id

    def _reset_specs_fields(self):
        fields = self._fields
        for field in fields.keys():
            if field not in models.MAGIC_COLUMNS + self._get_no_reset_fields():
                if fields[field].type in ['text', 'char']:
                    self.update({field: ''})
                elif fields[field].type in ['integer', 'float']:
                    self.update({field: 0})
                elif fields[field].type == 'one2many':
                    self.update({field: []})
                else:
                    self.update({field: False})

    def _get_attribute_ids(self, type):
        self.ensure_one()
        return self.env['product.attribute'].search([('attribute_type', '=', type)])

    def _get_view(self, view_id=None, view_type='form', **options):
        arch, view = super()._get_view(view_id, view_type, **options)
        if view_type in ['form']:
            # all fields
            _fields = self._get_specs_fields()

            for field in _fields:
                if field not in self._get_no_reset_fields():
                    field_node = next(iter(arch.xpath(f'//field[@name="{field}"]')), None)
                    if field_node is not None:
                        field_node.attrib['required'] = f"'{field}' in field_ui_modifications"
                        field_node.attrib['invisible'] = f"'{field}' in field_ui_invisible"
                        if field in ['specs_glass_line_ids']:  # los vidrios siempre sera editable
                            field_node.attrib['readonly'] = "state in ['cancel']"
                        else:
                            field_node.attrib['readonly'] = f"block_changes == True and '{field}' not in field_ui_readonly or '{field}' in field_ui_readonly and can_edit_spec_in_manufacturing == False"
        return arch, view

    def _get_company_partner(self, name, country):
        self.ensure_one()
        company = self._get_company(name, country)
        return company.partner_id or False

    def _get_company(self, cost=False):
        self.ensure_one()
        if not cost:
            company_id = self.env.company.specs_sale_company_id
        else:
            company_id = self.env.company.specs_cost_company_id
        return company_id or self.env.company

    def _get_glasses_info(self, glass_line=None):
        self.ensure_one()
        name_list = []
        if not glass_line:
            specs_glass_line_ids = self.specs_glass_line_ids
        else:
            specs_glass_line_ids = self.specs_glass_line_ids.filtered(lambda l: l == glass_line)
        if specs_glass_line_ids:
            for glass in specs_glass_line_ids:
                attribute = glass.glass_type_id and glass.glass_type_id.name or ""
                glass_piece = glass.glass_piece_id and glass.glass_piece_id.name or ""
                handing_glass = glass.handing_glass_id and glass.handing_glass_id.name or ""
                radius = glass.radius_id and glass.radius_id.name or ""
                glass_width = str(glass.glass_width)
                glass_height = str(glass.glass_height)
                glass_qty = str(glass.glass_qty)

                name_list.append({
                    'attribute': attribute,
                    'piece': _("PIECE: ") + glass_piece,
                    'handing': _("HANDING: ") + handing_glass,
                    'radius': _("RADIUS: ") + radius,
                    'width': _("WIDTH: ") + glass_width,
                    'height': _("HEIGHT: ") + glass_height,
                    'qty': _("QTY: ") + glass_qty,
                })
        return name_list

    def get_product_attribute(self, product_attribute_value, second_attribute_value=None):
        self.ensure_one()
        company = self.env.company
        if second_attribute_value:
            attribute_id = second_attribute_value.attribute_id
            attribute_id1 = product_attribute_value.attribute_id
            product = self.env['product.product'].sudo().with_company(company).search([
                ('product_template_variant_value_ids.attribute_id', '=', attribute_id1.id),
                ('product_template_variant_value_ids.product_attribute_value_id', '=', product_attribute_value.id),
                ('company_id', '=', company.id),
            ])
            product = product.filtered(lambda p: attribute_id.id in p.product_template_variant_value_ids.attribute_id.ids and second_attribute_value.id in p.product_template_variant_value_ids.product_attribute_value_id.ids)
        else:
            domain = [
                ('product_template_variant_value_ids.attribute_id', '=', product_attribute_value.attribute_id.id),
                ('product_template_variant_value_ids.product_attribute_value_id', '=', product_attribute_value.id),
                ('company_id', '=', company.id),
            ]
            product = self.env['product.product'].sudo().with_company(company).search(domain)

        return product
