from odoo import models, fields, api, _

import logging
_logger = logging.getLogger(__name__)

class productTemplate(models.Model):
    _inherit = "product.template"

    inventory_management_ca = fields.Selection(
        [('shopify', 'Shopify tracks this product Inventory'), ('Dont track Inventory', 'Dont track Inventory')],
        default='shopify', string='Inventory Management CA')

    check_product_stock_ca = fields.Boolean("Sale out of stock products for CA?", default=False)

    inventory_management_us = fields.Selection(
        [('shopify', 'Shopify tracks this product Inventory'), ('Dont track Inventory', 'Dont track Inventory')],
        default='shopify', string='Inventory Management US')

    check_product_stock_us = fields.Boolean("Sale out of stock products for US?", default=False)

    # @api.multi
    def write(self, vals):
        res = super(productTemplate, self).write(vals)
        shopify_instance_obj = self.env['shopify.instance.ept']
        shopify_product_template_obj = self.env['shopify.product.template.ept']

        if self.env.context.get('bypass_shopify_product'):
            return res

        if vals.get('inventory_management_us') or vals.get('check_product_stock_us'):
            us_instance = shopify_instance_obj.search([('country_id.code', '=', 'US'), ('country_id.name', '=', 'United States')], limit=1)
            for product_template in self:
                shopify_template = shopify_product_template_obj.search([('product_tmpl_id', '=', product_template.id), ('shopify_instance_id', '=', us_instance.id)], limit=1)
                shopify_template and not vals.get('inventory_management_us') and shopify_template.with_context(bypass_odoo_product=True).write({'check_product_stock': vals.get('check_product_stock_us')})
                shopify_template and vals.get('inventory_management_us') and shopify_template.with_context(bypass_odoo_product=True).write({'inventory_management': vals.get('inventory_management_us'), 'check_product_stock': vals.get('check_product_stock_us')})

        if vals.get('inventory_management_ca') or vals.get('check_product_stock_ca'):
            ca_instance = shopify_instance_obj.search([('country_id.code', '=', 'CA'), ('country_id.name', '=', 'Canada')], limit=1)
            for product_template in self:
                shopify_template = shopify_product_template_obj.search([('product_tmpl_id', '=', product_template.id), ('shopify_instance_id', '=', ca_instance.id)], limit=1)
                shopify_template and not vals.get('inventory_management_ca') and shopify_template.with_context(bypass_odoo_product=True).write({'check_product_stock': vals.get('check_product_stock_ca')})
                shopify_template and vals.get('inventory_management_ca') and shopify_template.with_context(bypass_odoo_product=True).write({'inventory_management': vals.get('inventory_management_ca'), 'check_product_stock': vals.get('check_product_stock_ca')})

        return res


class productProduct(models.Model):
    _inherit = "product.product"

    ca_minimum_stock = fields.Float('Minimum Stock level for CA')
    ca_low_stock = fields.Boolean('Low Stock in CA', store=True, compute='_calculate_low_stock_for_ca', search='_ca_low_stock')

    us_minimum_stock = fields.Float('Minimum Stock level for US')
    us_low_stock = fields.Boolean('Low Stock in US', store=True, compute='_calculate_low_stock_for_us', search='_us_low_stock')

    check_product_stock_us = fields.Selection(
        [('continue', 'Allow'), ('deny', 'Denied'), ('parent_product', 'Set as a Product Template')],
        default='parent_product', string="Sale out of stock products for Us?", help='If true than customers are allowed to place an order for the product variant when it is out of stock.')
    inventory_management_us = fields.Selection(
        [('shopify', 'Shopify tracks this product Inventory'), ('Dont track Inventory', 'Dont track Inventory'), ('parent_product', 'Set as a Product Template')],
        default='parent_product', string='Inventory Management US', help="If you select 'Shopify tracks this product Inventory' than shopify tracks this product inventory.if select 'Dont track Inventory' then after we can not update product stock from odoo")

    check_product_stock_ca = fields.Selection(
        [('continue', 'Allow'), ('deny', 'Denied'), ('parent_product', 'Set as a Product Template')],
        default='parent_product', string="Sale out of stock products for CA?", help='If true than customers are allowed to place an order for the product variant when it is out of stock.')
    inventory_management_ca = fields.Selection(
        [('shopify', 'Shopify tracks this product Inventory'), ('Dont track Inventory', 'Dont track Inventory'), ('parent_product', 'Set as a Product Template')],
        default='parent_product', string='Inventory Management CA', help="If you select 'Shopify tracks this product Inventory' than shopify tracks this product inventory.if select 'Dont track Inventory' then after we can not update product stock from odoo")

    def _ca_low_stock(self, operator, value):
        return [('ca_low_stock', operator, value)]

    def _us_low_stock(self, operator, value):
        return [('us_low_stock', operator, value)]

    @api.depends('ca_minimum_stock', 'virtual_available')
    def _calculate_low_stock_for_ca(self):
        company_id = self.env.user.company_id.id
        warehouse = self.env['stock.warehouse'].sudo().search([('code', '=', 'WH-CA')])
        if not warehouse:
            return
        for record in self:
            quantity = record.sudo().with_context(warehouse=warehouse.id).virtual_available
            if quantity < record.ca_minimum_stock:
                record.ca_low_stock = True
            elif quantity >= record.ca_minimum_stock:
                record.ca_low_stock = False

    @api.depends('us_minimum_stock', 'virtual_available')
    def _calculate_low_stock_for_us(self):
        company_id = self.env.user.company_id.id
        warehouse = self.env['stock.warehouse'].sudo().search([('code', '=', 'WH-US')])
        if not warehouse:
            return
        for record in self:
            quantity = record.sudo().with_context(warehouse=warehouse.id).virtual_available
            if quantity < record.us_minimum_stock:
                record.us_low_stock = True
            elif quantity >= record.us_minimum_stock:
                record.us_low_stock = False

    # @api.multi
    def write(self, vals):
        res = super(productProduct, self).write(vals)
        shopify_instance_obj = self.env['shopify.instance.ept']
        shopify_product_obj = self.env['shopify.product.product.ept']

        if self.env.context.get('bypass_shopify_product'):
            return res

        if vals.get('inventory_management_us') or vals.get('check_product_stock_us'):
            us_instance = shopify_instance_obj.search([('country_id.code', '=', 'US'), ('country_id.name', '=', 'United States')], limit=1)
            for product in self:
                shopify_product = shopify_product_obj.search([('product_id', '=', product.id), ('shopify_instance_id', '=', us_instance.id)], limit=1)
                shopify_product and vals.get('check_product_stock_us') and shopify_product.with_context(bypass_odoo_product=True).write({'check_product_stock': vals.get('check_product_stock_us')})
                shopify_product and vals.get('inventory_management_us') and shopify_product.with_context(bypass_odoo_product=True).write({'inventory_management': vals.get('inventory_management_us')})

        if vals.get('inventory_management_ca') or vals.get('check_product_stock_ca'):
            ca_instance = shopify_instance_obj.search([('country_id.code', '=', 'CA'), ('country_id.name', '=', 'Canada')], limit=1)
            for product in self:
                shopify_product = shopify_product_obj.search([('product_id', '=', product.id), ('shopify_instance_id', '=', ca_instance.id)], limit=1)
                shopify_product and vals.get('check_product_stock_ca') and shopify_product.with_context(bypass_odoo_product=True).write({'check_product_stock': vals.get('check_product_stock_ca')})
                shopify_product and vals.get('inventory_management_ca') and shopify_product.with_context(bypass_odoo_product=True).write({'inventory_management': vals.get('inventory_management_ca')})

        return res

    def get_set_product(self):
        try:
            bom_obj = self.env['mrp.bom']
            bom_point = bom_obj.sudo()._bom_find(product=self,company_id = self.env.user.company_id.id)
            _logger.info('bom_point %s', bom_point)
            from_uom = self.uom_id
            to_uom = bom_point.product_uom_id
            factor = from_uom._compute_quantity(1, to_uom) / bom_point.product_qty
            bom, lines = bom_point.explode(self, factor, picking_type=bom_point.picking_type_id)
            return lines
        except:
            return {}

    def find_bom_product_possible_quantity(self, warehouse_id, stock_type='virtual_available'):
        bom_lines = self.get_set_product()
        flag = True
        combination = 0
        for record in bom_lines:
            if record[0].product_id.type != 'product':
                continue
            _logger.info('record %s', record)
            bom_product_qty = record[1] and record[1].get('qty', 0)
            _logger.info('bom_product_qty %s', bom_product_qty)
            product = self.with_context(warehouse=warehouse_id).browse(record[0].product_id.id)
            product_stock = getattr(product, stock_type)
            _logger.info('product_stock bom_product_qty %s', product_stock)
            incoming_stock = getattr(product, 'incoming_qty')
            _logger.info('incoming_stock bom_product_qty %s', incoming_stock)
            actual_stock = product_stock - incoming_stock
            _logger.info('actual_stock bom_product_qty %s', actual_stock)
            possible_combination = int(actual_stock / bom_product_qty) \
                if actual_stock > 0 and bom_product_qty > 0 else 0
            if flag:
                combination = possible_combination
                flag = False
            if possible_combination < combination:
                combination = possible_combination
            _logger.info('possible_combination %s', possible_combination)
        _logger.info('bom stock %s', combination)
        return combination

    # @api.multi
    # def get_stock_ept(self, product_id, warehouse_id, fix_stock_type=False, fix_stock_value=0, stock_type='virtual_available'):
    #     product = self.with_context(warehouse=warehouse_id).browse(product_id.id)
    #     bom_stock = 0.0
    #     try:
    #         product_stock = getattr(product, stock_type)
    #         incoming_stock = getattr(product, 'incoming_qty')
    #         _logger.info('product_stock %s', product_stock)
    #         actual_stock = product_stock - incoming_stock
    #         _logger.info('actual_stock %s', actual_stock)
    #         if product_id.bom_count:
    #             bom_stock = product_id.find_bom_product_possible_quantity(warehouse_id, stock_type) or 0.0
    #             _logger.info('bom_stock %s', bom_stock)
    #         actual_stock = actual_stock + bom_stock
    #         _logger.info('updated final stock %s', actual_stock)
    #         if actual_stock >= 1.00:
    #             if fix_stock_type == 'fix':
    #                 if fix_stock_value >= actual_stock:
    #                     return actual_stock - 1
    #                 else:
    #                     return fix_stock_value - 1
    #
    #             elif fix_stock_type == 'percentage':
    #                 quantity = int((actual_stock * fix_stock_value) / 100.0)
    #                 if quantity >= actual_stock:
    #                     return actual_stock - 1
    #                 else:
    #                     return quantity - 1
    #         return actual_stock - 1
    #     except Exception as e:
    #         raise Warning(e)
