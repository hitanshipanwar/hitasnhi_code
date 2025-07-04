from odoo.tests import Form, TransactionCase


class TestLastPurchaseFrom(TransactionCase):
    def setUp(self):
        super().setUp()
        self.vendor1 = self.browse_ref('base.res_partner_12')
        self.vendor2 = self.browse_ref('base.res_partner_2')
        self.customer = self.browse_ref('base.res_partner_3')
        self.product1 = self.env['product.product'].create({
            'name': 'Test Product 1',
            'detailed_type': 'product',
        })
        self.product2 = self.env['product.product'].create({
            'name': 'Test Product 2',
            'detailed_type': 'product',
        })
        
    def test_00_last_purchased_from(self):
        po_form = Form(self.env['purchase.order'])
        po_form.partner_id = self.vendor1
        with po_form.order_line.new() as line:
            line.product_id = self.product1
            line.product_qty = 2.0
        with po_form.order_line.new() as line:
            line.product_id = self.product2
            line.product_qty = 2.0
        first_po = po_form.save()
        first_po.button_confirm()
        first_po.picking_ids.move_line_ids.write({
            'qty_done': 2.0
        })
        first_po.picking_ids.button_validate()
        self.assertEqual(first_po.picking_ids.company_id.country_id.code, 'US')
        
        self.assertEqual(first_po.picking_ids.state, 'done')
        self.assertEqual(self.product1.us_last_vendor_id, self.vendor1)
        self.assertEqual(self.product2.us_last_vendor_id, self.vendor1)
        self.assertFalse(self.product1.ca_last_vendor_id)
        self.assertFalse(self.product2.ca_last_vendor_id)
        
        # we will change the company's country to get the
        # next picking to fill the other field
        country_ca = self.env['res.country'].search([('code', '=', 'CA')])
        self.assertTrue(country_ca)
        first_po.picking_ids.company_id.country_id = country_ca
        
        po_form = Form(self.env['purchase.order'])
        po_form.partner_id = self.vendor2
        with po_form.order_line.new() as line:
            line.product_id = self.product2
            line.product_qty = 1.0
        second_po = po_form.save()
        second_po.button_confirm()
        second_po.picking_ids.move_line_ids.write({
            'qty_done': 1.0
        })
        second_po.picking_ids.button_validate()
        
        self.assertEqual(second_po.picking_ids.state, 'done')
        self.assertEqual(self.product1.us_last_vendor_id, self.vendor1)
        self.assertEqual(self.product2.us_last_vendor_id, self.vendor1)
        self.assertFalse(self.product1.ca_last_vendor_id)
        self.assertEqual(self.product2.ca_last_vendor_id, self.vendor2)
        
        # Delivery Order should not update last_vendor_id
        so_form = Form(self.env['sale.order'])
        so_form.partner_id = self.customer
        with so_form.order_line.new() as line:
            line.product_id = self.product1
            line.product_uom_qty = 2.0
        so = so_form.save()
        so.action_confirm()
        so.picking_ids.move_line_ids.write({
            'qty_done': 2.0
        })
        so.picking_ids.button_validate()
        
        self.assertEqual(so.picking_ids.state, 'done')
        self.assertEqual(self.product1.us_last_vendor_id, self.vendor1)
        self.assertEqual(self.product2.us_last_vendor_id, self.vendor1)
        self.assertFalse(self.product1.ca_last_vendor_id)
        self.assertEqual(self.product2.ca_last_vendor_id, self.vendor2)
