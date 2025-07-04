
from collections import defaultdict
from datetime import datetime
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.osv import expression
from odoo.tools import float_compare, OrderedSet


class StockRule(models.Model):
    _inherit = 'stock.rule'

    @api.model
    def _run_manufacture(self, procurements):
        new_productions_values_by_company = defaultdict(list)
        for procurement, rule in procurements:
            if float_compare(procurement.product_qty, 0, precision_rounding=procurement.product_uom.rounding) <= 0:
                # If procurement contains negative quantity, don't create a MO that would be for a negative value.
                continue
            bom = rule._get_matching_bom(procurement.product_id, procurement.company_id, procurement.values)

            mo = self.env['mrp.production']
            mto_route = self.env['stock.warehouse']._find_global_route('stock.route_warehouse0_mto',
                                                                       _('Replenish on Order (MTO)'))
            if rule.route_id != mto_route and procurement.origin != 'MPS':
                domain = rule._make_mo_get_domain(procurement, bom)
                mo = self.env['mrp.production'].sudo().search(domain, limit=1)
            if not mo:
                new_productions_values_by_company[procurement.company_id.id].append(
                    rule._prepare_mo_vals(*procurement, bom))
            else:
                self.env['change.production.qty'].sudo().with_context(skip_activity=True).create({
                    'mo_id': mo.id,
                    'product_qty': mo.product_id.uom_id._compute_quantity(
                        (mo.product_uom_qty + procurement.product_qty), mo.product_uom_id)
                }).change_prod_qty()

        note_subtype_id = self.env['ir.model.data']._xmlid_to_res_id('mail.mt_note')
        for company_id, productions_values in new_productions_values_by_company.items():
            # create the MO as SUPERUSER because the current user may not have the rights to do it (mto product launched by a sale for example)
            productions = self.env['mrp.production'].with_user(SUPERUSER_ID).sudo().with_company(company_id).create(
                productions_values)
            if not self.env.company.create_draft_mo:
                productions.filtered(self._should_auto_confirm_procurement_mo).action_confirm()

            for production in productions:
                origin_production = production.move_dest_ids and production.move_dest_ids[
                    0].raw_material_production_id or False
                orderpoint = production.orderpoint_id
                if orderpoint and orderpoint.create_uid.id == SUPERUSER_ID and orderpoint.trigger == 'manual':
                    production.message_post(
                        body=_('This production order has been created from Replenishment Report.'),
                        message_type='comment',
                        subtype_id=note_subtype_id
                    )
                elif orderpoint:
                    production.message_post_with_source(
                        'mail.message_origin_link',
                        render_values={'self': production, 'origin': orderpoint},
                        subtype_id=note_subtype_id,
                    )
                elif origin_production:
                    production.message_post_with_source(
                        'mail.message_origin_link',
                        render_values={'self': production, 'origin': origin_production},
                        subtype_id=note_subtype_id,
                    )
        return True