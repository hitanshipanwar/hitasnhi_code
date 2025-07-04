# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, _, api
from odoo.exceptions import UserError

import logging

_logger = logging.getLogger(__name__)

class SaleOrder(models.Model):
    _inherit = 'sale.order'
    
    state = fields.Selection(selection_add=[('draft_so', 'Draft SO'), ('sale',)])
    partner_invoice_id = fields.Many2one(states={'draft': [('readonly', False)], 'sent': [('readonly', False)], 'sale': [('readonly', False)], 'draft_so': [('readonly', False)]})
    partner_shipping_id = fields.Many2one(states={'draft': [('readonly', False)], 'sent': [('readonly', False)], 'sale': [('readonly', False)], 'draft_so': [('readonly', False)]})
    
    def action_draft_so(self):
        for sale in self:
            if sale.state not in ['draft', 'sent']:
                raise UserError(_("Invalid Transactions"))
            sale.state = 'draft_so'
    
    def get_woo_unit_price(self, tax_included, quantity, subtotal, subtotal_tax):
        #Added as per Badger requirement. In sale order line, the unit price need to be always excl. tax. So the tax will be 
        #configured to use excl. amount by default in connector and we will set price as excl. tax from here 
        res = super(SaleOrder, self).get_woo_unit_price(tax_included, quantity, subtotal, subtotal_tax)
        actual_unit_price = subtotal / quantity
        return actual_unit_price
    
    def get_employee_name(self, order_line, sale_order_line):
        meta_data = order_line.get('meta_data')
        for line in meta_data:
            if line.get('key', '') == 'associate_employee_name':
                employee_name = line['value']
                sale_order_line.employee_name = employee_name
                break
        return True
    
    @api.model
    def create_woo_sale_order_lines(self, queue_line, order_data, tax_included, common_log_book_id, woo_taxes):
        """
        Checks for products and creates sale order lines.
        @param is_process_from_queue: If processing order data from Queue.
        @param common_log_book_id: Record of Log book.
        @param order_data: Data of order.
        @param queue_line: The queue line.
        @param woo_taxes: Dictionary of woo taxes.
        @param tax_included: If tax is included or not in price of product.
        @return: Created sale order lines.
        @author: Maulik Barad on Date 13-Nov-2019.
        Migrated by Maulik Barad on Date 07-Oct-2021.
        Overwritten by Prajul PT to add employee name in sale order line. Unable to inherit since sale line crated inside loop of the function
        """
        order_lines_list = []
        woo_instance = common_log_book_id.woo_instance_id
        for order_line in order_data.get("line_items"):
            taxes = []
            woo_product = self.find_or_create_woo_product(queue_line, order_line, common_log_book_id)
            if not woo_product:
                message = "Product [%s][%s] not found for Order %s" % (
                    order_line.get("sku"), order_line.get("name"), order_data.get('number'))
                self.create_woo_log_lines(message, common_log_book_id, queue_line)
                return False
            product = woo_product.product_id
            quantity = float(order_line.get("quantity"))

            actual_unit_price = self.get_woo_unit_price(tax_included, quantity, float(order_line.get("subtotal")),
                                                        float(order_line.get("subtotal_tax")))

            if woo_instance.apply_tax == "create_woo_tax":
                for tax in order_line.get("taxes"):
                    if not tax.get('total'):
                        continue
                    taxes.append(woo_taxes.get(tax['id']))

            order_line_id = self.create_woo_order_line(order_line.get("id"), product, order_line.get("quantity"),
                                                       actual_unit_price, taxes, tax_included, woo_instance)
            #Added by Prajul to add employee name in sale order line
            self.get_employee_name(order_line, order_line_id)
            #End
            order_lines_list.append(order_line_id)

            self.woo_create_discount_line(order_line, tax_included, woo_instance, taxes, order_line_id)
            _logger.info("Sale order line is created for order %s.", self.name)
        return order_lines_list
    
    def prepare_woo_order_vals(self, order_data, woo_instance, partner, billing_partner, shipping_partner,
                               workflow_config):
        result = super(SaleOrder, self).prepare_woo_order_vals(order_data, woo_instance, partner, billing_partner, shipping_partner,
                                                               workflow_config)
        result['state'] = 'draft_so'
        # Todo[Dhaval]: set purchase_order_no in client_order_ref
        purchase_order_no = None
        for meta_data in order_data.get("meta_data"):
            if meta_data.get('key', '') == 'purchase_order_no':
                purchase_order_no = meta_data['value']
        result['client_order_ref'] = purchase_order_no
        return result
    
    def create_woo_shipping_line(self, order_data, tax_included, woo_taxes):
        res = super(SaleOrder, self).create_woo_shipping_line(order_data, False, woo_taxes)
        return res


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'
    
    def _prepare_procurement_values(self, group_id=False):
        """ Prepare specific key for moves or other components that will be created from a stock rule
        comming from a sale order line. This method could be override in order to add other custom key that could
        be used in move/po creation.
        """
        values = super(SaleOrderLine, self)._prepare_procurement_values(group_id)
        values.update({'employee_name': self.employee_name})
        return values

