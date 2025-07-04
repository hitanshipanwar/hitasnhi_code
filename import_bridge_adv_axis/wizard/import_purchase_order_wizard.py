# -*- coding: utf-8 -*-
#################################################################################
# Author      : AxisTechnolabs.com
# Copyright(c): 2011-Axistechnolabs.com.
# All Rights Reserved.
#
# This program is copyright property of the author mentioned above.
# You can`t redistribute it and/or modify it.
#
#################################################################################
from odoo import models, fields, _,api
from odoo.exceptions import Warning, ValidationError
import logging
import tempfile
import binascii
import datetime
import re
import csv
import xlrd
import base64
import io

_logger = logging.getLogger(__name__)


class ImportPurchaseOrder(models.TransientModel):
    _name = "import.purchase.order"
    _description = 'import purchase order'

    import_file = fields.Binary(string="Add File")
    file_option = fields.Selection([('csv', 'CSV File'), ('xls', 'XLS File')], string='Select File', default='csv')
    sequence_option = fields.Selection([('default_sequence', 'Use System Default Sequence Number'),
                                        ('file_sequence', 'Use Excel/CSV Sequence Number')], string='Sequence Option',
                                       default='default_sequence')
    product_detail_option = fields.Selection(
        [('detail_by_product', 'Take Details From the Product'),
         ('detail_by_file', 'Take Details From the XLS File')],
        string='Product Details Option', default='detail_by_product')

    quotation_stage_option = fields.Selection(
        [('draft_quotation', 'Import Draft Purchase'),
         ('validate_quotation', 'Confirm Purchase Automatically With Import')],
        string='Purchase Stage Option', default='draft_quotation')
    product_by = fields.Selection([('name', 'Name'), ('code', 'Default Code'), ('barcode', 'Barcode')],
                                  string='Import Product By', default='name')
    
    def import_purchase_order(self):
        if self.file_option == 'csv':

            try:
                csv_data = base64.b64decode(self.import_file)
                data_file = io.StringIO(csv_data.decode("utf-8"))
                data_file.seek(0)
                csv_reader = csv.DictReader(data_file, delimiter=',')
            except:
                raise Warning(_("Invalid file!"))

            partner = self.env['res.partner']
            payment_term = self.env['account.payment.term']
            product = self.env['product.product']
            user = self.env['res.users']
            tax = self.env['account.tax']
            lst =[]
            for line in csv_reader:

                if line.get('VAT'):
                    vat = str(line.get('VAT'))
                else:
                    vat = ""

                if line.get('Partner'):
                    if line.get('VAT'):
                        partners = partner.search([('name', '=', line.get('Partner'))])
                        exact_partner = partners.filtered(lambda p: p.vat == vat)

                        if exact_partner:
                            partner = exact_partner[0]
                        else:
                            partner_without_vat = partners.filtered(lambda p: not p.vat)
                            if partner_without_vat:
                                partner = partner_without_vat[0]
                                partner.write({'vat': vat})
                            else:
                                partner = partner.create({
                                    'name': line.get('Partner'),
                                    'vat': vat,
                                })
                    else:
                        partner = self.env['res.partner'].search([('name', '=', line.get('Partner'))])

                    if len(partner) > 1:
                        raise ValidationError(_("Multiple Partner(%s) with same name found")%line.get('Partner'))

                    if not partner:
                        partner = partner.create({
                            'name': line.get('Partner'),
                            'vat': vat,
                        })
                    else:
                        partner = partner[0]
                        if partner.vat != vat:
                            partner.write({
                                'vat': vat,
                            })
                    partner_count = self.env['res.partner'].sudo().search_count([('name', '=', line.get('Partner'))])
                    lst.append(partner_count)

                if vat:
                    partner = partner.search([('name', '=', line.get('Partner')), ('vat', '=', line.get('VAT'))]) 
                else:
                    partner = partner.search([('name', '=', line.get('Partner'))])
                    
                if line.get('Payment Terms'):

                    payment_term = payment_term.search([('name', '=', line.get('Payment Terms'))])
                    amount = [int(i) for i in line.get('Payment Terms').split() if i.isdigit()]

                    if not payment_term:
                        payment_term = payment_term.create({
                            'name': line.get('Payment Terms'),
                            'line_ids': [
                                (0, 0, {
                                    'value': 'balance',
                                    'days': amount[0],
                                    'option': 'day_after_invoice_date',
                                    'day_of_the_month': 0,
                                }),
                            ]
                        })

                if line.get('Date'):
                    date = datetime.datetime.strptime(line['Date'], '%m/%d/%Y')
                else:
                    date = datetime.datetime.now()

                if line.get('Salesperson'):
                    user = user.search([('name', '=', line.get('Salesperson'))])

                if line.get('Tax'):
                    amount = re.findall(r"[-+]?\d*\.\d+|\d+", line.get('Tax'))
                    vendor_tax = tax.search(
                        [('name', '=', line.get('Tax')), ('type_tax_use', '=', 'purchase')])

                    if not vendor_tax:
                        vendor_tax = vendor_tax.create({
                            'name': line.get('Tax'),
                            'type_tax_use': 'purchase',
                            'amount': amount[0],
                            'active': True,
                        })

                if line.get('Uom'):
                    uom = self.env['uom.uom'].search([('name', '=', line.get('Uom'))])

                if line.get('Partner Name'):
                    partner_name = line.get('Partner Name')
                else:
                    partner_name = ""
                
                if line.get('Attributes Name'):
                    attributes_name = line.get('Attributes Name')
                else:
                    attributes_name = ""
                
                if line.get('IMP Note'):
                    imp_note = line.get('IMP Note')
                else:
                    imp_note = ""

                if line.get('Other Details'):
                    other_details = line.get('Other Details')
                else:
                    other_details = ""

                if line.get('Order Number'):
                    order_number = line.get('Order Number')
                else:
                    order_number = ""

                if line.get('Payment Reference ID'):
                    payment_reference = line.get('Payment Reference ID')
                else:
                    payment_reference = "" 

                if line.get('Payment Date'):
                    payment_date = datetime.datetime.strptime(line['Payment Date'], '%m/%d/%Y')
                else:
                    payment_date = False    

                if line.get('Payment Amount'):
                    payment_amt = line.get('Payment Amount')
                else:
                    payment_amt = "" 

                if line.get('Payment Method Type'):
                    payment_method_type = line.get('Payment Method Type')
                else:
                    payment_method_type = "" 
                
                if line.get('Part Number'):
                    part_number = line.get('Part Number')
                else:
                    part_number = "" 
                
                yes_no = 0
                if line.get('Yes/No'):
                    if int(line.get('Yes/No')) == 1:
                        yes_no = 1
                    else:
                        yes_no = 0

                if self.sequence_option == 'default_sequence':
                    purchase_order = self.env['purchase.order'].create({
                        'partner_id': partner.id,
                        'date_order': date,
                        'payment_term_id': payment_term.id,
                        'user_id': user.id,
                        'seller_vat_num': vat,
                        'order_number': order_number,
                        'payment_reference': payment_reference,
                        'payment_date': payment_date,
                        'payment_amt': payment_amt,
                        'payment_method_type': payment_method_type,
                    })

                elif self.sequence_option == 'file_sequence':
                    purchase_order = self.env['purchase.order'].search([('name', '=', line.get('Order'))])
                    if not purchase_order:
                        purchase_order = self.env['purchase.order'].create({
                            'name': line.get('Order') if line.get('Order') else 'PO',
                            'partner_id': partner.id,
                            'date_order': date,
                            'payment_term_id': payment_term.id,
                            'user_id': user.id,
                            'seller_vat_num': vat,
                            'order_number': order_number,
                            'payment_reference': payment_reference,
                            'payment_date': payment_date,
                            'payment_amt': payment_amt,
                            'payment_method_type': payment_method_type,
                        })

                if purchase_order:
                    if line.get('Product'):

                        if self.product_by == 'name':
                            product = product.search([('name', '=', line.get('Product'))])

                            if len(product) > 1:
                                raise ValidationError(_("Multiple Product(%s) with same name found")%line.get('Product'))

                            if not product:
                                product = product.create({
                                    'name': line.get('Product'),
                                    'part_number': line.get('Part Number'),
                                })

                        if self.product_by == 'code':
                            product = product.search([('default_code', '=', line.get('Product'))])

                            if len(product) > 1:
                                raise ValidationError(_("Multiple Product(%s) with same name found")%line.get('Product'))

                        if self.product_by == 'barcode':
                            product = product.search([('barcode', '=', line.get('Product'))])

                            if len(product) > 1:
                                raise ValidationError(_("Multiple Product(%s) with same name found")%line.get('Product'))

                if product:
                    product.write({'part_number': line.get('Part Number')})


                if product and self.product_detail_option == 'detail_by_file':
                    purchase_order[0].write({
                        'order_line': [
                            (0, 0, {
                                'name': line.get('Description'),
                                'product_id': product.id,
                                'product_uom': uom.id if uom else False,
                                'product_qty': float(line.get('Quantity')) if line.get('Quantity') else 1.0,
                                'price_unit': float(line.get('Price')),
                                'taxes_id': vendor_tax,
                                'date_planned': datetime.datetime.now(),
                                'order_id': purchase_order,
                                'part_number': line.get('Part Number'),
                            }),
                        ],
                        'purchase_add_details_id': [
                            (0, 0, {
                                'product_id': product.id,
                                'partner_name': partner_name,
                                'attributes_name': attributes_name,
                                'imp_note': imp_note,
                                'other_details': other_details,
                                'yes_no': yes_no,
                            }),
                        ]
                    })

                if product and self.product_detail_option == 'detail_by_product':
                    purchase_order[0].write({
                        'order_line': [
                            (0, 0, {
                                'name': line.get('Description'),
                                'product_id': product.id,
                                'product_uom': product.uom_id.id if product.uom_id else False,
                                'product_qty': float(line.get('Quantity')) if line.get('Quantity') else 1.0,
                                'price_unit': product.standard_price,
                                'taxes_id': product.supplier_taxes_id,
                                'date_planned': datetime.datetime.now(),
                                'order_id': purchase_order,
                                'part_number': line.get('Part Number'),
                            }),
                        ],
                        'purchase_add_details_id': [
                            (0, 0, {
                                'product_id': product.id,
                                'partner_name': partner_name,
                                'attributes_name': attributes_name,
                                'imp_note': imp_note,
                                'other_details': other_details,
                                'yes_no': yes_no,
                            }),
                        ]
                    })

                if self.quotation_stage_option == 'validate_quotation':
                    purchase_order.button_confirm()
            get_count=0
            for rec in lst:
                get_count = get_count+rec
                
            model = self.env.context.get('active_model')
            if model == 'custom.dashboard':
               sale_info = self.env['custom.dashboard'].sudo().search([['name','=','Purchase']])
               if sale_info.count == 0:
                  sale_info.count = get_count
               else:
                  sale_info.count += get_count


        elif self.file_option == 'xls':
            try:
                fp = tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx")
                fp.write(binascii.a2b_base64(self.import_file))
                fp.seek(0)
                workbook = xlrd.open_workbook(fp.name)
                sheet = workbook.sheet_by_index(0)
                keys = sheet.row_values(0)
                xls_reader = [sheet.row_values(i) for i in range(1, sheet.nrows)]

            except:
                raise Warning(_("Invalid file!"))

            partner = self.env['res.partner']
            payment_term = self.env['account.payment.term']
            product = self.env['product.product']
            user = self.env['res.users']
            tax = self.env['account.tax']
            lst=[]
            for row in xls_reader:
                line = dict(zip(keys, row))

                if line.get('VAT'):
                    vat = str(line.get('VAT'))
                else:
                    vat = ""

                if line.get('Partner'):
                    if line.get('VAT'):
                        partners = partner.search([('name', '=', line.get('Partner'))])
                        exact_partner = partners.filtered(lambda p: p.vat == vat)

                        if exact_partner:
                            partner = exact_partner[0]
                        else:
                            partner_without_vat = partners.filtered(lambda p: not p.vat)
                            if partner_without_vat:
                                partner = partner_without_vat[0]
                                partner.write({'vat': vat})
                            else:
                                partner = partner.create({
                                    'name': line.get('Partner'),
                                    'vat': vat,
                                })
                    else:
                        partner = partner.search([('name', '=', line.get('Partner'))])

                    if len(partner) > 1:
                        raise ValidationError(_("Multiple Partner(%s) with same name found")%line.get('Partner'))

                    if not partner:
                        partner = partner.create({
                            'name': line.get('Partner'),
                            'vat': vat,
                        })
                    else:
                        partner = partner[0]
                        if partner.vat != vat:
                            partner.write({
                                'vat': vat,
                            })
                    partner_count = self.env['res.partner'].sudo().search_count([('name', '=', line.get('Partner'))])
                    lst.append(partner_count)

                if vat:
                    partner = partner.search([('name', '=', line.get('Partner')), ('vat', '=', line.get('VAT'))]) 
                else:
                    partner = partner.search([('name', '=', line.get('Partner'))])

                if line.get('Payment Terms'):

                    payment_term = payment_term.search([('name', '=', line.get('Payment Terms'))])
                    amount = [int(i) for i in line.get('Payment Terms').split() if i.isdigit()]

                    if not payment_term:
                        payment_term = payment_term.create({
                            'name': line.get('Payment Terms'),
                            'line_ids': [
                                (0, 0, {
                                    'value': 'balance',
                                    'days': amount[0],
                                    'option': 'day_after_invoice_date',
                                    'day_of_the_month': 0,
                                }),
                            ]
                        })

                if line.get('Date'):
                    date = datetime.datetime.strptime(line['Date'], '%m/%d/%Y')
                else:
                    date = datetime.datetime.now()

                if line.get('Salesperson'):
                    user = user.search([('name', '=', line.get('Salesperson'))])

                if line.get('Tax'):
                    amount = re.findall(r"[-+]?\d*\.\d+|\d+", line.get('Tax'))
                    vendor_tax = tax.search(
                        [('name', '=', line.get('Tax')), ('type_tax_use', '=', 'purchase')])

                    if not vendor_tax:
                        vendor_tax = vendor_tax.create({
                            'name': line.get('Tax'),
                            'type_tax_use': 'purchase',
                            'amount': amount[0],
                            'active': True,
                        })                
                else:
                    vendor_tax = [(6, 0, [])]

                if line.get('Uom'):
                    uom = self.env['uom.uom'].search([('name', '=', line.get('Uom'))])

                if line.get('Partner Name'):
                    partner_name = line.get('Partner Name')
                else:
                    partner_name = ""
                
                if line.get('Attributes Name'):
                    attributes_name = line.get('Attributes Name')
                else:
                    attributes_name = ""
                
                if line.get('IMP Note'):
                    imp_note = line.get('IMP Note')
                else:
                    imp_note = ""

                if line.get('Other Details'):
                    other_details = line.get('Other Details')
                else:
                    other_details = ""

                if line.get('Order Number'):
                    order_number = line.get('Order Number')
                else:
                    order_number = ""

                if line.get('Payment Reference ID'):
                    payment_reference = line.get('Payment Reference ID')
                else:
                    payment_reference = "" 

                if line.get('Payment Date'):
                    payment_date = datetime.datetime.strptime(line['Payment Date'], '%m/%d/%Y')
                else:
                    payment_date = False    

                if line.get('Payment Amount'):
                    payment_amt = line.get('Payment Amount')
                else:
                    payment_amt = "" 

                if line.get('Payment Method Type'):
                    payment_method_type = line.get('Payment Method Type')
                else:
                    payment_method_type = "" 

                if line.get('Part Number'):
                    part_number = line.get('Part Number')
                else:
                    part_number = ""
                
                yes_no = 0
                if line.get('Yes/No'):
                    if int(line.get('Yes/No')) == 1:
                        yes_no = 1
                    else:
                        yes_no = 0

                if self.sequence_option == 'default_sequence':
                    purchase_order = self.env['purchase.order'].create({
                        'partner_id': partner.id,
                        'date_order': date,
                        'payment_term_id': payment_term.id,
                        'user_id': user.id,
                        'seller_vat_num': vat,
                        'order_number': order_number,
                        'payment_reference': payment_reference,
                        'payment_date': payment_date,
                        'payment_amt': payment_amt,
                        'payment_method_type': payment_method_type,
                    })

                elif self.sequence_option == 'file_sequence':
                    purchase_order = self.env['purchase.order'].search([('name', '=', line.get('Order'))])
                    if not purchase_order:
                        purchase_order = self.env['purchase.order'].create({
                            'name': line.get('Order') if line.get('Order') else 'PO',
                            'partner_id': partner.id,
                            'date_order': date,
                            'payment_term_id': payment_term.id,
                            'user_id': user.id,
                            'seller_vat_num': vat,
                            'order_number': order_number,
                            'payment_reference': payment_reference,
                            'payment_date': payment_date,
                            'payment_amt': payment_amt,
                            'payment_method_type': payment_method_type,
                        })
                if purchase_order:
                    if line.get('Product'):

                        if self.product_by == 'name':
                            product = product.search([('name', '=', line.get('Product'))])

                            if len(product) > 1:
                                raise ValidationError(_("Multiple Product(%s) with same name found")%line.get('Product'))

                            if not product:
                                product = product.create({
                                    'name': line.get('Product'),
                                    'part_number': line.get('Part Number'),
                                })

                        if self.product_by == 'code':
                            product = product.search([('default_code', '=', line.get('Product'))])
                            
                            if len(product) > 1:
                                raise ValidationError(_("Multiple Product(%s) with same name found")%line.get('Product'))

                        if self.product_by == 'barcode':
                            product = product.search([('barcode', '=', line.get('Product'))])

                if product:
                    product.write({'part_number': line.get('Part Number')})

                if product and self.product_detail_option == 'detail_by_file':                    
                    purchase_order[0].write({
                        'order_line': [
                            (0, 0, {
                                'name': line.get('Description'),
                                'product_id': product.id,
                                'product_uom': uom.id if uom else False,
                                'product_qty': float(line.get('Quantity')) if line.get('Quantity') else 1.0,
                                'price_unit': float(line.get('Price')),
                                'taxes_id': vendor_tax,
                                'date_planned': datetime.datetime.now(),
                                'order_id': purchase_order,
                                'part_number': line.get('Part Number'),
                            }),
                        ],
                        'purchase_add_details_id': [
                            (0, 0, {
                                'product_id': product.id,
                                'partner_name': partner_name,
                                'attributes_name': attributes_name,
                                'imp_note': imp_note,
                                'other_details': other_details,
                                'yes_no': yes_no,
                            }),
                        ]
                    })

                if product and self.product_detail_option == 'detail_by_product':
                    purchase_order[0].write({
                        'order_line': [
                            (0, 0, {
                                'name': line.get('Description'),
                                'product_id': product.id,
                                'product_uom': product.uom_id.id if product.uom_id else False,
                                'product_qty': float(line.get('Quantity')) if line.get('Quantity') else 1.0,
                                'price_unit': product.standard_price,
                                'taxes_id': product.supplier_taxes_id,
                                'date_planned': datetime.datetime.now(),
                                'order_id': purchase_order,
                                'part_number': line.get('Part Number'),
                            }),
                        ],
                        'purchase_add_details_id': [
                            (0, 0, {
                                'product_id': product.id,
                                'partner_name': partner_name,
                                'attributes_name': attributes_name,
                                'imp_note': imp_note,
                                'other_details': other_details,
                                'yes_no': yes_no,
                            }),
                        ]
                    })

                if self.quotation_stage_option == 'validate_quotation':
                    purchase_order.button_confirm()
            get_count=0
            for rec in lst:
                get_count = get_count+rec
                
            model = self.env.context.get('active_model')
            if model == 'custom.dashboard':
               sale_info = self.env['custom.dashboard'].sudo().search([['name','=','Purchase']])
               if sale_info.count == 0:
                  sale_info.count = get_count
               else:
                  sale_info.count += get_count
