# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    def _prepare_procurement_values(self, group_id=False):
        values = super(SaleOrderLine, self)._prepare_procurement_values(group_id=group_id)
        if self.sale_specs_name:
            values['product_description_variants'] = self.sale_specs_name
        return values

    # functions for create Glass PO
    def _purchase_spec_match_supplier(self, product_id, quantity, **kwargs):
        # determine vendor of the order (take the first matching company and product)
        suppliers = product_id._select_seller(partner_id=self._retrieve_purchase_partner(),
                                                   quantity=quantity,
                                                   date=self.order_id.date_order and self.order_id.date_order.date())
        if not suppliers:
            raise UserError(_("There is no vendor associated to the product %s. Please define a vendor for this product.", product_id.display_name))
        return suppliers[0]

    def _purchase_spec_prepare_order_values(self, supplierinfo):
        """ Returns the values to create the purchase order from the current SO line.
            :param supplierinfo: record of product.supplierinfo
            :rtype: dict
        """
        self.ensure_one()
        partner_supplier = supplierinfo.partner_id
        fpos = self.env['account.fiscal.position'].sudo()._get_fiscal_position(partner_supplier)
        date_order = self._purchase_get_date_order(supplierinfo)
        return {
            'partner_id': partner_supplier.id,
            'partner_ref': partner_supplier.ref,
            'company_id': self.company_id.id,
            'currency_id': partner_supplier.property_purchase_currency_id.id or self.env.company.currency_id.id,
            'origin': self.order_id.name,
            'payment_term_id': partner_supplier.property_supplier_payment_term_id.id,
            'date_order': date_order,
            'fiscal_position_id': fpos.id,
        }

    def _create_spec_purchase_order(self, supplierinfo):
        values = self._purchase_spec_prepare_order_values(supplierinfo)
        return self.env['purchase.order'].with_context(mail_create_nosubscribe=True).create(values)

    def _purchase_match_purchase_order(self, partner, company=False):
        return self.env['purchase.order'].search([
            ('partner_id', '=', partner.id),
            ('state', '=', 'draft'),
            ('company_id', '=', (company and company or self.env.company).id),
        ], order='id desc')

    def _match_or_spec_create_purchase_order(self, supplierinfo):
        purchase_order = self._purchase_match_purchase_order(supplierinfo.partner_id)[:1]
        if not purchase_order:
            purchase_order = self._create_spec_purchase_order(supplierinfo)
        return purchase_order

    def _create_purchase_order_by_spec(self):
        self.ensure_one()
        supplier_po_map = {}
        sale_line_purchase_map = {}

        specs_glass_line_ids = self.sale_specs_id.specs_glass_line_ids
        if self.sale_specs_id and not self.sale_specs_id.specs_glass_line_ids:
            raise UserError(_(f"Invalid operation! The spec {self.sale_specs_id.name} has no glass information."))

        for glass_line in specs_glass_line_ids:
            product_id = glass_line.specs_id.get_product_attribute(glass_line.glass_type_id)
            if not product_id:
                raise UserError(_(f"Product not found for attribute {glass_line.glass_type_id.name} and the company {self.company_id.name}"))

            supplierinfo = self._purchase_spec_match_supplier(product_id, glass_line.glass_qty)
            partner_supplier = supplierinfo.partner_id

            # determine (or create) PO
            purchase_order = supplier_po_map.get(partner_supplier.id)
            if not purchase_order:
                purchase_order = self._match_or_spec_create_purchase_order(supplierinfo)
            so_name = self.order_id.name
            origins = (purchase_order.origin or '').split(', ')
            if so_name not in origins:
                purchase_order.write({'origin': ', '.join(origins + [so_name])})
            supplier_po_map[partner_supplier.id] = purchase_order

            # add a PO line to the PO
            values = self.env['purchase.order.line']._prepare_purchase_order_line(product_id, glass_line.glass_qty, product_id.uom_po_id, self.company_id, supplierinfo, purchase_order)
            values['sale_line_id'] = self.id,
            values.update(self._update_po_line_name(glass_line, values))
            purchase_line = self.env['purchase.order.line'].create(values)

            # link the generated purchase to the SO line
            sale_line_purchase_map.setdefault(self, self.env['purchase.order.line'])
            sale_line_purchase_map[self] |= purchase_line

    def _update_po_line_name(self, glass_line, values):
        self.ensure_one()
        spec_id = glass_line.specs_id
        if values.get('product_description_variants'):
            line_sale_specs_name = values['product_description_variants']
        else:
            line_sale_specs_name = spec_id.name
        if line_sale_specs_name == spec_id.name and len(line_sale_specs_name.split('/')) == 6:
            values['product_description_variants'] = line_sale_specs_name
        # si hay spec y tiene configurado glasses adicionar al nombre
        if spec_id and glass_line:
            glasses_info = spec_id._get_glasses_info(glass_line=glass_line)
            piece_info = ''.join(v for tinfo in glasses_info for k, v in tinfo.items() if k == 'piece')
            values['name'] = '\n'.join(v for tinfo in glasses_info for k, v in tinfo.items() if k != 'piece') + '\n' + 'LABEL: ' + line_sale_specs_name + ' ' + piece_info
        return values

    # create PO hardware
    def _create_purchase_order_hardware_by_spec(self):
        self.ensure_one()
        supplier_po_map = {}
        sale_line_purchase_map = {}

        specs_hardware_line_ids = self.sale_specs_id.specs_hardware_line_ids
        if self.sale_specs_id and not self.sale_specs_id.specs_hardware_line_ids:
            raise UserError(_(f"Invalid operation! The spec {self.sale_specs_id.name} has no hardware information."))

        for hardware in specs_hardware_line_ids:
            product_id = hardware.hardware_id.product_id
            spec_id = hardware.specs_id
            if not product_id:
                raise UserError(
                    _(f"Product not found for hardware {hardware.hardware_id.name} and the company {self.company_id.name}"))

            supplierinfo = self._purchase_spec_match_supplier(product_id, hardware.amount)
            partner_supplier = supplierinfo.partner_id

            # determine (or create) PO
            purchase_order = supplier_po_map.get(partner_supplier.id)
            if not purchase_order:
                purchase_order = self._match_or_spec_create_purchase_order(supplierinfo)
            so_name = self.order_id.name
            origins = (purchase_order.origin or '').split(', ')
            if so_name not in origins:
                purchase_order.write({'origin': ', '.join(origins + [so_name])})
            supplier_po_map[partner_supplier.id] = purchase_order

            # add a PO line to the PO
            values = self.env['purchase.order.line']._prepare_purchase_order_line(product_id, hardware.amount,
                                                                                  product_id.uom_po_id, self.company_id,
                                                                                  supplierinfo, purchase_order)
            values['sale_line_id'] = self.id,
            if values.get('product_description_variants'):
                line_sale_specs_name = values['product_description_variants']
            else:
                line_sale_specs_name = spec_id.name
            if line_sale_specs_name == spec_id.name and len(line_sale_specs_name.split('/')) == 6:
                values['product_description_variants'] = line_sale_specs_name
            values['name'] += '\n' + line_sale_specs_name
            purchase_line = self.env['purchase.order.line'].create(values)

            # link the generated purchase to the SO line
            sale_line_purchase_map.setdefault(self, self.env['purchase.order.line'])
            sale_line_purchase_map[self] |= purchase_line