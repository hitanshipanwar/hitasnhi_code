# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class SpecsSale(models.Model):
    _inherit = 'specs.sale'

    bom_ids = fields.One2many('mrp.bom', 'specs_id', string='Bill of Materials')
    bom_count = fields.Integer('BoM count', compute='_compute_bom_count')

    @api.depends('bom_ids', 'bom_ids.specs_id')
    def _compute_bom_count(self):
        data = self.env['mrp.bom']._read_group([('specs_id', 'in', self.ids)], ['specs_id'], ['__count'])
        result = {order.id: count for order, count in data}
        for order in self:
            order.bom_count = result.get(order.id, 0)

    def materials_bills_create(self, product_attribute_value):
        self.ensure_one()
        setup_attribute_id = self.specs_dc_id.product_attribute_id.value_ids.filtered(
            lambda v: v.config_id == self.specs_dc_id)

        # trim
        if product_attribute_value.attribute_id.attribute_type == 'molding':
            product = self.get_product_attribute(product_attribute_value, second_attribute_value=self.specs_type_arc_id)
        # Threshold
        elif product_attribute_value.attribute_id.attribute_type == 'dust_guard':
            product = self.get_product_attribute(product_attribute_value, second_attribute_value=setup_attribute_id)
        # Flashing
        elif product_attribute_value.attribute_id.attribute_type == 'flashing':
            product = self.get_product_attribute(product_attribute_value, second_attribute_value=setup_attribute_id)
        # Product family
        elif product_attribute_value.attribute_id.attribute_type == 'family':
            product = self.get_product_attribute(product_attribute_value, second_attribute_value=setup_attribute_id)
        else:
            product = self.get_product_attribute(product_attribute_value)

        # attribute_id = product_attribute_value.attribute_id
        # product = self.env['product.product'].search([
        #     ('product_tmpl_id', '!=', self.specs_product_type_id.id),
        #     ('product_template_variant_value_ids.attribute_id', '=', attribute_id.id),
        #     ('product_template_variant_value_ids.product_attribute_value_id', '=', product_attribute_value.id),
        # ])
        # find product by family product
        if product and product.specs_dc_ids and self.specs_dc_id.id in product.specs_dc_ids.ids:
            return product
        return product

    def action_create_materials_bills(self):
        for rec in self:
            materials = self.env['product.product']
            materials = []
            uom_id = rec.specs_product_type_id._get_default_uom_id()
            specs_product_id = rec.specs_product_id
            family_attribute_value_id = specs_product_id.product_attribute_id.value_ids.filtered(
                lambda v: v.family_product_id == specs_product_id)
            # family_product_id = self.env['product.product'].sudo().search(domain)

            # list to find product with the variants (product.attribute.value)
            lista = [
                rec.specs_color_id,
                rec.specs_anchor_id,
                rec.specs_hinges_id,
                rec.specs_molding_int_id,
                rec.specs_molding_ext_id,
                rec.specs_typeguar_id,
                rec.specs_flashing_id,
                rec.specs_latchsup_id,
                rec.specs_latchin_id,
                rec.specs_forging_id,
                rec.specs_jac_id,
                rec.specs_jacin_id,
                rec.specs_jin_id,
                rec.specs_jinin_id,
            ] + [glass_type_id for glass_type_id in rec.specs_glass_line_ids.mapped('glass_type_id')]
            if family_attribute_value_id:
                lista.append(family_attribute_value_id)

            # find product
            lista = [item for item in lista if item]
            for product_attribute_value in lista:
                if product_attribute_value:
                    found_products = rec.materials_bills_create(product_attribute_value)
                    if found_products:
                        materials.append(found_products)

            if rec.specs_bac:
                product_id = rec._get_ball_catches_or_roller_latches_product('specs_bac')
                materials.append(product_id)
            if rec.specs_rlat:
                product_id = rec._get_ball_catches_or_roller_latches_product('specs_rlat')
                materials.append(product_id)

            for line in rec.specs_sale_id.order_line.filtered(lambda l: l.sale_specs_name == rec.name):
                bom_values = rec._prepare_bom_values(line, uom_id)
                bills = self.env['mrp.bom'].create(bom_values)
                for material in materials:
                    if material:
                        product_qty = 1
                        if material.product_spec_ball_catche:
                            product_qty = rec.specs_bac
                        if material.product_spec_roller_latche:
                            product_qty = rec.specs_rlat
                        self.env['mrp.bom.line'].create(
                            {
                                'bom_id': bills.id,
                                'product_id': material.id,
                                'product_uom_id': material.uom_id and material.uom_id.id or uom_id.id,
                                'product_qty': product_qty,
                            }
                        )
                bills_msg = _("This Bill of Materials has been created from: %s", self.name)
                bills.message_post(body=bills_msg)
            rec.stage_id = self.env.ref("solt_quarry_door_mpr.stage_finish", raise_if_not_found=False)

    def _prepare_bom_values(self, order_line, uom_id):
        self.ensure_one()
        return {
                'product_tmpl_id': order_line.product_template_id.id,
                'product_id': order_line.product_id.id,
                'product_uom_id': order_line.product_uom and order_line.product_uom.id or uom_id.id,
                'product_qty': 1.00,
                'specs_id': self.id
            }

    def view_action_bom(self):
        self.ensure_one()
        action = {
            'res_model': 'mrp.bom',
            'type': 'ir.actions.act_window',
            'context': {'create': False, 'delete': False, 'edit': False}
        }
        if len(self.bom_ids) == 1:
            action.update({
                'view_mode': 'form',
                'res_id': self.bom_ids.id,
            })
        else:
            action.update({
                'name': _("Bill of Material Generated by %s", self.name),
                'domain': [('id', 'in', self.bom_ids.ids)],
                'view_mode': 'tree,form',
            })
        return action

    def _get_state_list(self):
        states = super(SpecsSale, self)._get_state_list()
        return states + ['bom']

    def _get_max_amount_field_of_family(self, field):
        pass

    def _get_ball_catches_or_roller_latches_product(self, field):
        if field == 'specs_bac':
            domain = [('product_spec_ball_catche', '=', True)]
        if field == 'specs_rlat':
            domain = [('product_spec_roller_latche', '=', True)]
        return self.env['product.product'].search(domain)

    def _get_view(self, view_id=None, view_type='form', **options):
        arch, view = super()._get_view(view_id, view_type, **options)
        if view_type in ['form']:
            # all fields
            _fields = self._get_specs_fields()
            for field in _fields:
                if field in ['specs_glass_line_ids']:
                    field_node = next(iter(arch.xpath(f'//field[@name="{field}"]')), None)
                    if field_node is not None:
                        field_node.attrib['required'] = f"'{field}' in field_ui_modifications"
                        field_node.attrib['invisible'] = f"'{field}' in field_ui_invisible"
                        field_node.attrib['readonly'] = "state in ['bom', 'cancel']"
        return arch, view

