import json
import logging
import time
from datetime import datetime

from odoo.addons.shopify_ept.shopify.pyactiveresource.connection import ClientError

_logger = logging.getLogger("Shopify Product")

from odoo import models, fields, api, _
from odoo.addons.shopify_ept import shopify


class shopify_product_template_ept(models.Model):
    _inherit = "shopify.product.template.ept"

    # @api.multi
    def write(self, vals):
        res = super(shopify_product_template_ept, self).write(vals)

        if self.env.context.get('bypass_odoo_product'):
            return res

        shopify_instance_obj = self.env['shopify.instance.ept']
        us_instance = shopify_instance_obj.search([('country_id.code', '=', 'US'), ('country_id.name', '=', 'United States')], limit=1)
        ca_instance = shopify_instance_obj.search([('country_id.code', '=', 'CA'), ('country_id.name', '=', 'Canada')], limit=1)
        for template in self:
            odoo_template = template.product_tmpl_id
            us_instance and odoo_template and vals.get('check_product_stock') and odoo_template.with_context(bypass_shopify_product=True).write({'check_product_stock_us': vals.get('check_product_stock')})
            us_instance and odoo_template and vals.get('inventory_management') and odoo_template.with_context(bypass_shopify_product=True).write({'inventory_management_us': vals.get('inventory_management')})
            ca_instance and odoo_template and vals.get('check_product_stock') and odoo_template.with_context(bypass_shopify_product=True).with_context(bypass_shopify_product=True).write({'check_product_stock_ca': vals.get('check_product_stock')})
            ca_instance and odoo_template and vals.get('inventory_management') and odoo_template.with_context(bypass_shopify_product=True).write({'inventory_management_ca': vals.get('inventory_management')})
        return res

    @api.model
    def create(self, vals):
        res = super(shopify_product_template_ept, self).create(vals)
        shopify_instance_obj = self.env['shopify.instance.ept']
        us_instance = shopify_instance_obj.search([('country_id.code', '=', 'US'), ('country_id.name', '=', 'United States')], limit=1)
        ca_instance = shopify_instance_obj.search([('country_id.code', '=', 'CA'), ('country_id.name', '=', 'Canada')], limit=1)
        for template in self:
            odoo_template = template.product_tmpl_id
            us_instance and odoo_template and vals.get('check_product_stock') and odoo_template.write({'check_product_stock_us': vals.get('check_product_stock')})
            us_instance and odoo_template and vals.get('inventory_management') and odoo_template.write({'inventory_management_us': vals.get('inventory_management')})
            ca_instance and odoo_template and vals.get('check_product_stock') and odoo_template.write({'check_product_stock_ca': vals.get('check_product_stock')})
            ca_instance and odoo_template and vals.get('inventory_management') and odoo_template.write({'inventory_management_ca': vals.get('inventory_management')})
        return res

    # @api.model
    # def update_product_tracks_in_shopify(self, instance, templates):
    #     transaction_log_obj = self.env['shopify.transaction.log']
    #     instance.connect_in_shopify()
    #
    #     for template in templates:
    #         try:
    #             new_product = shopify.Product().find(template.shopify_tmpl_id)
    #         except:
    #             message = "Template %s not found in shopify When update Product" % (template.shopify_tmpl_id)
    #             log = transaction_log_obj.search([('shopify_instance_id', '=', instance.id), ('message', '=', message)])
    #             if not log:
    #                 transaction_log_obj.create(
    #                     {'message': message,
    #                      'mismatch_details': True,
    #                      'type': 'product',
    #                      'shopify_instance_id': instance.id
    #                      })
    #
    #             else:
    #                 log.write({'message': message})
    #
    #             continue
    #         new_product.id = template.shopify_tmpl_id
    #         variants = []
    #         for variant in template.shopify_product_ids:
    #             info = {}
    #             if variant.inventory_management == 'parent_product':
    #                 if template.inventory_management == 'shopify':
    #                     info.update({'id': variant.variant_id, 'inventory_management': 'shopify'})
    #                 else:
    #                     info.update({'id': variant.variant_id, 'inventory_management': None})
    #             elif variant.inventory_management == 'shopify':
    #                 info.update({'id': variant.variant_id, 'inventory_management': 'shopify'})
    #             else:
    #                 info.update({'id': variant.variant_id, 'inventory_management': None})
    #
    #             if variant.check_product_stock == 'parent_product':
    #                 if template.check_product_stock:
    #                     info.update({'id': variant.variant_id,'inventory_policy': 'continue'})
    #                 else:
    #                     info.update({'inventory_policy': 'deny'})
    #             elif variant.check_product_stock == 'continue':
    #                 info.update({
    #                     'id': variant.variant_id,'inventory_policy': 'continue'
    #                 })
    #             else:
    #                 info.update({
    #                     'id': variant.variant_id,'inventory_policy': 'deny'
    #                 })
    #
    #             variants.append(info)
    #         new_product.variants = variants
    #         result = new_product.save()
    #     return True

    @api.model
    def update_product_tracks_in_shopify(self, instance, templates):
        common_log_obj = self.env["common.log.book.ept"]
        common_log_line_obj = self.env['common.log.lines.ept']
        instance.connect_in_shopify()

        for template in templates:
            try:
                new_product = shopify.Product().find(template.shopify_tmpl_id)
            except:
                message = "Template %s not found in shopify When update Product" % (template.shopify_tmpl_id)
                model_id = common_log_line_obj.get_model_id(template._name)
                log_book_id = common_log_obj.create({"type": "export", "shopify_instance_id": instance.id if instance else False, "model_id": model_id})
                log = common_log_line_obj.search([("model_id", "=", model_id), ('message', '=', message), ('res_id', '=', int(template.shopify_tmpl_id))])
                if not log:
                    common_log_line_obj.create(
                        {"message": message,
                         "mismatch_details": True,
                         "model_id": model_id,
                         "log_book_id": log_book_id.id,
                         "res_id": int(template.shopify_tmpl_id),
                         })

                else:
                    log.write({'message': message})

                continue
            new_product.id = template.shopify_tmpl_id
            variants = []
            for variant in template.shopify_product_ids:
                info = {}
                if variant.inventory_management == 'parent_product':
                    if template.inventory_management == 'shopify':
                        info.update({'id': variant.variant_id, 'inventory_management': 'shopify'})
                    else:
                        info.update({'id': variant.variant_id, 'inventory_management': None})
                elif variant.inventory_management == 'shopify':
                    info.update({'id': variant.variant_id, 'inventory_management': 'shopify'})
                else:
                    info.update({'id': variant.variant_id, 'inventory_management': None})

                if variant.check_product_stock == 'parent_product':
                    if template.check_product_stock:
                        info.update({'id': variant.variant_id, 'inventory_policy': 'continue'})
                    else:
                        info.update({'inventory_policy': 'deny'})
                elif variant.check_product_stock == 'continue':
                    info.update({
                        'id': variant.variant_id, 'inventory_policy': 'continue'
                    })
                else:
                    info.update({
                        'id': variant.variant_id, 'inventory_policy': 'deny'
                    })

                variants.append(info)
            new_product.variants = variants
            result = new_product.save()
        return True


class shopify_product_product_ept(models.Model):
    _inherit = "shopify.product.product.ept"

    # @api.multi
    def write(self, vals):
        res = super(shopify_product_product_ept, self).write(vals)
        shopify_instance_obj = self.env['shopify.instance.ept']

        if self.env.context.get('bypass_odoo_product'):
            return res

        us_instance = shopify_instance_obj.search([('country_id.code', '=', 'US'), ('country_id.name', '=', 'United States')], limit=1)
        ca_instance = shopify_instance_obj.search([('country_id.code', '=', 'CA'), ('country_id.name', '=', 'Canada')], limit=1)
        for template in self:
            odoo_product = template.product_id
            us_instance and odoo_product and vals.get('check_product_stock') and odoo_product.with_context(bypass_shopify_product=True).write({'check_product_stock_us': vals.get('check_product_stock')})
            us_instance and odoo_product and vals.get('inventory_management') and odoo_product.with_context(bypass_shopify_product=True).write({'inventory_management_us': vals.get('inventory_management')})
            ca_instance and odoo_product and vals.get('check_product_stock') and odoo_product.with_context(bypass_shopify_product=True).write({'check_product_stock_ca': vals.get('check_product_stock')})
            ca_instance and odoo_product and vals.get('inventory_management') and odoo_product.with_context(bypass_shopify_product=True).write({'inventory_management_ca': vals.get('inventory_management')})
        return res

    @api.model
    def create(self, vals):
        res = super(shopify_product_product_ept, self).create(vals)
        shopify_instance_obj = self.env['shopify.instance.ept']
        us_instance = shopify_instance_obj.search([('country_id.code', '=', 'US'), ('country_id.name', '=', 'United States')], limit=1)
        ca_instance = shopify_instance_obj.search([('country_id.code', '=', 'CA'), ('country_id.name', '=', 'Canada')], limit=1)
        for template in self:
            odoo_product = template.product_id
            us_instance and odoo_product and vals.get('check_product_stock') and odoo_product.write({'check_product_stock_us': vals.get('check_product_stock')})
            us_instance and odoo_product and vals.get('inventory_management') and odoo_product.write({'inventory_management_us': vals.get('inventory_management')})
            ca_instance and odoo_product and vals.get('check_product_stock') and odoo_product.write({'check_product_stock_ca': vals.get('check_product_stock')})
            ca_instance and odoo_product and vals.get('inventory_management') and odoo_product.write({'inventory_management_ca': vals.get('inventory_management')})
        return res

    # Override the method to add the some arguments in 'compute_qty_for_export_stock' method.
    @api.model
    def export_stock_in_shopify(self, instance, product_ids):
        """
        Find products with below condition
            1. shopify_instance_id = instance.id
            2. exported_in_shopify = True
            3. product_id in products
        Find Shopify location for the particular instance
        Check export_stock_warehouse_ids is configured in location or not
        Get the total stock of the product with configured warehouses and update that stock in shopify location
        here we use InventoryLevel shopify API for export stock
        @author: Maulik Barad on Date 15-Sep-2020.
        """
        common_log_line_obj = self.env["common.log.lines.ept"]
        product_obj = self.env["product.product"]
        sale_order_obj = self.env["sale.order"]

        log_line_array = []
        model = "shopify.product.product.ept"
        model_id = common_log_line_obj.get_model_id(model)
        all_products = self.search_shopify_product_for_export_stock(instance, product_ids)

        if self._context.get('is_process_from_selected_product'):
            shopify_products = all_products
        else:
            if instance.shopify_last_date_update_stock:
                shopify_products = all_products.filtered(lambda x: not x.last_stock_update_date or
                                                                   x.last_stock_update_date <= instance.shopify_last_date_update_stock)
            else:
                shopify_products = all_products.filtered(lambda x: not x.last_stock_update_date)

        if not shopify_products:
            return False
        last_export_date = all_products[0].last_stock_update_date or datetime.now()

        if not shopify_products:
            return True

        instance.connect_in_shopify()
        location_ids = self.env["shopify.location.ept"].search([("instance_id", "=", instance.id)])
        if not location_ids:
            message = "Location not found for instance %s while update stock" % instance.name
            log_line_array = self.shopify_create_log(message, model_id, False, log_line_array)

        for location_id in location_ids:
            shopify_location_warehouse = location_id.export_stock_warehouse_ids or False
            if not shopify_location_warehouse:
                message = "No Warehouse found for Export Stock in Shopify Location: %s" % location_id.name
                log_line_array = self.shopify_create_log(message, model_id, False, log_line_array)
                continue

            odoo_product_ids = shopify_products.product_id.ids
            product_stock = self.check_stock(instance, odoo_product_ids, product_obj,
                                             location_id.export_stock_warehouse_ids)
            commit_count = 0
            for shopify_product in shopify_products:
                if commit_count == 50:
                    self._cr.commit()
                    commit_count = 0
                commit_count += 1
                odoo_product = shopify_product.product_id
                if odoo_product.detailed_type == "product":
                    if not shopify_product.inventory_item_id:
                        message = "Inventory Item Id did not found for Shopify Product Variant ID " \
                                  "%s with name %s for instance %s while Export stock" % (
                                      shopify_product.id, shopify_product.name, instance.name)
                        log_line_array = self.shopify_create_log(message, model_id, odoo_product, log_line_array)
                        continue

                    quantity = self.compute_qty_for_export_stock(product_stock, shopify_product, odoo_product, instance.shopify_warehouse_id.id)
                    try:
                        shopify.InventoryLevel.set(location_id.shopify_location_id, shopify_product.inventory_item_id,
                                                   int(quantity))
                    except ClientError as error:
                        if hasattr(error,
                                   "response") and error.response.code == 429 and error.response.msg == "Too Many Requests":
                            time.sleep(int(float(error.response.headers.get('Retry-After', 5))))
                            shopify.InventoryLevel.set(location_id.shopify_location_id,
                                                       shopify_product.inventory_item_id,
                                                       int(quantity))
                            continue
                        message = "Error while Export stock for Product ID: %s & Product Name: '%s' for instance:" \
                                  "'%s'\nError: %s\n%s" % (odoo_product.id, odoo_product.name, instance.name,
                                                           str(error.response.code) + " " + error.response.msg,
                                                           json.loads(error.response.body.decode()).get("errors")[0]
                                                           )
                        log_line_array = self.shopify_create_log(message, model_id, odoo_product, log_line_array)
                    except ResourceNotFound as error:
                        if hasattr(error, "response"):
                            message = "Error while Export stock for Product ID: %s & Product Name: '%s' for instance:" \
                                      "'%s'not found in Shopify store\nError: %s\n%s" % (odoo_product.id, odoo_product.name, instance.name,
                                                               str(error.response.code) + " " + error.response.msg,
                                                               json.loads(error.response.body.decode()).get("errors")[0]
                                                               )
                            log_line_array = self.shopify_create_log(message, model_id, odoo_product, log_line_array)
                    except Exception as error:
                        message = "Error while Export stock for Product ID: %s & Product Name: '%s' for instance: " \
                                  "'%s'\nError: %s" % (odoo_product.id, odoo_product.name, instance.name, str(error))
                        log_line_array = self.shopify_create_log(message, model_id, odoo_product, log_line_array)

                    if not self._context.get('is_process_from_selected_product'):
                        shopify_product.write({
                            'last_stock_update_date': last_export_date if not shopify_product.last_stock_update_date else datetime.now()})
        log_book_id = False
        if len(log_line_array) > 0:
            log_book_id = self.create_log_book(log_line_array, "export", instance)

        if log_book_id and instance.is_shopify_create_schedule:
            message = []
            count = 0
            for log_line in log_book_id.log_lines:
                count += 1
                if count <= 5:
                    message.append('<' + 'li' + '>' + log_line.message + '<' + '/' + 'li' + '>')
            if count >= 5:
                message.append(
                    '<' + 'p' + '>' + 'Please refer the logbook' + '  ' + log_book_id.name + '  ' + 'check it in more detail' + '<' + '/' + 'p' + '>')
            note = "\n".join(message)

            sale_order_obj.create_schedule_activity_against_logbook(log_book_id, log_book_id.log_lines, note)
        return all_products

    # Override the method
    def compute_qty_for_export_stock(self, product_stock, shopify_product, odoo_product, warehouse_id, stock_type='virtual_available'):
        bom_stock = 0.0
        try:
            quantity = product_stock.get(odoo_product.id, 0)
            incoming_stock = getattr(odoo_product, 'incoming_qty')
            _logger.info('product_stock %s', quantity)
            actual_stock = quantity - incoming_stock
            _logger.info('actual_stock %s', actual_stock)
            if odoo_product.bom_count:
                bom_stock = odoo_product.find_bom_product_possible_quantity(warehouse_id, stock_type) or 0.0
                _logger.info('bom_stock %s', bom_stock)
            actual_stock = actual_stock + bom_stock
            _logger.info('updated final stock %s', actual_stock)
            if shopify_product.fix_stock_type == 'fix':
                if shopify_product.fix_stock_value < actual_stock:
                    actual_stock = shopify_product.fix_stock_value
            elif shopify_product.fix_stock_type == 'percentage':
                percentage_stock = int((actual_stock * shopify_product.fix_stock_value) / 100.0)
                if percentage_stock < actual_stock:
                    actual_stock = percentage_stock

            return actual_stock - 1
        except Exception as e:
            raise Warning(e)

