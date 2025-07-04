# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    # Generate the Sales Order values from the PO
    # def _prepare_sale_order_data(self, name, partner, company, direct_delivery_address):
    #     values = super(PurchaseOrder, self)._prepare_sale_order_data(name, partner, company, direct_delivery_address)
    #     sale_order_ids = self._get_sale_orders()
    #     values['specs_sale_ids'] = []
    #     if sale_order_ids:
    #         specs_sale_ids = sale_order_ids.specs_sale_ids.filtered(lambda r: r.state != 'cancel')
    #         specs_sale_ids = specs_sale_ids.with_company(company)
    #         values['specs_sale_ids'] = [(6, 0, specs_sale_ids.ids)]
            # for specs in sale_order_ids.specs_sale_ids.filtered(lambda r: r.state != 'cancel'):
            #     values['specs_sale_ids'] += [(0, 0, self._prepare_specs_sale_data(specs, company))]

        # return values

    def _prepare_specs_sale_data(self, specs, company):
        self.ensure_one()

        return {
            'name': specs.name,
            'sequence_name': specs.sequence_name,
            'stage_id': specs.stage_id.id,
            'specs_product_type_id': specs.specs_product_type_id.id,
            'creation_date': specs.creation_date,
            'version': specs.version,
            'unit_id': specs.unit_id,
            'specs_product_id': specs.specs_product_id and specs.specs_product_id.id or False,
            'specs_design_id': specs.specs_design_id and specs.specs_design_id.id or False,
            'specs_suffix_id': specs.specs_suffix_id and specs.specs_suffix_id.id or False,
            'specs_color_id': specs.specs_color_id and specs.specs_color_id.id or False,
            'specs_handing_id': specs.specs_handing_id and specs.specs_handing_id.id or False,
            'specs_forging_id': specs.specs_forging_id and specs.specs_forging_id.id or False,
            'specs_type_arc_id': specs.specs_type_arc_id and specs.specs_type_arc_id.id or False,
            'specs_fixed_glass': specs.specs_fixed_glass,
            'specs_type_glass_id': specs.specs_type_glass_id and specs.specs_type_glass_id.id or False,
            'specs_total_ant': specs.specs_total_ant,
            'specs_total_alt': specs.specs_total_alt,
            'specs_antmarc': specs.specs_antmarc,
            'specs_altmarc': specs.specs_altmarc,
            'specs_bast': specs.specs_bast,
            'specs_porfbast': specs.specs_porfbast,
            'specs_antleaft': specs.specs_antleaft,
            'specs_altleaft': specs.specs_altleaft,
            # 'specs_tramrec': specs.specs_tramrec,
            # 'specs_traminc': specs.specs_traminc,
            # 'specs_tramcurniv': specs.specs_tramcurniv,
            # 'specs_tramcurin': specs.specs_tramcurin,
            # 'specs_pasrec': specs.specs_pasrec,
            # 'specs_newdec': specs.specs_newdec,
            'specs_altarc': specs.specs_altarc,
            'specs_tolsup': specs.specs_tolsup,
            'specs_tolcen': specs.specs_tolcen,
            'specs_tollat': specs.specs_tollat,
            'specs_anchor_id': specs.specs_anchor_id and specs.specs_anchor_id.id or False,
            'specs_hinges_id': specs.specs_hinges_id and specs.specs_hinges_id.id or False,
            'specs_molding_int_id': specs.specs_molding_int_id and specs.specs_molding_int_id.id or False,
            'specs_molding_ext_id': specs.specs_molding_ext_id and specs.specs_molding_ext_id.id or False,
            'specs_traslape_int_id': specs.specs_traslape_int_id and specs.specs_traslape_int_id.id or False,
            'specs_traslape_ext_id': specs.specs_traslape_ext_id and specs.specs_traslape_ext_id.id or False,
            'specs_ancmarc': specs.specs_ancmarc,
            'specs_profmarc': specs.specs_profmarc,
            'specs_amount_hinges': specs.specs_amount_hinges,
            'specs_jac_id': specs.specs_jac_id and specs.specs_jac_id.id or False,
            'specs_jacin_id': specs.specs_jacin_id and specs.specs_jacin_id.id or False,
            'specs_jin_id': specs.specs_jin_id and specs.specs_jin_id.id or False,
            'specs_jinin_id': specs.specs_jinin_id and specs.specs_jinin_id.id or False,
            'specs_pch_id': specs.specs_pch_id and specs.specs_pch_id.id or False,
            'specs_moce_id': specs.specs_moce_id and specs.specs_moce_id.id or False,
            'specs_altce': specs.specs_altce,
            'specs_mbas': specs.specs_mbas,
            'specs_mbai': specs.specs_mbai,
            'specs_rlat': specs.specs_rlat,
            'specs_bac': specs.specs_bac,
            'specs_tyarct_id': specs.specs_tyarct_id and specs.specs_tyarct_id.id or False,
            'specs_taltarc': specs.specs_taltarc,
            'specs_antra': specs.specs_antra,
            'specs_altra': specs.specs_altra,
            # 'specs_altpc': specs.specs_altpc,
            # 'specs_anpc': specs.specs_anpc,
            'specs_ddm': specs.specs_ddm,
            'specs_board_type_id': specs.specs_board_type_id and specs.specs_board_type_id.id or False,
            'specs_posfi_id': specs.specs_posfi_id and specs.specs_posfi_id.id or False,
            'specs_anfi': specs.specs_anfi,
            'specs_alfi': specs.specs_alfi,
            'specs_saltboard_type': specs.specs_saltboard_type,
            'specs_sidelight_glassf': specs.specs_sidelight_glassf,
            'specs_ddmf': specs.specs_ddmf,
            'description': specs.description,
            'specs_latchsup_id': specs.specs_latchsup_id and specs.specs_latchsup_id.id or False,
            'specs_latchin_id': specs.specs_latchin_id and specs.specs_latchin_id.id or False,
            'specs_typeguar_id': specs.specs_typeguar_id and specs.specs_typeguar_id.id or False,
            'specs_flashing_id': specs.specs_flashing_id and specs.specs_flashing_id.id or False,
            'specs_assembly_id': specs.specs_assembly_id and specs.specs_assembly_id.id or False,
            'specs_cls': specs.specs_cls,
            'specs_cli': specs.specs_cli,
            'specs_tolerance': specs.specs_tolerance,
            'specs_operable': specs.specs_operable,
            'specs_huacal': specs.specs_huacal,
            'specs_typef_glass_id': specs.specs_typef_glass_id and specs.specs_typef_glass_id.id or False,
            'specs_typet_glass_id': specs.specs_typet_glass_id and specs.specs_typet_glass_id.id or False,
            'specs_board_id': specs.specs_board_id and specs.specs_board_id.id or False,
            'specs_glass_line_ids': [(0, 0, {
                'glass_piece_id': line.glass_piece_id.id,
                'handing_glass_id': line.handing_glass_id.id,
                'radius_id': line.radius_id.id,
                'glass_type_id': line.glass_type_id and line.glass_type_id.id or False,
                'sequence': line.sequence,
                'glass_width': line.glass_width,
                'glass_height': line.glass_height,
                'glass_qty': line.glass_qty,
            }) for line in specs.specs_glass_line_ids],
            # 'specs_line_ids': [(0, 0, {
            #     'accessories_id': line.accessories_id.id,
            #     'amount_accessories': line.amount_accessories,
            #     'sequence': line.sequence,
            # }) for line in specs.specs_line_ids],
            # 'specs_sp_line_ids': [(0, 0, {
            #     'preparations_ids': [(6, 0, line.preparations_ids.ids)],
            #     'amount_preparations': line.amount_preparations,
            #     'sequence': line.sequence,
            # }) for line in specs.specs_sp_line_ids],
            'specs_hardware_line_ids': [(0, 0, {
                'hardware_id': line.hardware_id.id,
                'amount': line.amount,
                'sequence': line.sequence,
                'include_in_spec_price': line.include_in_spec_price,
            }) for line in specs.specs_hardware_line_ids],
            'specs_dc_id': specs.specs_dc_id.id or False,
            'from_duplicate': specs.from_duplicate,
            'product_uom_qty': specs.product_uom_qty,
            'specs_opportunity_name': specs.specs_opportunity_name,
            'amount_total_manufacturing': specs.specs_amount_total,
        }

    @api.model
    def _prepare_sale_order_line_data(self, line, company):
        values = super(PurchaseOrder, self)._prepare_sale_order_line_data(line, company)

        # specs description
        if line.product_description_variants and len(line.product_description_variants.split('/')) == 6:
            values['sale_specs_name'] = line.product_description_variants
        return values

    def inter_company_create_sale_order(self, company):
        """ Create a Sales Order from the current PO (self)
            Note : In this method, reading the current PO is done as sudo, and the creation of the derived
            SO as intercompany_user, minimizing the access right required for the trigger user.
            :param company : the company of the created PO
            :rtype company : res.company record
        """
        # find user for creating and validation SO/PO from partner company
        intercompany_uid = company.intercompany_user_id and company.intercompany_user_id.id or False
        if not intercompany_uid:
            raise UserError(_(
                'Provide at least one user for inter company relation for %(name)s',
                name=company.name,
            ))
        # check intercompany user access rights
        if not self.env['sale.order'].check_access_rights('create', raise_exception=False):
            raise UserError(_(
                "Inter company user of company %(name)s doesn't have enough access rights",
                name=company.name,
            ))

        for rec in self:
            # check pricelist currency should be same with SO/PO document
            company_partner = rec.company_id.partner_id.with_user(intercompany_uid)
            if company_partner.property_product_pricelist and \
               rec.currency_id.id != company_partner.property_product_pricelist.currency_id.id:
                raise UserError(_(
                    'You cannot create SO from PO because sale price list currency is different '
                    'than purchase price list currency.\n'
                    'The currency of the SO is obtained from the pricelist of the company partner.\n\n'
                    '(SO currency: %(so_currency)s, Pricelist: %(pricelist)s, Partner: %(partner)s (ID: %(id)s))',
                    so_currency=rec.currency_id.name,
                    pricelist=company_partner.property_product_pricelist.display_name,
                    partner=company_partner.display_name,
                    id=company_partner.id,
                ))

            # create the SO and generate its lines from the PO lines
            # read it as sudo, because inter-compagny user can not have the access right on PO
            direct_delivery_address = rec.picking_type_id.warehouse_id.partner_id.id or rec.dest_address_id.id
            sale_order_data = rec.sudo()._prepare_sale_order_data(
                rec.name, company_partner, company,
                direct_delivery_address or False)
            inter_user = self.env['res.users'].sudo().browse(intercompany_uid)
            # lines are browse as sudo to access all data required to be copied on SO line (mainly for company dependent field like taxes)
            for line in rec.order_line.sudo():
                sale_order_data['order_line'] += [(0, 0, rec._prepare_sale_order_line_data(line, company))]
            sale_order = self.env['sale.order'].with_context(allowed_company_ids=inter_user.company_ids.ids).with_user(intercompany_uid).create(sale_order_data)
            # specs
            sale_order_ids = self._get_sale_orders()
            if sale_order_ids and sale_order:
                values = ['sale.order,%s' % (order_id,) for order_id in sale_order_ids.ids]
                specs_sale_prop = self.env['ir.property'].sudo().search([('value_reference', 'in', values)]).mapped('res_id')
                if specs_sale_prop:
                    specs_sale_ids = [int(res_id.split(',')[1]) for res_id in specs_sale_prop if res_id and len(res_id.split(',')) > 1]
                    specs_sale_ids = self.env['specs.sale'].browse(specs_sale_ids).exists()
                    specs_sale_ids.write({
                        'specs_sale_id': sale_order.id,
                        'currency_id': sale_order.currency_id.id,
                        'company_id': sale_order.company_id.id,
                        'salesman_id': sale_order.user_id and sale_order.user_id.id or False,
                    })
                    for spec_id in specs_sale_ids:
                        documents_folder_id = spec_id.with_company(rec.company_id).documents_folder_id
                        # Copiar los documentos al nuevo specs
                        for doc in documents_folder_id.document_ids:
                            new_attachment = False
                            if doc.attachment_id:
                                new_attachment = doc.attachment_id.copy({
                                    'res_model': doc.res_model,
                                    'res_id': spec_id.id,
                                    'company_id': spec_id.company_id.id
                                })
                            if new_attachment and new_attachment.document_ids:
                                new_attachment.document_ids.sudo().write({
                                    'res_id': spec_id.id,
                                    'folder_id': spec_id.documents_folder_id.id,
                                    'res_model': 'specs.sale',
                                    'company_id': spec_id.company_id.id
                                })
            msg = _("Automatically generated from %(origin)s of company %(company)s.", origin=self.name, company=rec.company_id.name)
            sale_order.message_post(body=msg)

            # write vendor reference field on PO
            if not rec.partner_ref:
                rec.partner_ref = sale_order.name

            #Validation of sales order
            if company.auto_validation:
                sale_order.with_user(intercompany_uid).action_confirm()
    

