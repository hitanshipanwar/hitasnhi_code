# -*- coding: utf-8 -*-
##############################################################################
# Copyright (c) 2015-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
# See LICENSE file for full copyright and licensing details.
# License URL : <https://store.webkul.com/license.html/>
##############################################################################
from odoo import http, SUPERUSER_ID, api
from odoo.http import request
from odoo.addons.shopify_odoo_bridge.shopify_bridge import Bridge

from logging import getLogger
_logger = getLogger(__name__)
import requests
from odoo import Command

# Webhook Implementation
class ChannelWebhook(http.Controller):

    def get_super_env(self):
        return api.Environment(request.cr, SUPERUSER_ID, request.context)

    # Extra Webhook can be used from extension, for other webhooks
    @http.route('/multichannel/<string:object>/webhook/<string:channel_id>', type="http", auth="public", csrf=False)
    def import_common_webhook(self, channel_id, object, **kwargs):
        if channel_id:
            try:
                channel_id = int(channel_id)
            except:
                _logger.error(f'Multi Channel Channel ID [{channel_id}] Can not be identified!')
                return
            env = self.get_super_env()
            channel = env['multi.channel.sale'].browse(channel_id)
            if channel and channel.state == 'validate' and channel.active:
                try:
                    event_data = request.httprequest.data
                    event_headers = request.httprequest.headers
                    if hasattr(channel, f'{channel.channel}_webhook_{object}_data'):
                        getattr(channel, f'{channel.channel}_webhook_{object}_data')(event_data, event_headers, **kwargs)
                except Exception as e:
                    _logger.error(f'Webhook Error: Can not import the Webhook data from {channel.channel} to Odoo.')

    # Order Create and Update Webhook
    @http.route('/multichannel/<string:type>/order/webhook/<string:channel_id>', type="http", auth="public", csrf=False)
    def import_order_webhook(self, type, channel_id, **kwargs):
        """
            It will get the orders webhook data and pass to extensions method to
            process it and returned order data will be created/updated in Odoo.
            params:
                channel_id(str): Channel Odoo ID
                type(str): 'create' or 'update'
        """
        _logger.info('************type: %s' % type)
        _logger.info('************channel_id: %s' % channel_id)
        if channel_id:
            request.update_context = dict(request.context)
            try:
                channel_id = int(channel_id)
            except:
                _logger.error(f'Multi Channel Channel ID [{channel_id}] Can not be identified!')
                return
            env = self.get_super_env()
            request.update_context['super_env'] = env
            channel = env['multi.channel.sale'].browse(channel_id)
            _logger.info(f'Calling {channel.channel} Realtime Webhook')
            if channel and channel.state == 'validate' and channel.active and (channel.is_create_order_webhook or channel.is_update_order_webhook):
                if channel.debug == 'enable':
                    _logger.info(f'RealTime Order {type} is Running for {channel.channel}: {channel.name}')
                try:
                    event_data = request.httprequest.data
                    event_headers = request.httprequest.headers
                    if type == 'create' and channel.is_create_order_webhook and hasattr(channel, f'{channel.channel}_order_webhook_data'):
                        response_data = getattr(channel, f'{channel.channel}_order_webhook_data')(event_data, event_headers, type, **kwargs)
                        message = self.create_order_data(channel, response_data)
                    elif type == 'update' and channel.is_update_order_webhook and hasattr(channel, f'{channel.channel}_order_webhook_data_update'):
                        response_data = getattr(channel, f'{channel.channel}_order_webhook_data_update')(event_data, event_headers, type, **kwargs)
                        message = self.update_order_data(channel, response_data)
                    else:
                        message = f'Webhook {type} Order is Not Active or Nothing to Import in RealTime from {channel.channel} To Odoo'
                    _logger.info(message)
                except Exception as e:
                    _logger.error('Error in RealTime Order Import: %r', e)
                    if channel.debug == 'enable':
                        _logger.error('Error: %r', e, exc_info=True)

    def create_order_data(self, channel, response_data):
        env = request.update_context.get('super_env') or self.get_super_env()
        message = 'Something Went Wrong: Error in Creating Order in Realtime'
        if response_data and response_data.get('store_id'):
            store_id = response_data.get('store_id')
            data = response_data.get('data')
            data = data if isinstance(data, list) else [data]
            if not channel.match_order_mappings(store_id):
                s_id, e_id, feed_id = env['order.feed'].with_context(
                    channel_id=channel)._create_feeds(data)
                if feed_id:
                    feed_id.message = "<br/><span class='text-info'>Realtime Order Imported Successfully</span>"
                    message = self.evaluate_order_webhook(channel, feed_id)
            else:
                message = 'Realtime Order Create: Nothing to Create, Order is Already Created in Odoo.'
        return message

    def update_order_data(self, channel, return_data):
        """
            It will decide what kind of update to perform according to
            the response of extension.(Status update or Complete Update)
        """
        env = request.update_context.get('super_env') or self.get_super_env()
        message = f'Nothing to Update in RealTime from {channel.channel} To Odoo'
        if return_data:
            store_id = return_data.get('store_id')
            data = return_data.get('data')
            if store_id and data:
                order_mapping = channel.match_order_mappings(store_id)
                feed = env['order.feed'].search([
                    ('channel_id','=', channel.id),
                    ('store_id','=', store_id)
                    ], limit=1)
                initial_feed_state = feed.state
                if not order_mapping and not feed:
                    return f"Error Update Order Webhook, Mapping and Feed is not exists for {channel.channel} Order, [StoreID: {store_id}]"
                data = data[0] if isinstance(data, list) else data
                raw_data = data.get('raw_data', {}) #Abhishek getting the raw data

                # Abhishek
                if return_data.get('update_case') == 'status_update' and data.get('financial_status') == 'paid':
                    shop_url = channel.url
                    access_token = channel.api_key
                    order_id_shopify = store_id
                    if shop_url and access_token:
                        url = f"{shop_url}/admin/api/2024-01/orders/{order_id_shopify}/transactions.json"
                        headers = {
                            "Content-Type": "application/json",
                            "X-Shopify-Access-Token": access_token
                        }
                        try:
                            response = requests.get(url, headers=headers)
                            if response.status_code == 200:
                                transactions = response.json().get('transactions', [])
                                _logger.info("transactions from update webhook************* %s", transactions)

                                authorize_txn = next(
                                    (txn for txn in transactions
                                     if not txn.get('parent_id') and txn.get('kind') == 'authorization'
                                     and txn.get('status') == 'success'),
                                    None
                                )

                                if not authorize_txn:
                                    authorize_txn = next(
                                        (txn for txn in transactions
                                         if not txn.get('parent_id') and txn.get('kind') == 'sale'
                                         and txn.get('status') == 'success'),
                                        None
                                    )

                                capture_txn = next(
                                    (txn for txn in transactions
                                     if txn.get('kind') == 'capture' and txn.get('status') == 'success'),
                                    None
                                )

                                refund_txn = next(
                                    (txn for txn in transactions
                                     if txn.get('kind') == 'refund' and txn.get('status') == 'success'),
                                    None
                                )

                                sale_order = order_mapping.order_name
                                if sale_order:
                                    updates = {}
                                    if authorize_txn:
                                        gateway = authorize_txn.get('gateway', '')
                                        payment_id = str(authorize_txn.get('payment_id', ''))
                                        if payment_id and gateway and gateway.startswith('authorize'):
                                            payment_id = payment_id[:-5]
                                        updates['txn_amount_shopify'] = float(authorize_txn.get('amount', 0.0))
                                        updates['txn_status'] = authorize_txn.get('status', '')
                                        updates['shopify_payment_id'] = payment_id

                                    if capture_txn:
                                        updates['txn_amount_shopify_capture'] = float(capture_txn.get('amount', 0.0))
                                        updates['txn_status_capture'] = capture_txn.get('status', '')
                                        updates['shopify_payment_id_capture'] = str(capture_txn.get('payment_id'))

                                    if refund_txn:
                                        updates['txn_amount_shopify_refund'] = float(refund_txn.get('amount', 0.0))
                                        updates['txn_status_refund'] = refund_txn.get('status', '')
                                        updates['shopify_payment_id_refund'] = str(refund_txn.get('receipt', {}).get('network_trans_id'))

                                    if updates:
                                        sale_order.write(updates)
                                        _logger.info(f"Transaction updated on Sale Order: {sale_order.name} -> {updates}")
                                        if sale_order.invoice_ids:
                                            for invoice in sale_order.invoice_ids:
                                                invoice_updates = {}
                                                for key in updates:
                                                    if hasattr(invoice, key):
                                                        invoice_updates[key] = updates[key]
                                                if invoice_updates:
                                                    invoice.write(invoice_updates)
                                                    _logger.info(f"Invoice {invoice.name} updated -> {invoice_updates}")
                            else:
                                _logger.warning(f"Shopify transaction fetch failed for Order {store_id}: {response.text}")
                        except Exception as e:
                            _logger.error(f"Error fetching Shopify transactions: {str(e)}")
                    else:
                        _logger.error("Missing Access Token or Shop url")

                # this is basically to check the fucntion whether any changes perform in the sale order.
                if return_data.get('update_case') == 'status_update':
                    if feed and raw_data:
                        self.sync_shopify_to_feed(env, feed, raw_data)

                    if order_mapping:
                        sale_order = order_mapping.order_name
                        if sale_order and raw_data:
                            self.sync_shopify_to_sale_order(env, sale_order, raw_data , channel)

                if return_data.get('update_case') == 'status_update' and order_mapping and data.get('order_state') and data.get('order_state') == 'fulfilled':
                    _logger.info("Creating Invoice When Fulfilled")
                    sale_order = order_mapping.order_name
                    _logger.info("sale_order ***************** %s", sale_order)
                    if sale_order and not sale_order.invoice_ids:
                        sale_order = order_mapping.order_name
                        invoices = sale_order._create_invoices()
                        if invoices:
                            invoices.action_post()

                # Abhishek
                if return_data.get('update_case') == 'status_update' and data.get('order_state'):
                    _logger.info("feed: %s" % feed)
                    if feed:
                        _logger.info("order_state: %s" % data.get('order_state'))
                        if data.get('order_state') == 'fulfilled':
                            res = request.env['channel.order.mappings'].sudo().search(
                                [
                                    ('channel_id', '=', feed.channel_id.id),
                                    ('store_order_id', '=', feed.store_id),
                                ]
                            )
                            _logger.info("order mapping id: %s" % res)
                            sale_order = res.order_name
                            _logger.info("sale_order: %s" % sale_order)
                            pickings = sale_order.picking_ids.sorted('id')
                            _logger.info("pickings: %s" % pickings)
                            for picking in pickings.sudo():
                                _logger.info("pickings: %s" % picking.state)
                                if picking.state != 'done':
                                    if picking.picking_type_id.sequence_code == 'PICK':
                                        for line in picking.move_ids_without_package:
                                            if line.quantity == 0 and line.product_uom_qty > 0:
                                                line.quantity = line.product_uom_qty
                                    picking.sudo().action_confirm()
                                    picking.sudo().action_assign()
                                    picking.sudo().button_validate()

                            # if not sale_order.invoice_ids:
                                # create_invoice = env['multi.channel.skeleton']._SetOdooOrderState(sale_order, feed.channel_id, 'Paid', data.get('payment_method', False))
                        
                        # Update Order Status With Feed
                        if not feed.order_state == data.get('order_state'):
                            write_data = {'order_state': data.get('order_state')}
                            if data.get('payment_method'):
                                write_data.update({'payment_method': data.get('payment_method')})
                            feed.write(write_data)
                            message = "Order Feed Status Updated Successfully in RealTime"
                            if initial_feed_state == 'done':
                                return self.evaluate_order_webhook(channel, feed)
                        else:
                            message = f"Order State [{feed.name}] is Already Updated in Feeds"
                    else:
                        # Update Order Status Without Feed
                        if not order_mapping.store_order_status == data.get('order_state'):
                            order = order_mapping.order_name
                            if order:
                                message = env['multi.channel.skeleton']._SetOdooOrderState(order, channel, data.get('order_status'), data.get('payment_method', False))
                        else:
                            message = "Order state is already Updated in Odoo"
                elif return_data.get('update_case') == 'complete_update':
                    # Order Complete Update or Create Feed
                    data = data if isinstance(data, list) else [data]
                    s_id, e_id, feed_id = env['order.feed'].with_context(
                    channel_id=channel)._create_feeds(data)
                    if feed_id and initial_feed_state == 'done':
                        return self.evaluate_order_webhook(channel, feed)
                    message = "Order Feed Created/Updated Successfully in RealTime"
                
                message += f' [StoreID: {store_id}]'
        return message

    def evaluate_order_webhook(self, channel, feed_id):
        message = "RealTime Order Feed Created/Updated Successfully, "
        if channel.auto_evaluate_feed:
            feed_id.with_context(from_webhook=True).import_items()
            if feed_id.state == 'done':
                message = "RealTime Order Evaluated Successfully, "
        return message + f'[Order Ref: {feed_id.name}, StoreID: {feed_id.store_id}]'

    def sync_shopify_to_feed(self, env, feed, raw_data):
        existing_lines = feed.line_ids

        # Map of existing feed lines using line_product_id
        existing_map = {
            line.line_product_id: line
            for line in existing_lines
            if line.line_product_id
        }

        # Collect valid Shopify line_product_ids
        shopify_ids_seen = set()
        new_lines = []

        # Inline tax processor
        def get_tax(item):
            tax_lines = item.get('tax_lines', [])
            if not tax_lines or all(str(t.get('price', '0')).strip() in ['0', '0.0', '0.00'] or float(t.get('price', 0)) == 0.0 for t in tax_lines):
                return []

            taxes = []
            for tax in tax_lines:
                try:
                    rate = float(tax.get('rate', 0.0)) * 100  # Convert 0.07 -> 7.0
                    title = tax.get('title') or 'Shopify Tax'
                    tax_id = env['account.tax'].search([
                        ('amount', '=', round(rate, 2)),
                        ('name', 'ilike', title),
                        ('type_tax_use', '=', 'sale')
                    ], limit=1)
                    if tax_id:
                        taxes.append(tax_id.id)
                    else:
                        _logger.warning(f"[SYNC] No tax found for rate={rate}% and title='{title}'")
                except Exception as e:
                    _logger.error(f"[SYNC] Tax parse error: {e}")
            return [(6, 0, taxes)] if taxes else []

        # Check and update if field value has changed
        def update_if_changed(line, data):
            updates = {}
            for field in ['line_price_unit', 'line_product_uom_qty', 'line_taxes']:
                if hasattr(line, field) and line[field] != data[field]:
                    updates[field] = data[field]
            if updates:
                line.write(updates)

        # === Product Lines ===
        for item in raw_data.get('line_items', []):
            product_id = item.get('product_id')
            if not product_id:
                continue
            unique_id = f"{product_id}"
            shopify_ids_seen.add(unique_id)

            sku = item.get('sku')
            product = env['product.product'].search([('default_code', '=', sku)], limit=1)
            if not product:
                continue

            line_data = {
                'line_name': item.get('name'),
                'line_product_id': unique_id,
                'line_variant_ids': item.get('variant_id'),
                'line_price_unit': float(item.get('price', 0.0)),
                'line_product_uom_qty': item.get('current_quantity', 1),
                'line_product_default_code': sku or '',
                'line_taxes': get_tax(item),
                'line_source': 'product',
            }

            existing_line = existing_map.get(unique_id)
            if existing_line:
                update_if_changed(existing_line, line_data)
            else:
                new_lines.append((0, 0, line_data))

        # === Shipping Lines ===
        for ship in raw_data.get('shipping_lines', []):
            unique_id = f"{ship.get('id')}"
            shopify_ids_seen.add(unique_id)

            line_data = {
                'line_name': f"Delivery: {ship.get('title')}",
                'line_product_id': unique_id,
                'line_price_unit': float(ship.get('price', 0.0)),
                'line_product_uom_qty': 1,
                'line_product_default_code': ship.get('code', ''),
                'line_taxes': get_tax(ship),
                'line_source': 'delivery',
            }

            existing_line = existing_map.get(unique_id)
            if existing_line:
                update_if_changed(existing_line, line_data)
            else:
                new_lines.append((0, 0, line_data))

        # === Discount Lines ===
        discount_sum = 0
        for discount in raw_data.get('discount_codes', []):
            code = discount.get('code')
            unique_id = f"{code}"
            shopify_ids_seen.add(unique_id)

            amount = float(discount.get('amount', 0.0))
            line_data = {
                'line_name': f"Discount: {code}",
                'line_product_id': unique_id,
                'line_price_unit': amount,
                'line_product_uom_qty': 1,
                'line_product_default_code': code,
                'line_taxes': [],
                'line_source': 'discount',
            }
            discount_sum += amount

            existing_line = existing_map.get(unique_id)
            if existing_line:
                update_if_changed(existing_line, line_data)
            else:
                new_lines.append((0, 0, line_data))

        # === Discount Rounding Adjustment (if any) ===
        current_total_discounts = float(raw_data.get('current_total_discounts', 0.0))
        if current_total_discounts and (current_total_discounts - discount_sum):
            diff_amt = round(current_total_discounts - discount_sum, 3)
            unique_id = 'Discount'
            shopify_ids_seen.add(unique_id)

            line_data = {
                'line_name': 'Discount Adjustment',
                'line_product_id': unique_id,
                'line_price_unit': diff_amt,
                'line_product_uom_qty': 1,
                'line_product_default_code': '',
                'line_taxes': [],
                'line_source': 'discount',
            }

            existing_line = existing_map.get(unique_id)
            if existing_line:
                update_if_changed(existing_line, line_data)
            else:
                new_lines.append((0, 0, line_data))

        # === Remove Outdated Lines ===
        for line_id, line in existing_map.items():
            if line_id not in shopify_ids_seen:
                line.unlink()

        # === Add New Lines to Feed ===
        if new_lines:
            feed.write({'line_ids': new_lines})
        else:
            _logger.info(f"[SYNC] No new lines to add")

    def sync_shopify_to_sale_order(self, env, sale_order, raw_data, channel):

        was_locked = sale_order.state in ['sale', 'done']
        if was_locked:
            sale_order.action_unlock()

        existing_lines = sale_order.order_line
        product_line_map = {line.product_id.id: line for line in existing_lines if line.product_id and line.product_id.default_code != 'delivery'}
        shipping_lines = [line for line in existing_lines if line.product_id.default_code == 'delivery']

        # Helper: Get tax_ids from Shopify tax_lines
        def get_tax_ids(item):
            tax_lines = item.get('tax_lines', [])
            tax_ids = []
            for tax in tax_lines:
                if float(tax.get('price', 0.0)) == 0:
                    continue
                title = tax.get("title", "").strip()
                rate = float(tax.get("rate", 0.0))
                tax_obj = env['account.tax'].search([
                    ('amount', '=', round(rate * 100, 2)),
                    ('name', 'ilike', title)
                ], limit=1)
                if tax_obj:
                    tax_ids.append(tax_obj.id)
                else:
                    _logger.warning(f"[TAX MISSING] ⚠️ {title} ({rate*100}%) not found.")
            return tax_ids

        # Update if something changed
        def update_if_changed(line, new_data):
            updates = {}
            if line.product_uom_qty != new_data['product_uom_qty']:
                updates['product_uom_qty'] = new_data['product_uom_qty']
            if float(line.price_unit) != float(new_data['price_unit']):
                updates['price_unit'] = new_data['price_unit']
            if set(line.tax_id.ids) != set(new_data['tax_id']):
                updates['tax_id'] = [(6, 0, new_data['tax_id'])]
            if updates:
                line.sudo().write(updates)
            else:
                _logger.info(f"[NO CHANGE] ✅ Line '{line.name}' is up to date")

        # -------------------------------
        # 1️⃣ SYNC PRODUCT LINES
        # -------------------------------
        seen_product_ids = set()
        new_lines = []

        for item in raw_data.get('line_items', []):
            qty = item.get('current_quantity', 1)
            if qty <= 0:
                continue

            product = None
            sku = item.get('sku')
            variant_id = item.get('variant_id')
            product_id_shopify = item.get('product_id')
            title = item.get('title', '')

            if sku:
                product = env['product.product'].search([('default_code', '=', sku)], limit=1)
            elif variant_id:
                mapping = env['channel.product.mappings'].search([
                    ('store_variant_id', '=', str(variant_id)), ('channel_id', '=', channel.id)
                ], limit=1)
                product = mapping.product_name if mapping else False
            elif product_id_shopify:
                mapping = env['channel.product.mappings'].search([
                    ('store_product_id', '=', str(product_id_shopify)), ('channel_id', '=', channel.id)
                ], limit=1)
                product = mapping.product_name if mapping else False
            else:
                product = env['product.product'].search([('name', 'ilike', title)], limit=1)

            if not product:
                continue

            seen_product_ids.add(product.id)
            tax_ids = get_tax_ids(item)
            line_data = {
                'name': item.get('name'),
                'product_id': product.id,
                'product_uom_qty': qty,
                'price_unit': float(item.get('price', 0.0)),
                'tax_id': tax_ids,
            }

            existing_line = product_line_map.get(product.id)
            if existing_line:
                update_if_changed(existing_line, line_data)
            else:
                new_lines.append((0, 0, {
                    'name': line_data['name'],
                    'product_id': line_data['product_id'],
                    'product_uom_qty': line_data['product_uom_qty'],
                    'price_unit': line_data['price_unit'],
                    'tax_id': [(6, 0, tax_ids)],
                }))

        for pid, line in product_line_map.items():
            if pid not in seen_product_ids:
                line.sudo().write({'product_uom_qty': 0})

        if new_lines:
            sale_order.sudo().write({'order_line': new_lines})

        # -------------------------------
        # 2️⃣ SYNC SHIPPING LINE
        # -------------------------------

        delivery_product = channel.delivery_product_id

        if not delivery_product:
            carrier_id = sale_order.carrier_id
            delivery_product = carrier_id.product_id if carrier_id else env['product.product'].search([
                ('default_code', '=', 'delivery')
            ], limit=1)

        if not delivery_product:
            delivery_product = env['product.product'].create({
                'name': 'Shipping',
                'type': 'service',
                'default_code': 'delivery',
                'sale_ok': True,
                'purchase_ok': False
            })

        # Step 0: Fetch Shopify and existing Odoo delivery lines
        shipping_lines_shopify = raw_data.get('shipping_lines', [])
        shipping_lines_odoo = [
            line for line in sale_order.order_line
            if line.is_delivery or (line.product_id.id == delivery_product.id)
        ]

        # Step 1: Map Shopify delivery lines by name
        shopify_delivery_titles = {
            f"Delivery: {s.get('title', 'Shipping')}": s
            for s in shipping_lines_shopify
        }
        existing_delivery_lines_by_name = {
            line.name: line
            for line in shipping_lines_odoo
        }

        # Step 2: Handle Shopify shipping lines one by one
        for shop_title, shop_data in shopify_delivery_titles.items():
            is_removed = shop_data.get('is_removed', False)
            existing_line = existing_delivery_lines_by_name.get(shop_title)

            if is_removed:
                if existing_line:
                    existing_line.sudo().write({'product_uom_qty': 0})
                else:
                    _logger.info(f"[SKIP] 🚫 Shopify removed '{shop_title}' and no such line exists in Odoo.")
                continue

            # Now, handle the active shipping lines
            new_price = float(shop_data.get('price', 0.0))
            new_tax_ids = get_tax_ids(shop_data)

            if existing_line:
                updates = {}
                if float(existing_line.price_unit) != new_price:
                    updates['price_unit'] = new_price
                if set(existing_line.tax_id.ids) != set(new_tax_ids):
                    updates['tax_id'] = [(6, 0, new_tax_ids)]
                if existing_line.product_uom_qty != 1:
                    updates['product_uom_qty'] = 1
                if not existing_line.is_delivery:
                    updates['is_delivery'] = True

                if updates:
                    existing_line.sudo().write(updates)
                else:
                    _logger.info(f"[NO CHANGE] ✅ Shipping line '{shop_title}' is already up-to-date.")
            else:
                sale_order.sudo().write({
                    'order_line': [(0, 0, {
                        'name': shop_title,
                        'product_id': delivery_product.id,
                        'product_uom_qty': 1,
                        'price_unit': new_price,
                        'tax_id': [(6, 0, new_tax_ids)],
                        'is_delivery': True,
                    })]
                })

        # -------------------------------
        # 3️⃣ SYNC DISCOUNT LINE (Handles All Discount Types)
        # -------------------------------

        discount_product = channel.discount_product_id or env['product.product'].search([
            ('default_code', '=', 'discount')
        ], limit=1)

        if not discount_product:
            discount_product = env['product.product'].create({
                'name': 'Discount',
                'type': 'service',
                'default_code': 'discount',
                'sale_ok': True,
                'purchase_ok': False
            })

        # Get existing Odoo discount line
        existing_discount_line = sale_order.order_line.filtered(lambda l: l.product_id.id == discount_product.id)

        # 1️⃣ Total from discount_codes (fixed or percentage)
        discount_sum = 0.0
        for discount in raw_data.get('discount_codes', []):
            amount = float(discount.get('amount', 0.0))
            discount_sum += amount

        # 2️⃣ Total from discount_allocations on line_items (product specific)
        allocation_sum = 0.0
        for item in raw_data.get("line_items", []):
            if item.get("current_quantity", 1) <= 0:
                continue
            for alloc in item.get("discount_allocations", []):
                allocation_sum += float(alloc.get("amount", 0.0))

        # 3️⃣ Final Total Shopify Discount (as per Shopify)
        shopify_total_discount = float(raw_data.get("current_total_discounts", 0.0))

        # 4️⃣ Calculate any rounding or missing diff (if Shopify gave total more than sum of parts)
        expected_discount = discount_sum + allocation_sum
        rounding_diff = round(shopify_total_discount - expected_discount, 2)

        # 5️⃣ Final Discount to Apply in Odoo
        final_discount = shopify_total_discount

        # Now reflect this as a single discount line in Odoo
        if final_discount > 0:
            if existing_discount_line:
                line = existing_discount_line[0]
                updates = {}
                if float(line.price_unit) != -final_discount:
                    updates['price_unit'] = -final_discount
                if line.product_uom_qty != 1:
                    updates['product_uom_qty'] = 1
                if updates:
                    line.sudo().write(updates)
                else:
                    _logger.info("[DISCOUNT] ✅ Discount line already up to date")
                # Clean extra discount lines if any
                if len(existing_discount_line) > 1:
                    existing_discount_line[1:].sudo().write({'product_uom_qty': 0})
            else:
                sale_order.sudo().write({
                    'order_line': [(0, 0, {
                        'name': f'Discount',
                        'product_id': discount_product.id,
                        'product_uom_qty': 1,
                        'price_unit': -final_discount,
                        'tax_id': [],
                    })]
                })
        else:
            _logger.info("[DISCOUNT] ♻️ No discount applicable")
            if existing_discount_line:
                _logger.info("[DISCOUNT] 🗑️ Removing existing discount line")
                existing_discount_line.sudo().write({'product_uom_qty': 0})


        # -------------------------------
        # 4️⃣ RELock if needed
        # -------------------------------
        if was_locked:
            sale_order.action_lock()
