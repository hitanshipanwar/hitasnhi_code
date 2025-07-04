import json
from datetime import datetime
from odoo import api, models
from odoo.addons.shopify_ept import shopify
from odoo.addons.shopify_ept.shopify.pyactiveresource.connection import ClientError, ResourceNotFound

import logging
_logger = logging.getLogger(__name__)


class shopify_product_product_ept(models.Model):
    _inherit = "shopify.product.product.ept"
    
    # Copied from shopify_ept.models.shopify_product_ept
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
        debug_logging = self.env['ir.config_parameter'].sudo().get_param('shopify.log_inventory_export', default=False)

        log_line_array = []
        model = "shopify.product.product.ept"
        model_id = common_log_line_obj.get_model_id(model)
        shopify_products = self.search_shopify_product_for_export_stock(instance, product_ids)

        # 6/7/2023
        # Why filter products by date again?
        # The wizard already searches for products with stock moves since the 
        # last update and search_shopify_product_for_export_stock above filters
        # to products that have been exported. No need to filter again, and it 
        # introduces unexpected behavior when the export takes a long time
        # (i.e.) next time the export runs, many products from that export 
        # will be filtered out and won't get exported here
        
        # if self._context.get('is_process_from_selected_product'):
        #     shopify_products = all_products
        # else:
        #     if instance.shopify_last_date_update_stock:
        #         shopify_products = all_products.filtered(lambda x: not x.last_stock_update_date or
        #                                                            x.last_stock_update_date <= instance.shopify_last_date_update_stock)
        #     else:
        #         shopify_products = all_products.filtered(lambda x: not x.last_stock_update_date)

        if not shopify_products:
            return False

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
            _logger.warning('product_stock:')
            _logger.warning(str(product_stock))
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

                    quantity = self.compute_qty_for_export_stock(product_stock, shopify_product, odoo_product)
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
                        else:
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

                    shopify_product.write({
                                'last_stock_update_date': datetime.now()})
                    if debug_logging:
                        message = "Manual Export: "
                        if not self._context.get('is_process_from_selected_product'):
                            message = "Scheduled Export: "
                        message += "Exported quantity %s for product %s" % (int(quantity), odoo_product.display_name)
                        log_line_array = self.shopify_create_log(message, model_id, odoo_product, log_line_array) 
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
        return shopify_products.filtered('last_stock_update_date').sorted('last_stock_update_date')
