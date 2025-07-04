from odoo.tests import common


class TestOMF(common.TransactionCase):
    def setUp(self):
        super().setUp()
        self.warehouse = self.env.ref('stock.warehouse0')
        self.location = self.warehouse.lot_stock_id
        self.raw_product_1 = self.env['product.product'].create({
            'name': 'raw1',
            'default_code': 'raw2',
            'type': 'product',
        })
        self.raw_product_2 = self.env['product.product'].create({
            'name': 'raw2',
            'default_code': 'raw2',
            'type': 'product',
        })
        self.kit_product_1 = self.env['product.product'].create({
            'name': 'kit1',
            'default_code': 'kit1',
            'type': 'product',
        })
        self.mrp_product_1 = self.env['product.product'].create({
            'name': 'mrp1',
            'default_code': 'mrp1',
            'type': 'product',
        })
        
        # Inventory Adjustments...
        # Raw products get 100 of each.
        adjust_quant = self.env['stock.quant'].with_context(inventory_mode=True).create({
            'product_id': self.raw_product_1.id,
            'inventory_quantity': 100.0,
            'location_id': self.location.id,
        })
        adjust_quant.action_apply_inventory()
        adjust_quant = self.env['stock.quant'].with_context(inventory_mode=True).create({
            'product_id': self.raw_product_2.id,
            'inventory_quantity': 100.0,
            'location_id': self.location.id,
        })
        adjust_quant.action_apply_inventory()
        
        # Add some product in another company
        chicago_location = self.env.ref('stock.stock_location_shop0')
        adjust_quant = self.env['stock.quant'].with_context(inventory_mode=True).create({
            'product_id': self.raw_product_2.id,
            'inventory_quantity': 50.0,
            'location_id': chicago_location.id,
        })
        adjust_quant.action_apply_inventory()
        
        # MRP Product I'll adjust in 10
        adjust_quant = self.env['stock.quant'].with_context(inventory_mode=True).create({
            'product_id': self.mrp_product_1.id,
            'inventory_quantity': 10.0,
            'location_id': self.location.id,
        })
        adjust_quant.action_apply_inventory()
        
        # MRP Product and Kit will be built out of both products with one product at 2:1 ratio
        # thus the raw materials can only produce 50 units
        self.env['mrp.bom'].create({
            'product_tmpl_id': self.mrp_product_1.product_tmpl_id.id,
            'product_qty': 1.0,
            'product_uom_id': self.mrp_product_1.uom_id.id,
            'type': 'normal',
            'bom_line_ids': [
                (0, 0, {
                    'product_id': self.raw_product_1.id,
                    'product_qty': 1.0,
                    'product_uom_id': self.raw_product_1.uom_id.id,
                }),
                (0, 0, {
                    'product_id': self.raw_product_2.id,
                    'product_qty': 2.0,
                    'product_uom_id': self.raw_product_2.uom_id.id,
                }),
            ]
        })
        self.env['mrp.bom'].create({
            'product_tmpl_id': self.kit_product_1.product_tmpl_id.id,
            'product_qty': 1.0,
            'product_uom_id': self.kit_product_1.uom_id.id,
            'type': 'phantom',
            'bom_line_ids': [
                (0, 0, {
                    'product_id': self.raw_product_1.id,
                    'product_qty': 1.0,
                    'product_uom_id': self.raw_product_1.uom_id.id,
                }),
                (0, 0, {
                    'product_id': self.raw_product_2.id,
                    'product_qty': 2.0,
                    'product_uom_id': self.raw_product_2.uom_id.id,
                }),
            ]
        })
    
    def test_10_mrp_stock_availability(self):
        # OMF uses the field 'virtual_available' on both Shopify Instances
        # After tracing the code, all of the shopify code goes away and becomes 
        # a single method on product.product
        # 
        # def get_forecasted_qty_ept(self, warehouse, product_list):
        
        all_products= self.raw_product_1 + self.raw_product_2 + self.mrp_product_1 + self.kit_product_1
        product_list = all_products.ids
        
        product_qtys = self.env['product.product'].get_forecasted_qty_ept(self.warehouse, product_list)

        # the two raw products
        self.assertEqual(product_qtys[self.raw_product_1.id], 100.0)
        self.assertEqual(product_qtys[self.raw_product_2.id], 100.0)
        # the kit product, no inventory can build 
        self.assertEqual(product_qtys[self.kit_product_1.id], 50.0)
        # the mrp product, 10 inventory can build
        self.assertEqual(product_qtys[self.mrp_product_1.id], 60.0)

        # Now that we have basic qtys working, lets ensure that making some outbound demand has
        # the correct effect
        customer_location = self.env.ref('stock.stock_location_customers')
        picking_out = self.env.ref('stock.picking_type_out')
        mrp_product_out = self.env['stock.picking'].create({
            'picking_type_id': picking_out.id,
            'partner_id': self.env.user.partner_id.id,
            'location_id': picking_out.default_location_src_id.id,
            'location_dest_id': customer_location.id,
            'move_lines': [
                (0, 0, {
                    'name': 'test mrp product out',
                    'product_id': self.mrp_product_1.id,
                    'location_id': picking_out.default_location_src_id.id,
                    'location_dest_id': customer_location.id,
                    'product_uom_qty': 1.0,
                    'product_uom': self.mrp_product_1.uom_id.id,
                })
            ]
        })
        mrp_product_out.action_confirm()
        
        product_qtys = self.env['product.product'].get_forecasted_qty_ept(self.warehouse, product_list)

        # the two raw products
        self.assertEqual(product_qtys[self.raw_product_1.id], 100.0)
        self.assertEqual(product_qtys[self.raw_product_2.id], 100.0)
        # the kit product, no inventory can build 
        self.assertEqual(product_qtys[self.kit_product_1.id], 50.0)
        # the mrp product, 10 inventory can build
        self.assertEqual(product_qtys[self.mrp_product_1.id], 59.0)

        # Make incoming and outgoing on raw product.
        picking_in = self.env.ref('stock.picking_type_in')
        raw_product_in = self.env['stock.picking'].create({
            'picking_type_id': picking_in.id,
            'partner_id': self.env.user.partner_id.id,
            'location_id': customer_location.id,
            'location_dest_id': picking_out.default_location_src_id.id,
            'move_lines': [
                (0, 0, {
                    'name': 'test raw product in',
                    'product_id': self.raw_product_1.id,
                    'location_id': customer_location.id,
                    'location_dest_id': picking_out.default_location_src_id.id,
                    'product_uom_qty': 5.0,
                    'product_uom': self.raw_product_1.uom_id.id,
                })
            ]
        })
        raw_product_in.action_confirm()
        raw_product_out = self.env['stock.picking'].create({
            'picking_type_id': picking_in.id,
            'partner_id': self.env.user.partner_id.id,
            'location_id': picking_out.default_location_src_id.id,
            'location_dest_id': customer_location.id,
            'move_lines': [
                (0, 0, {
                    'name': 'test raw product out',
                    'product_id': self.raw_product_1.id,
                    'location_id': picking_out.default_location_src_id.id,
                    'location_dest_id': customer_location.id,
                    'product_uom_qty': 20.0,
                    'product_uom': self.raw_product_1.uom_id.id,
                })
            ]
        })
        raw_product_out.action_confirm()
        
        product_qtys = self.env['product.product'].get_forecasted_qty_ept(self.warehouse, product_list)

        # the two raw products
        self.assertEqual(product_qtys[self.raw_product_1.id], 80.0)  # outs accounted for but not ins
        self.assertEqual(product_qtys[self.raw_product_2.id], 100.0)
        # the kit product, no inventory can build 
        self.assertEqual(product_qtys[self.kit_product_1.id], 50.0)
        # the mrp product, 10 inventory can build
        self.assertEqual(product_qtys[self.mrp_product_1.id], 59.0)
