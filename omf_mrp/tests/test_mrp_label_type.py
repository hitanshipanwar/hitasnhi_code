from odoo.exceptions import ValidationError
from odoo.tests import Form, TransactionCase


class TestMrpLabelType(TransactionCase):
    def setUp(self):
        self.bom_product = self.env['product.product'].create({
            'name': 'BOM Product',
        })
        self.product1 = self.env['product.product'].create({
            'name': 'Test Product 1',
        })
        self.product2 = self.env['product.product'].create({
            'name': 'Test Product 2',
        })
        self.po_product = self.env['product.product'].create({
            'name': 'Product on PO Only',
        })
        self.bom = self.env['mrp.bom'].create({
            'product_tmpl_id': self.bom_product.product_tmpl_id.id,
            'bom_line_ids': [
                (0, 0, {'product_id': self.product1.id, 'product_qty': 1.0}),
                (0, 0, {'product_id': self.product2.id, 'product_qty': 1.0}),
            ],
        })
        
        po = Form(self.env['purchase.order'])
        po.partner_id = self.env.ref('base.res_partner_4')
        with po.order_line.new() as line:
            line.product_id = self.product1
            line.organic_status = 'NOP' # Organic
        with po.order_line.new() as line:
            line.product_id = self.product2
            line.organic_status = 'NON-ORG'
        with po.order_line.new() as line:
            line.product_id = self.po_product
            line.organic_status = 'NON-ORG'
        self.po = po.save()
        
    def test_00_wrong_label_type(self):
        wrong_label_exception = self.env.ref('omf_mrp.excep_wrong_label_type')
        wrong_label_exception.active = True
        
        production = Form(self.env['mrp.production'])
        production.bom_id = self.bom
        production.po_lot_id = self.po
        production.label_type = 'ORG'
        production = production.save()
        production.action_confirm()
        self.assertEqual(production.state, 'draft')
        self.assertEqual(production.exception_ids, wrong_label_exception)
        
        # We only care about PO lines related to this MO, 
        # so the exception should not be triggered by the po_product line
        self.po.order_line.filtered(lambda pol: pol.product_id == self.product2).organic_status = 'NOP'
        production.action_confirm()
        self.assertEqual(production.state, 'confirmed')
        self.assertEqual(len(production.exception_ids), 0)
    
    def test_10_set_label_type(self):
        self.env.company.country_id = self.env.ref('base.us')
        production = Form(self.env['mrp.production'])
        production.bom_id = self.bom
        self.assertEqual(production.label_type, 'ORG')
        production.po_lot_id = self.po
        self.assertEqual(production.label_type, 'ORG')
        
        # This piece needs to work for both companies
        invalid_po = Form(self.env['purchase.order'])
        invalid_po.partner_id = self.env.ref('base.res_partner_4')
        with invalid_po.order_line.new() as line:
            line.product_id = self.po_product
            line.organic_status = 'NON-ORG'
        invalid_po = invalid_po.save()
        
        with self.assertRaises(ValidationError):
            production.po_lot_id = invalid_po
        
        self.env.company.country_id = self.env.ref('base.ca')
        production = Form(self.env['mrp.production'])
        production.bom_id = self.bom
        self.assertEqual(production.label_type, 'ORG')
        production.po_lot_id = self.po
        self.assertEqual(production.label_type, 'NON-ORG')
        
        invalid_po = Form(self.env['purchase.order'])
        invalid_po.partner_id = self.env.ref('base.res_partner_4')
        with invalid_po.order_line.new() as line:
            line.product_id = self.po_product
            line.organic_status = 'NON-ORG'
        invalid_po = invalid_po.save()
        
        with self.assertRaises(ValidationError):
            production.po_lot_id = invalid_po
