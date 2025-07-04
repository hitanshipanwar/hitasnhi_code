# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from datetime import datetime, timedelta
from collections import defaultdict

from odoo import models
from odoo.addons.sale_planner.wizard.order_planner import distance

import logging
_logger = logging.getLogger(__name__)


class SaleOrderMakePlan(models.TransientModel):
    _inherit = 'sale.order.make.plan'

    # override to get product specific planning policy
    def generate_base_option(self, order_fake):
        _logger.error('generate_base_option:')
        __start_date = datetime.now() - timedelta(days=30)
        product_lines = list(filter(lambda line: line.product_id.type == 'product', order_fake.order_line))
        if not product_lines:
            return {}

        buy_qty = defaultdict(int)
        for line in product_lines:
            buy_qty[line.product_id.id] += line.product_uom_qty

        products = self.env['product.product']
        for line in product_lines:
            products |= line.product_id

        policy_groups = defaultdict(lambda: {'products': [], 'buy_qty': {}})
        for p in products:
            policy = p.get_planning_policy()
            if policy:
                policy_groups[policy.id]['products'].append(p)
                policy_groups[policy.id]['buy_qty'][p.id] = buy_qty[p.id]
                policy_groups[policy.id]['policy'] = policy
            else:
                policy_groups[0]['products'].append(p)
                policy_groups[0]['buy_qty'][p.id] = buy_qty[p.id]

        for _, policy_group in policy_groups.items():
            product_set = self.env['product.product'].browse()
            for p in policy_group['products']:
                product_set += p
            policy_group['products'] = product_set
            policy_group['base_option'] = self._generate_base_option(order_fake, policy_group)

        option_policy_groups = defaultdict(lambda: {'products': self.env['product.product'].browse(),
                                                    'policies': self.env['sale.order.planning.policy'].browse(),
                                                    'date_planned': __start_date, 'sub_options': [], })
        for policy_id, policy_group in policy_groups.items():
            base_option = policy_group['base_option']
            _logger.error('  base_option: ' + str(base_option))
            b_wh_id = base_option['warehouse_id']
            if 'policy' in policy_group:
                option_policy_groups[b_wh_id]['policies'] += policy_group['policy']
            if option_policy_groups[b_wh_id].get('date_planned'):
                # The first base_option without a date clears it
                if base_option.get('date_planned'):
                    if base_option['date_planned'] > option_policy_groups[b_wh_id]['date_planned']:
                        option_policy_groups[b_wh_id]['date_planned'] = base_option['date_planned']
                else:
                    # One of our options has no plan date.  Remove it.
                    del option_policy_groups[b_wh_id]['date_planned']
            if 'sub_options' in base_option:
                option_policy_groups[b_wh_id]['sub_options'].append(base_option['sub_options'])
            option_policy_groups[b_wh_id]['products'] += policy_group['products']
            option_policy_groups[b_wh_id]['warehouse_id'] = b_wh_id

        # clean up unused sub_options and collapse used ones
        for o_wh_id, option_group in option_policy_groups.items():
            if not option_group['sub_options']:
                del option_group['sub_options']
            else:
                sub_options = defaultdict(lambda: {'date_planned': __start_date, 'product_ids': [], 'product_skus': []})
                remaining_products = option_group['products']
                for options in option_group['sub_options']:
                    for wh_id, option in options.items():
                        if sub_options[wh_id].get('date_planned'):
                            # The first option without a date clears it
                            if option.get('date_planned'):
                                if option['date_planned'] > sub_options[wh_id]['date_planned']:
                                    sub_options[wh_id]['date_planned'] = option['date_planned']
                            else:
                                del sub_options[wh_id]['date_planned']
                        sub_options[wh_id]['product_ids'] += option['product_ids']
                        sub_options[wh_id]['product_skus'] += option['product_skus']
                        remaining_products = remaining_products.filtered(
                            lambda p: p.id not in sub_options[wh_id]['product_ids'])
                option_group['sub_options'] = sub_options
                if remaining_products:
                    option_group['sub_options'][o_wh_id]['product_ids'] += remaining_products.ids
                    option_group['sub_options'][o_wh_id]['product_skus'] += remaining_products.mapped('default_code')

        # At this point we should have all of the policy options collapsed.
        # Collapse warehouse options.
        base_option = {'date_planned': __start_date, 'products': self.env['product.product'].browse()}
        for wh_id, intermediate_option in option_policy_groups.items():
            _logger.error('    base_option: ' + str(base_option))
            _logger.error('    intermediate_option: ' + str(intermediate_option))
            if 'warehouse_id' not in base_option:
                base_option['warehouse_id'] = wh_id
            b_wh_id = base_option['warehouse_id']

            if base_option.get('date_planned'):
                if intermediate_option.get('date_planned'):
                    if intermediate_option['date_planned'] > base_option['date_planned']:
                        base_option['date_planned'] = intermediate_option['date_planned']
                else:
                    del base_option['date_planned']
                    if 'sub_options' in base_option:
                        for _, option in base_option['sub_options'].items():
                            del option['date_planned']
            if b_wh_id == wh_id:
                if 'sub_options' in intermediate_option and 'sub_options' not in base_option:
                    # Base option will get new sub_options
                    intermediate_option['sub_options'][wh_id]['product_ids'] += base_option['products'].ids
                    intermediate_option['sub_options'][wh_id]['product_skus'] += base_option['products'].mapped(
                        'default_code')
                    base_option['sub_options'] = intermediate_option['sub_options']
                elif 'sub_options' in intermediate_option and 'sub_options' in base_option:
                    # Both have sub_options, merge
                    for o_wh_id, option in intermediate_option['sub_options'].items():
                        if o_wh_id not in base_option['sub_options']:
                            base_option['sub_options'][o_wh_id] = option
                        else:
                            base_option['sub_options'][o_wh_id]['product_ids'] += option['product_ids']
                            base_option['sub_options'][o_wh_id]['product_skus'] += option['product_skus']
                        if base_option.get('date_planned'):
                            if option['date_planned'] > base_option['sub_options'][o_wh_id]['date_planned']:
                                base_option['sub_options'][o_wh_id]['date_planned'] = intermediate_option[
                                    'date_planned']
                elif 'sub_options' in base_option:
                    # merge products from intermediate into base_option's sub_options
                    base_option['sub_options'][wh_id]['product_ids'] += intermediate_option['products'].ids
                    base_option['sub_options'][wh_id]['product_skus'] += intermediate_option['products'].mapped(
                        'default_code')
                base_option['products'] += intermediate_option['products']
            else:
                # Promote
                if 'sub_options' not in intermediate_option and 'sub_options' not in base_option:
                    base_option['sub_options'] = {
                        wh_id: {
                            'product_ids': intermediate_option['products'].ids,
                            'product_skus': intermediate_option['products'].mapped('default_code'),
                        },
                        b_wh_id: {
                            'product_ids': base_option['products'].ids,
                            'product_skus': base_option['products'].mapped('default_code'),
                        },
                    }
                    if base_option.get('date_planned'):
                        base_option['sub_options'][wh_id]['date_planned'] = intermediate_option['date_planned']
                        base_option['sub_options'][b_wh_id]['date_planned'] = base_option['date_planned']
                elif 'sub_options' in base_option and 'sub_options' not in intermediate_option:
                    if wh_id not in base_option['sub_options']:
                        base_option['sub_options'][wh_id] = {
                            'product_ids': intermediate_option['products'].ids,
                            'product_skus': intermediate_option['products'].mapped('default_code'),
                        }
                        if base_option.get('date_planned'):
                            base_option['sub_options'][wh_id]['date_planned'] = intermediate_option['date_planned']
                    else:
                        base_option['sub_options'][wh_id]['product_ids'] += intermediate_option['products'].ids
                        base_option['sub_options'][wh_id]['product_skus'] += intermediate_option['products'].mapped(
                            'default_code')
                        if base_option.get('date_planned'):
                            if intermediate_option['date_planned'] > base_option['sub_options'][wh_id]['date_planned']:
                                base_option['sub_options'][wh_id]['date_planned'] = intermediate_option['date_planned']
                elif 'sub_options' in intermediate_option and 'sub_options' in base_option:
                    # Both have sub_options, merge
                    for o_wh_id, option in intermediate_option['sub_options'].items():
                        if o_wh_id not in base_option['sub_options']:
                            base_option['sub_options'][o_wh_id] = option
                        else:
                            base_option['sub_options'][o_wh_id]['product_ids'] += option['product_ids']
                            base_option['sub_options'][o_wh_id]['product_skus'] += option['product_skus']
                        if base_option.get('date_planned'):
                            if option['date_planned'] > base_option['sub_options'][o_wh_id]['date_planned']:
                                base_option['sub_options'][o_wh_id]['date_planned'] = intermediate_option[
                                    'date_planned']
                else:
                    # intermediate_option has sub_options but base_option doesn't
                    base_option['sub_options'] = {
                        b_wh_id: {
                            'product_ids': base_option['products'].ids,
                            'product_skus': base_option['products'].mapped('default_code'),
                        }
                    }
                    if base_option.get('date_planned'):
                        base_option['sub_options'][b_wh_id]['date_planned'] = base_option['date_planned']
                    for o_wh_id, option in intermediate_option['sub_options'].items():
                        if o_wh_id not in base_option['sub_options']:
                            base_option['sub_options'][o_wh_id] = option
                        else:
                            base_option['sub_options'][o_wh_id]['product_ids'] += option['product_ids']
                            base_option['sub_options'][o_wh_id]['product_skus'] += option['product_skus']
                        if base_option.get('date_planned'):
                            if option['date_planned'] > base_option['sub_options'][o_wh_id]['date_planned']:
                                base_option['sub_options'][o_wh_id]['date_planned'] = intermediate_option[
                                    'date_planned']

        del base_option['products']
        _logger.error('  returning: ' + str(base_option))
        order_fake.warehouse_id = self.get_warehouses(warehouse_id=base_option['warehouse_id'])
        return base_option

    # override to use farthest warehouse for last selection
    def _generate_base_option(self, order_fake, policy_group):
        flag_force_closest = False
        warehouse_domain = False
        if 'policy' in policy_group:
            policy = policy_group['policy']
            flag_force_closest = policy.always_closest_warehouse
            warehouse_domain = policy.warehouse_filter_id.domain
            # Need to look at warehouse filter.
            # Eventually need to look at shipping filter....

        warehouses = self.get_warehouses(domain=warehouse_domain)
        if flag_force_closest:
            warehouses = self._find_closest_warehouse_by_partner(warehouses, order_fake.partner_shipping_id)
        product_stock = self._fetch_product_stock(warehouses, policy_group['products'])
        sub_options = {}
        wh_date_planning = {}

        p_len = len(policy_group['products'])
        full_candidates = set()
        partial_candidates = set()
        for wh_id, stock in product_stock.items():
            available = sum(1 for p_id, p_vals in stock.items() if self._is_in_stock(p_vals, policy_group['buy_qty'][p_id]))
            if available == p_len:
                full_candidates.add(wh_id)
            elif available > 0:
                partial_candidates.add(wh_id)

        if full_candidates:
            if len(full_candidates) == 1:
                warehouse = warehouses.filtered(lambda wh: wh.id in full_candidates)
            else:
                warehouse = self._find_closest_warehouse_by_partner(
                    warehouses.filtered(lambda wh: wh.id in full_candidates), order_fake.partner_shipping_id)
            date_planned = self._next_warehouse_shipping_date(warehouse)
            #order_fake.warehouse_id = warehouse
            return {'warehouse_id': warehouse.id, 'date_planned': date_planned}

        _logger.error('      partial_candidates: ' + str(partial_candidates))
        if partial_candidates:
            _logger.error('      using...')
            if len(partial_candidates) == 1:
                warehouse = warehouses.filtered(lambda wh: wh.id in partial_candidates)
                #order_fake.warehouse_id = warehouse
                return {'warehouse_id': warehouse.id}

            sorted_warehouses = self._sort_warehouses_by_partner(
                warehouses.filtered(lambda wh: wh.id in partial_candidates), order_fake.partner_shipping_id)
            _logger.error('      sorted_warehouses: ' + str(sorted_warehouses) + ' warehouses: ' + str(warehouses))
            primary_wh = sorted_warehouses[0]  # partial_candidates means there is at least one warehouse
            primary_wh_date_planned = self._next_warehouse_shipping_date(primary_wh)
            wh_date_planning[primary_wh.id] = primary_wh_date_planned
            for wh in sorted_warehouses:
                _logger.error('      wh: ' + str(wh) + ' buy_qty: ' + str(policy_group['buy_qty']))
                if not policy_group['buy_qty']:
                    continue
                stock = product_stock[wh.id]
                for p_id, p_vals in stock.items():
                    _logger.error('      p_id: ' + str(p_id) + ' p_vals: ' + str(p_vals))
                    if p_id in policy_group['buy_qty'] and self._is_in_stock(p_vals, policy_group['buy_qty'][p_id]):
                        if wh.id not in sub_options:
                            sub_options[wh.id] = {
                                'date_planned': self._next_warehouse_shipping_date(wh),
                                'product_ids': [],
                                'product_skus': [],
                            }
                        sub_options[wh.id]['product_ids'].append(p_id)
                        sub_options[wh.id]['product_skus'].append(p_vals['sku'])
                        _logger.error('        removing: ' + str(p_id))
                        del policy_group['buy_qty'][p_id]

            if not policy_group['buy_qty']:
                # item_details can fulfil all items.
                # this is good!!
                #order_fake.warehouse_id = primary_wh
                return {'warehouse_id': primary_wh.id, 'date_planned': primary_wh_date_planned,
                        'sub_options': sub_options}
            else:
                for p_id in policy_group['buy_qty']:
                    if wh.id not in sub_options:
                        sub_options[wh.id] = {
                            'date_planned': self._next_warehouse_shipping_date(wh),
                            'product_ids': [],
                            'product_skus': [],
                        }
                    sub_options[wh.id]['product_ids'].append(p_id)
                return {'warehouse_id': primary_wh.id, 'date_planned': primary_wh_date_planned,
                        'sub_options': sub_options}

            # warehouses cannot fulfil all requested items!!
            #order_fake.warehouse_id = primary_wh
            primary_wh = self._find_closest_warehouse_by_partner(warehouses, order_fake.partner_shipping_id, farthest=True)
            return {'warehouse_id': primary_wh.id}

        # nobody has stock!
        primary_wh = self._find_closest_warehouse_by_partner(warehouses, order_fake.partner_shipping_id, farthest=True)
        return {'warehouse_id': primary_wh.id}

    # override to pass farthest
    def _find_closest_warehouse_by_partner(self, warehouses, partner, farthest=False):
        if not partner.date_localization:
            partner.geo_localize()
        return self._find_closest_warehouse(warehouses, partner.partner_latitude, partner.partner_longitude, farthest=farthest)

    # override to reverse direction on farthest
    def _find_closest_warehouse(self, warehouses, latitude, longitude, farthest=False):
        if not warehouses:
            return warehouses
        distances = {distance(latitude, longitude, wh.partner_id.partner_latitude, wh.partner_id.partner_longitude): wh.id for wh in warehouses}
        wh_id = distances[min(distances)]
        if farthest:
            wh_id = distances[max(distances)]
        return warehouses.filtered(lambda wh: wh.id == wh_id)
