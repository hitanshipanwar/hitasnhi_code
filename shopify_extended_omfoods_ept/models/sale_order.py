from odoo import models,api,fields
from odoo.addons.shopify_ept import shopify
from operator import itemgetter
from odoo.tools import float_round

class SaleOrder(models.Model):
    _inherit="sale.order"
    
    # @api.model
    # def get_tax_id_ept(self,instance,order_line,tax_included):
    #     tax_id=[]
    #     taxes=[]
    #     for tax in order_line:
    #         price = float(tax.get('price',0.0))
    #         if price <=0:
    #             continue
    #         rate=float(tax.get('rate',0.0))
    #         rate = rate*100
    #         if rate!=0.0:
    #             acctax_id = self.env['account.tax'].search([('price_include','=',tax_included),('type_tax_use', '=', 'sale'), ('amount', '=', rate),('company_id','=',instance.warehouse_id.company_id.id)],limit=1)
    #             if not acctax_id:
    #                 acctax_id = self.createAccountTax(rate,tax_included,instance.warehouse_id.company_id,tax.get('title'))
    #                 if acctax_id:
    #                     transaction_log_obj=self.env["shopify.transaction.log"]
    #                     message="""Tax was not found in ERP ||
    #                     Automatic Created Tax,%s ||
    #                     tax rate  %s ||
    #                     Company %s"""%(acctax_id.name,rate,instance.company_id.name)
    #                     transaction_log_obj.create(
    #                                                 {'message':message,
    #                                                  'mismatch_details':True,
    #                                                  'type':'sales',
    #                                                  'shopify_instance_id':instance.id
    #                                                 })
    #             if acctax_id:
    #                 taxes.append(acctax_id.id)
    #     if taxes:
    #         tax_id = [(6, 0, taxes)]
    #
    #     return tax_id

    #Override the base method
    @api.model
    def shopify_get_tax_id_ept(self, instance, tax_lines, tax_included):
        tax_id = []
        taxes = []
        company = instance.shopify_warehouse_id.company_id
        for tax in tax_lines:
            rate = float(tax.get("rate", 0.0))
            price = float(tax.get('price', 0.0))
            title = tax.get("title")
            rate = rate * 100
            if rate != 0.0 and price != 0.0:
                if tax_included:
                    name = "%s_(%s %s included)_%s" % (title, str(rate), "%", company.name)
                else:
                    name = "%s_(%s %s excluded)_%s" % (title, str(rate), "%", company.name)
                tax_id = self.env["account.tax"].search([("price_include", "=", tax_included),
                                                         ("type_tax_use", "=", "sale"), ("amount", "=", rate),
                                                         ("name", "=", name), ("company_id", "=", company.id)], limit=1)
                if not tax_id:
                    tax_id = self.sudo().shopify_create_account_tax(instance, rate, tax_included, company, name)
                if tax_id:
                    taxes.append(tax_id.id)
        if taxes:
            tax_id = [(6, 0, taxes)]
        return tax_id
    
    # @api.model
    # def update_order_status(self,instance):
    #     move_line_obj = self.env['stock.move.line']
    #     transaction_log_obj=self.env["shopify.transaction.log"]
    #     log = False
    #     instances=[]
    #     if not instance:
    #         instances=self.env['shopify.instance.ept'].search([('order_auto_import','=',True),('state','=','confirmed')])
    #     else:
    #         instances.append(instance)
    #     for instance in instances:
    #         instance.connect_in_shopify()
    #         sales_orders = self.search([('warehouse_id','=',instance.warehouse_id.id),
    #                                                      ('shopify_order_id','!=',False),
    #                                                      ('shopify_instance_id','=',instance.id),
    #                                                      ('updated_in_shopify','=',False)],order='date_order')
    #
    #         for sale_order in sales_orders:
    #             order = shopify.Order.find(sale_order.shopify_order_id)
    #             for picking in sale_order.picking_ids:
    #                 """Here We Take only done picking and  updated in shopify false"""
    #                 if picking.updated_in_shopify or picking.state!='done' or picking.picking_type_code == 'internal':
    #                     continue
    #
    #                 line_items={}
    #                 shopify_line_id=False
    #                 list_of_tracking_number=[]
    #                 tracking_numbers=[]
    #                 carrier_name=picking.carrier_id and picking.carrier_id.shopify_code  or ''
    #                 if not carrier_name:
    #                     carrier_name=picking.carrier_id and picking.carrier_id.name or ''
    #                 for move in picking.move_lines:
    #                     if move.sale_line_id and move.sale_line_id.shopify_line_id:
    #                         shopify_line_id=move.sale_line_id.shopify_line_id
    #
    #                     """Create Package for the each parcel"""
    #                     move_line = move_line_obj.search([('move_id','=',move.id),('product_id','=',move.product_id.id)],limit=1)
    #                     tracking_no=False
    #                     if sale_order.shopify_instance_id.multiple_tracking_number:
    #                         if move_line.result_package_id.tracking_no:
    #                             tracking_no=move_line.result_package_id.tracking_no
    #                         if (move_line.package_id and move_line.package_id.tracking_no):
    #                             tracking_no=move_line.package_id.tracking_no
    #                     else:
    #                         tracking_no = picking.carrier_tracking_ref or ''
    #
    #                     list_of_tracking_number.append(tracking_no)
    #                     product_qty=move_line.qty_done or 0.0
    #                     product_qty=int(product_qty)
    #                     if shopify_line_id in line_items:
    #                         if 'tracking_no' in line_items.get(shopify_line_id):
    #                             quantity=line_items.get(shopify_line_id).get('quantity')
    #                             quantity=quantity+product_qty
    #                             line_items.get(shopify_line_id).update({'quantity':quantity})
    #                             if tracking_no not in line_items.get(shopify_line_id).get('tracking_no'):
    #                                 line_items.get(shopify_line_id).get('tracking_no').append(tracking_no)
    #                         else:
    #                             line_items.get(shopify_line_id).update({'tracking_no':[]})
    #                             line_items.get(shopify_line_id).update({'quantity':product_qty})
    #                             line_items.get(shopify_line_id).get('tracking_no').append(tracking_no)
    #                     else:
    #                         line_items.update({shopify_line_id:{}})
    #                         line_items.get(shopify_line_id).update({'tracking_no':[]})
    #                         line_items.get(shopify_line_id).update({'quantity':product_qty})
    #                         line_items.get(shopify_line_id).get('tracking_no').append(tracking_no)
    #
    #                 update_lines=[]
    #                 for sale_line_id in line_items:
    #                     tracking_numbers+=line_items.get(sale_line_id).get('tracking_no')
    #                     update_lines.append({'id':sale_line_id,'quantity':line_items.get(sale_line_id).get('quantity')})
    #                 if not update_lines:
    #                     if tracking_no:
    #                         message="No lines found for update order status for %s"%(picking.name)
    #                         log=transaction_log_obj.search([('shopify_instance_id','=',instance.id),('message','=',message)])
    #                         if not log:
    #                             transaction_log_obj.create(
    #                                                         {'message':message,
    #                                                          'mismatch_details':True,
    #                                                          'type':'sales',
    #                                                          'shopify_instance_id':instance.id
    #                                                         })
    #                     continue
    #                 try:
    #                     shopify_location_id = sale_order.shopify_location_id or False
    #                     if not shopify_location_id:
    #                         location_id=self.env['shopify.location.ept'].search([('is_primary_location','=',True),('instance_id','=',instance.id)])
    #                         shopify_location_id = location_id.shopify_location_id or False
    #                         if not location_id:
    #                             message = "Primary Location not found for instance %s while Update order status" % (instance.name)
    #                             if not log:
    #                                 transaction_log_obj.create(
    #                                     {'message': message,
    #                                      'mismatch_details': True,
    #                                      'type': 'stock',
    #                                      'shopify_instance_id': instance.id
    #                                      })
    #                             continue
    #                     new_fulfillment = shopify.Fulfillment({'order_id':order.id,'location_id':shopify_location_id,'tracking_numbers':list(set(tracking_numbers)),'tracking_company':carrier_name,'line_items':update_lines})
    #                     new_fulfillment.save()
    #                 except Exception as e:
    #                     raise Warning(e)
    #                 picking.write({'updated_in_shopify':True})
    #     self.closed_at(instances)
    #     return True

    # @api.model
    # def create_sale_order_line(self, line, product, quantity, name, order_id, price,
    #                            order_response, is_shipping=False,
    #                            previous_line=False,
    #                            is_discount=False
    #                            ):
    #     sale_order_line_obj = self.env['sale.order.line']
    #
    #     uom_id = product and product.uom_id and product.uom_id.id or False
    #     line_vals = {
    #         'product_id': product and product.ids[0] or False,
    #         'order_id': order_id.id,
    #         'company_id': order_id.company_id.id,
    #         'product_uom': uom_id,
    #         'name': name,
    #         'price_unit': price,
    #         'order_qty': quantity,
    #     }
    #     order_line_vals = sale_order_line_obj.create_sale_order_line_ept(line_vals)
    #     if order_id.shopify_instance_id.apply_tax_in_order == 'create_shopify_tax':
    #         taxes_included = order_response.get('taxes_included') or False
    #         new_order_line_without_tax = {}
    #         tax_ids = []
    #         if line and line.get('tax_lines'):
    #             if line.get('taxable'):
    #                 # This is used for when the one product is taxable and another product is not
    #                 # taxable
    #                 tax_ids = self.shopify_get_tax_id_ept(order_id.shopify_instance_id, line.get('tax_lines'),
    #                                               taxes_included)
    #             if is_shipping:
    #                 # In the Shopify store there is configuration regarding tax is applicable on shipping or not, if applicable then this use.
    #                 tax_ids = self.shopify_get_tax_id_ept(order_id.shopify_instance_id,
    #                                               line.get('tax_lines'),
    #                                               taxes_included)
    #                 order_line = line.get('tax_lines')
    #                 tax_price = list(map(itemgetter('price'), order_line))
    #                 # tax_rate = list(map(itemgetter('rate'), order_line))
    #                 tax_rate = [x['rate'] for x in order_line if x['price'] != '0.00']
    #                 price_addition = list(map(float, tax_price))
    #                 rate_addition = list(map(float, tax_rate))
    #                 total_tax_price = float_round(sum(price_addition), precision_digits=2)
    #                 total_tax = total_tax_price and sum(rate_addition) * 100 or 0.0
    #                 total_tax_amount_to_apply = total_tax and float_round((total_tax_price / (total_tax / 100)), precision_digits=2) or float(price)
    #                 if total_tax_amount_to_apply == float(price):
    #                     pass
    #                 else:
    #                     order_line_vals.update({
    #                         'price_unit': total_tax_amount_to_apply,
    #                         })
    #                     new_order_line_without_tax = order_line_vals.copy()
    #                     new_order_line_without_tax.update({
    #                         'price_unit': float(price) - total_tax_amount_to_apply,
    #                         'tax_id': False,
    #                         'is_delivery': is_shipping,
    #                         })
    #         elif not line:
    #             if order_id.shopify_instance_id.add_discount_tax:
    #                 tax_ids = self.shopify_get_tax_id_ept(order_id.shopify_instance_id,
    #                                               order_response.get('tax_lines'),
    #                                               taxes_included)
    #         order_line_vals["tax_id"] = tax_ids
    #         # When the one order with two products one product with tax and another product
    #         # without tax and apply the discount on order that time not apply tax on discount
    #         # which is
    #         if is_discount and not previous_line.tax_id:
    #             order_line_vals["tax_id"] = []
    #     else:
    #         if is_shipping and not line.get("tax_lines", []):
    #             order_line_vals["tax_id"] = []
    #     if is_discount:
    #         order_line_vals["name"] = 'Discount for ' + str(name)
    #         if order_id.shopify_instance_id.apply_tax_in_order == 'odoo_tax' and is_discount:
    #             order_line_vals["tax_id"] = previous_line.tax_id
    #
    #     order_line_vals.update({
    #         'shopify_line_id': line.get('id'),
    #         'is_delivery': is_shipping
    #     })
    #     order_line = sale_order_line_obj.with_context({'round': False}).create(order_line_vals)
    #     if new_order_line_without_tax:
    #         sale_order_line_obj.with_context({'round': False}).create(new_order_line_without_tax)
    #     return order_line

    #Override the base method to pass argument in 'shopify_set_tax_in_sale_order_line' method
    def shopify_create_sale_order_line(self, line, product, quantity, product_name, price,
                                       order_response, is_shipping=False, previous_line=False,
                                       is_discount=False):
        sale_order_line_obj = self.env["sale.order.line"]
        instance = self.shopify_instance_id
        line_vals = self.prepare_vals_for_sale_order_line(product, product_name, price, quantity)
        order_line_vals = sale_order_line_obj.create_sale_order_line_ept(line_vals)
        order_line_vals = self.shopify_set_tax_in_sale_order_line(instance, line, order_response, is_shipping,
                                                                  is_discount, previous_line, order_line_vals, price)
        if is_discount:
            order_line_vals["name"] = "Discount for " + str(product_name)
            if instance.apply_tax_in_order == "odoo_tax" and is_discount:
                order_line_vals["tax_id"] = previous_line.tax_id

        order_line_vals.update({
            "shopify_line_id": line.get("id"),
            "is_delivery": is_shipping,
        })
        order_line = sale_order_line_obj.create(order_line_vals)
        order_line.with_context(round=False)._compute_amount()
        return order_line

    #Override the base method
    def shopify_set_tax_in_sale_order_line(self, instance, line, order_response, is_shipping, is_discount,
                                           previous_line, order_line_vals, price):
        sale_order_line_obj = self.env["sale.order.line"]
        if instance.apply_tax_in_order == "create_shopify_tax":
            taxes_included = order_response.get("taxes_included") or False
            tax_ids = []
            new_order_line_without_tax = {}
            if line and line.get("tax_lines"):
                if line.get("taxable"):
                    # This is used for when the one product is taxable and another product is not
                    # taxable
                    tax_ids = self.shopify_get_tax_id_ept(instance,
                                                          line.get("tax_lines"),
                                                          taxes_included)
                if is_shipping:
                    # In the Shopify store there is configuration regarding tax is applicable on shipping or not,
                    # if applicable then this use.
                    tax_ids = self.shopify_get_tax_id_ept(instance,
                                                          line.get("tax_lines"),
                                                          taxes_included)
                    order_line = line.get('tax_lines')
                    tax_price = list(map(itemgetter('price'), order_line))
                    # tax_rate = list(map(itemgetter('rate'), order_line))
                    tax_rate = [x['rate'] for x in order_line if x['price'] != '0.00']
                    price_addition = list(map(float, tax_price))
                    rate_addition = list(map(float, tax_rate))
                    total_tax_price = float_round(sum(price_addition), precision_digits=2)
                    total_tax = total_tax_price and sum(rate_addition) * 100 or 0.0
                    total_tax_amount_to_apply = total_tax and float_round((total_tax_price / (total_tax / 100)), precision_digits=2) or float(price)
                    if total_tax_amount_to_apply == float(price):
                        pass
                    else:
                        order_line_vals.update({
                            'price_unit': total_tax_amount_to_apply,
                        })
                        new_order_line_without_tax = order_line_vals.copy()
                        new_order_line_without_tax.update({
                            'price_unit': float(price) - total_tax_amount_to_apply,
                            'tax_id': False,
                            'is_delivery': is_shipping,
                        })
            elif not line and previous_line:
                # Before modification, connector set order taxes on discount line but as per connector design,
                # we are creating discount line base on sale order line so it should apply sale order line taxes
                # in discount line not order taxes. It creates a problem while the customer is using multi taxes
                # in sale orders. so set the previous line taxes on the discount line.
                tax_ids = [(6, 0, previous_line.tax_id.ids)]
            order_line_vals["tax_id"] = tax_ids
            # When the one order with two products one product with tax and another product
            # without tax and apply the discount on order that time not apply tax on discount
            # which is
            if is_discount and not previous_line.tax_id:
                order_line_vals["tax_id"] = []
        if new_order_line_without_tax:
            sale_order_line_obj.with_context({'round': False}).create(new_order_line_without_tax)
        return order_line_vals
