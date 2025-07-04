from datetime import datetime
from math import ceil, floor
from odoo import models, _
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_round, float_is_zero

import logging
_logger = logging.getLogger(__name__)


class ProductProduct(models.Model):
    _inherit = 'product.product'
    
    def get_products_based_on_movement_date_ept(self, from_datetime, company):
        """ Override from common_connector_library/models/product_product.py
            Change query to get products with negative forecasted quantity
        """
        if not from_datetime or not company:
            raise UserError(_('You must provide the From Date and Company'))
        result = []
        mrp_module = self.search_installed_module_ept('mrp')
        date = str(datetime.strftime(from_datetime, '%Y-%m-%d %H:%M:%S'))

        if mrp_module:
            result = self.get_product_movement_of_bom_product(date, company)

        # Original query allowed states from ('partially_available','assigned','done')
        # Products with negative forecasted qty will be 'waiting' or 'confirmed'
        # Easier to just exclude moves that are not confirmed
        qry = ("""select product_id from stock_move where date >= '%s' and company_id = %d and
                 state not in ('draft','cancel')""" % (date, company.id))
        self._cr.execute(qry)
        result += self._cr.dictfetchall()
        product_ids = [product_id.get('product_id') for product_id in result]

        return list(set(product_ids))
    
    def get_product_movement_of_bom_product(self, date, company):
        """ Override from common_connector_library/models/product_product.py
            Change query to get products with negative forecasted quantity
        """
        # Also change stock move query here
        mrp_qry = ("""select p.id as product_id from product_product as p
                    inner join mrp_bom as mb on mb.product_tmpl_id=p.product_tmpl_id
                    inner join mrp_bom_line as ml on ml.bom_id=mb.id
                    inner join stock_move as sm on sm.product_id=ml.product_id
                    where sm.date >= '%s' and sm.company_id = %d and 
                    sm.state not in ('draft','cancel')""" % (date, company.id))
        self._cr.execute(mrp_qry)
        result = self._cr.dictfetchall()
        return result
    
    def check_for_bom_products(self, product_ids):
        """ Override from common_connector_library/models/product_product.py
            Change query to exclude archived boms
        """
        bom_product_ids = []
        mrp_module = self.search_installed_module_ept('mrp')
        if mrp_module:
            qry = ("""select p.id as product_id from product_product as p
                        inner join mrp_bom as mb on mb.product_tmpl_id=p.product_tmpl_id
                        and mb.active = True and p.id in (%s)""" % product_ids)
            self._cr.execute(qry)
            bom_product_ids = self._cr.dictfetchall()
            bom_product_ids = {product_id.get('product_id') for product_id in bom_product_ids}

        return bom_product_ids
    
    def _compute_quantities_dict_omf_shopify_ept(self, bom):
        # this is an adapted method, some of the 
        # variable names won't make sense and/or were initialized to empty
        product = self
        qties = {}
        bom_sub_lines_per_kit = {}     
        prefetch_component_ids = set()

        __, bom_sub_lines = bom.explode(product, 1)
        bom_sub_lines_per_kit[product] = bom_sub_lines
        for bom_line, __ in bom_sub_lines:
            if bom_line.product_id.id not in qties:
                prefetch_component_ids.add(bom_line.product_id.id)

        bom_sub_lines = bom_sub_lines_per_kit[product]
        ratios_virtual_available = []
        ratios_qty_available = []
        ratios_incoming_qty = []
        ratios_outgoing_qty = []
        ratios_free_qty = []
        for bom_line, bom_line_data in bom_sub_lines:
            component = bom_line.product_id.with_context(mrp_compute_quantities=qties).with_prefetch(prefetch_component_ids)
            if component.type != 'product' or float_is_zero(bom_line_data['qty'], precision_rounding=bom_line.product_uom_id.rounding):
                # As BoMs allow components with 0 qty, a.k.a. optionnal components, we simply skip those
                # to avoid a division by zero. The same logic is applied to non-storable products as those
                # products have 0 qty available.
                continue
            _logger.warning('bom_line_data:')
            _logger.warning(str(bom_line_data))
            uom_qty_per_kit = bom_line_data['qty'] / bom_line_data['original_qty']
            _logger.warning('uom_qty_per_kit:')
            _logger.warning(str(uom_qty_per_kit))
            qty_per_kit = bom_line.product_uom_id._compute_quantity(uom_qty_per_kit, bom_line.product_id.uom_id, round=False, raise_if_failure=False)
            _logger.warning('qty_per_kit:')
            _logger.warning(str(qty_per_kit))
            if not qty_per_kit:
                continue
            rounding = component.uom_id.rounding
            _logger.warning('qties:')
            _logger.warning(str(qties))
            component_res = (
                qties.get(component.id)
                if component.id in qties
                else {
                    # "virtual_available": float_round(component.virtual_available, precision_rounding=rounding),
                    # "qty_available": float_round(component.qty_available, precision_rounding=rounding),
                    # "incoming_qty": float_round(component.incoming_qty, precision_rounding=rounding),
                    # "outgoing_qty": float_round(component.outgoing_qty, precision_rounding=rounding),
                    # "free_qty": float_round(component.free_qty, precision_rounding=rounding),
                    "virtual_available": floor(component.virtual_available),
                    "qty_available": floor(component.qty_available),
                    "incoming_qty": floor(component.incoming_qty),
                    "outgoing_qty": ceil(component.outgoing_qty),
                    "free_qty": floor(component.free_qty),
                }
            )
            _logger.warning('component_res:')
            _logger.warning(str(component_res))
            ratios_virtual_available.append(component_res["virtual_available"] / qty_per_kit)
            ratios_qty_available.append(component_res["qty_available"] / qty_per_kit)
            ratios_incoming_qty.append(component_res["incoming_qty"] / qty_per_kit)
            ratios_outgoing_qty.append(component_res["outgoing_qty"] / qty_per_kit)
            ratios_free_qty.append(component_res["free_qty"] / qty_per_kit)
        
        # Given that the qtys are already computed for the product
        # We need to add existing qty (this method was adapted from kit boms)
        # for a kit BoM, there is (or shouldn't be) "on hand" qty
        # for a real BoM, there might be, so what we're computing needs to be added to existing qtys
        _logger.warning('bom_sub_lines:')
        _logger.warning(str(bom_sub_lines))
        _logger.warning('ratios_virtual_available:')
        _logger.warning(str(ratios_virtual_available))
        _logger.warning('ratios_qty_available:')
        _logger.warning(str(ratios_qty_available))
        if bom_sub_lines and ratios_virtual_available:  # Guard against all cnsumable bom: at least one ratio should be present.
            return {
                'virtual_available': floor(min(ratios_virtual_available)) + product.virtual_available,
                'qty_available': floor(min(ratios_qty_available)) + product.qty_available,
                'incoming_qty': floor(min(ratios_incoming_qty)) + product.incoming_qty,
                'outgoing_qty': ceil(min(ratios_outgoing_qty)) + product.outgoing_qty,
                'free_qty': floor(min(ratios_free_qty)) + product.free_qty,
            }
        else:
            return {
                'virtual_available': product.virtual_available,
                'qty_available': product.qty_available,
                'incoming_qty': product.incoming_qty,
                'outgoing_qty': product.outgoing_qty,
                'free_qty': product.free_qty,
            }
        
    # Hibou Customize, handle regular BoMs for projected inventory.
    def get_forecasted_qty_ept(self, warehouse, product_list):
        """ This method is used to get forecast quantity based on warehouse and products.
            @param warehouse: Records of warehouse
            @param product_list: List of product ids
            @return: Dictionary with a product and its quantity.
            @author: Haresh Mori @Emipro Technologies Pvt. Ltd on date 21 September 2021 .
            Task_id: 178058
        """
        _logger.warning('get_forecasted_qty_ept %s %s' % (warehouse, product_list))
        forcasted_qty = {}
        location_ids, product_ids = self.prepare_location_and_product_ids(warehouse, product_list)
        
        _logger.warning('  location_ids %s product_ids %s' % (location_ids, product_ids))

        bom_product_ids = self.check_for_bom_products(product_ids)
        _logger.warning('  bom_product_ids %s' % (bom_product_ids, ))
        if bom_product_ids:
            bom_products = self.with_context(warehouse=warehouse.ids).browse(bom_product_ids)
            for product in bom_products:
                # original
                # actual_stock = getattr(product, 'free_qty') + getattr(product, 'incoming_qty')
                # now, we don't want incoming quantity
                actual_stock = product.qty_available - product.outgoing_qty
                if not product.is_kits:
                    # kits are already computed properly
                    # bom qty will be computed similarly to how kits does it in mrp.models.product.ProductProduct._compute_quantities_dict
                    boms = self.env['mrp.bom'].with_context(warehouse=warehouse.ids)._bom_find(product)
                    bom = boms.get(product)
                    if bom:
                        qtys = product._compute_quantities_dict_omf_shopify_ept(bom)
                        _logger.warning('bom_product_stock:')
                        _logger.warning(str(qtys))
                        # we have the 'can be built' qty, we need to add what we have and reduce what is outgoing
                        # if we do not, then we will always send what can be built and potentially underflow inventory as we rack up orders
                        actual_stock = qtys['qty_available'] - qtys['outgoing_qty']
                        # _logger.warning('qtys for bom: %s with qty_available: %s and outgoing: %s' % (qtys, product.qty_available, product.outgoing_qty))
                _logger.warning('    actual_stock set to %s for product %s' % (str(actual_stock), product.id))
                forcasted_qty.update({product.id: actual_stock})

        simple_product_list = list(set(product_list) - set(bom_product_ids))
        _logger.warning('  simple_product_list %s' % (simple_product_list, ))
        # customization to avoid query at all, use existing computation
        # commented out for comparison
        # simple_product_list_ids = ','.join(str(e) for e in simple_product_list)
        # if simple_product_list_ids:
        #     qry = self.prepare_forecasted_qty_query(location_ids, simple_product_list_ids)
        #     self._cr.execute(qry)
        #     result = self._cr.dictfetchall()
        #     for i in result:
        #         forcasted_qty.update({i.get('product_id'): i.get('stock')})
        if simple_product_list:
            single_products = self.browse(simple_product_list).with_context(warehouse=warehouse.ids)
            for p in single_products:
                forcasted_qty[p.id] = p.qty_available - p.outgoing_qty
        return forcasted_qty

