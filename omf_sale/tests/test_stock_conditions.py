from odoo import tests


class TestStockConditions(tests.TransactionCase):
    def test_00_stock_conditions(self):
        Product = self.env['product.product'].with_context(test_mode=True)
        customer_location = self.env.ref('stock.stock_location_customers')
        supplier_location = self.env.ref('stock.stock_location_suppliers')
        
        self.product_categ = self.env['product.category'].search([('id', '!=', 1)], limit=1)
        
        product = Product.create({
            'name': 'Test Product',
            'type': 'product',
            'us_low_stock_qty': 10,
            'ca_low_stock_qty': 15,
            'categ_id': self.product_categ.id,
        })
        
        us_warehouse = self.env['stock.warehouse'].create({
            'name': 'US Warehouse',
            'code': 'WH-US',
        })
        ca_warehouse = self.env['stock.warehouse'].create({
            'name': 'CA Warehouse',
            'code': 'WH-CA',
        })
        product_context_us = product.with_context(warehouse=us_warehouse.id)
        product_context_ca = product.with_context(warehouse=ca_warehouse.id)
        
        Product._cron_compute_stock_conditions_in_om_wh(use_manual_qty_categ_id=self.product_categ.id)
        self.assertEqual(product_context_us.virtual_available, 0)
        self.assertEqual(product_context_ca.virtual_available, 0)
        self.assertEqual(product.us_stock_condition, 'out_stock')
        self.assertEqual(product.ca_stock_condition, 'out_stock')
        
        # Add some inventory
        self.env['stock.quant'].with_context(inventory_mode=True).create({
            'product_id': product.id,
            'inventory_quantity': 20.0,
            'location_id': us_warehouse.lot_stock_id.id,
        }).action_apply_inventory()
        
        self.env['stock.quant'].with_context(inventory_mode=True).create({
            'product_id': product.id,
            'inventory_quantity': 20.0,
            'location_id': ca_warehouse.lot_stock_id.id,
        }).action_apply_inventory()
        
        Product._cron_compute_stock_conditions_in_om_wh(use_manual_qty_categ_id=self.product_categ.id)
        self.assertEqual(product_context_us.virtual_available, 20.0)
        self.assertEqual(product_context_ca.virtual_available, 20.0)
        self.assertEqual(product.us_stock_condition, 'in_stock')
        self.assertEqual(product.ca_stock_condition, 'in_stock')
        
        out_move = self.env['stock.move'].create({
            'name': 'test_out_us',
            'location_id': us_warehouse.lot_stock_id.id,
            'location_dest_id': customer_location.id,
            'product_id': product.id,
            'product_uom': product.uom_id.id,
            'product_uom_qty': 25.0,
        })
        out_move._action_confirm()
        
        Product._cron_compute_stock_conditions_in_om_wh(use_manual_qty_categ_id=self.product_categ.id)
        self.assertEqual(product_context_us.virtual_available, -5.0)
        self.assertEqual(product_context_ca.virtual_available, 20.0)
        self.assertEqual(product.us_stock_condition, 'out_stock')
        self.assertEqual(product.ca_stock_condition, 'in_stock')
        
        out_move = self.env['stock.move'].create({
            'name': 'test_out_ca',
            'location_id': ca_warehouse.lot_stock_id.id,
            'location_dest_id': customer_location.id,
            'product_id': product.id,
            'product_uom': product.uom_id.id,
            'product_uom_qty': 15.0,
        })
        out_move._action_confirm()
        
        Product._cron_compute_stock_conditions_in_om_wh(use_manual_qty_categ_id=self.product_categ.id)
        self.assertEqual(product_context_us.virtual_available, -5.0)
        self.assertEqual(product_context_ca.virtual_available, 5.0)
        self.assertEqual(product.us_stock_condition, 'out_stock')
        self.assertEqual(product.ca_stock_condition, 'low_stock')
        
        in_move = self.env['stock.move'].create({
            'name': 'test_in_us',
            'location_id': supplier_location.id,
            'location_dest_id': us_warehouse.lot_stock_id.id,
            'product_id': product.id,
            'product_uom': product.uom_id.id,
            'product_uom_qty': 20.0,
        })
        in_move._action_confirm()
        
        Product._cron_compute_stock_conditions_in_om_wh(use_manual_qty_categ_id=self.product_categ.id)
        self.assertEqual(product_context_us.virtual_available, 15.0)
        self.assertEqual(product_context_ca.virtual_available, 5.0)
        self.assertEqual(product.us_stock_condition, 'incoming_stock')
        self.assertEqual(product.ca_stock_condition, 'low_stock')
