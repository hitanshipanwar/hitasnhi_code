from odoo.tests.common import Form, TransactionCase


class TestOMFPurchase(TransactionCase):
    def test_00_manual_price_unit(self):
        test_product = self.env['product.product'].create({
            'name': 'Test Product',
            'default_code': 'TEST_PRICE_UNIT',
            'type': 'consu',
            'standard_price': 5.0,
        })
        po_form = Form(self.env['purchase.order'])
        with po_form.order_line.new() as line:
            line.product_id = test_product
            line.product_qty = 2.0
            self.assertEqual(line.price_unit, 5.0)
            line.price_unit = 10.0
            line.product_qty = 10.0
            self.assertEqual(line.price_unit, 10.0)
