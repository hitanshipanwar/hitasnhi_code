# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) Sitaram Solutions (<https://sitaramsolutions.in/>).
#
#    For Module Support : info@sitaramsolutions.in  or Skype : contact.hiren1188
#
##############################################################################

import tempfile
import binascii
import xlrd
import io
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from datetime import date, datetime
from odoo.exceptions import Warning,UserError
from odoo import models, fields, api, _
import csv
import base64


class SrImportPurchase(models.TransientModel):
    _name = "sr.import.purchase"

    select_file = fields.Binary('File')
    sequence_option = fields.Selection([('custom', 'Use Excel/CSV Sequence Number'), ('system', 'Use System Default Sequence Number')], string='Sequence Option', default='custom')
    import_option = fields.Selection([('csv', 'CSV File'), ('xls', 'XLS File')], string='Select', default='csv')
    stage_option = fields.Selection(
        [('draft', 'Import Draft Purchase'), ('confirm', 'Confirm Purchase Automatically With Import')],
        string="Purchase Stage Option", default='draft')
    import_product_option = fields.Selection([('name', 'Name'), ('code', 'Code'), ('barcode', 'Barcode')], string='Import Product By ', default='name')
    import_vendor_option = fields.Selection([('name', 'Name'), ('code', 'Internal Reference')], string='Import Vendor By ', default='name')        

    def import_purchase(self):
        try:
            if self.import_option == 'xls':
                temp_excel_file = tempfile.NamedTemporaryFile(suffix=".xlsx")
                temp_excel_file.write(binascii.a2b_base64(self.select_file))
                temp_excel_file.seek(0)
                workbook = xlrd.open_workbook(temp_excel_file.name)
                sheet = workbook.sheet_by_index(0)
                for row_no in range(sheet.nrows):
                    if row_no != 0:
                        line = list(map(lambda row:isinstance(row.value, bytes) and row.value.encode('utf-8') or str(row.value), sheet.row(row_no)))
                        date_tuple = xlrd.xldate_as_tuple(float(line[5]), workbook.datemode)
                        line[5] = datetime(*date_tuple).strftime('%Y-%m-%d')
                        self.generate_purchase_order(line)
                        
            else:
                try:
                    csv_data = base64.b64decode(self.select_file)
                    data_file = io.StringIO(csv_data.decode("utf-8"))
                    data_file.seek(0)
                    file_reader = []
                    csv_reader = csv.reader(data_file, delimiter=',')
                    file_reader.extend(csv_reader)
                except:
                    raise UserError(_("Invalid file!"))
                for row_no in range(len(file_reader)):
                    line = list(map(str, file_reader[row_no]))
                    if line:
                        if row_no != 0:
#                             line[2] = datetime.strptime(line[2], '%d/%m/%y')
                            self.generate_purchase_order(line)
        except Exception as e:
            raise UserError(_(e))

    def _find_vendor(self, vendor):
        if self.import_vendor_option == 'name':
            vendor_id = self.env['res.partner'].search([('name', '=', vendor)])
        else:
            vendor_id = self.env['res.partner'].search([('ref', '=', vendor)])
        if vendor_id:
            return vendor_id
        else:
            raise UserError(_('"%s" Vendor not in your system') % vendor)

    def _find_currency(self, currency):
        currency_id = self.env['res.currency'].search([('name', '=', currency)])
        if currency_id:
            return currency_id
        else:
            raise UserError(_('"%s" Currency not in your system') % currency)

    def _find_compnay(self, company):
        company_id = self.env['res.company'].search([('name', '=', company)])
        if company_id:
            return company_id
        else:
            raise UserError(_('"%s" Company not in your system') % company)

    def generate_purchase_order_line(self, purchase_id, product, description, quantity, uom, price, tax):
        tax_ids = []
        if tax:
            for record in tax.split(','):
                tax = self.env['account.tax'].search([('name', '=', record), ('type_tax_use', '=', 'purchase')])
                if not tax:
                    raise UserError(_('"%s" Tax not in your system') % record)
                tax_ids.append(tax.id)
        self.env['purchase.order.line'].create(
            {
                'product_id':self._find_product(product).id,
                'name': description,
                'product_qty': quantity,
                'product_uom': self._find_uom(uom).id,
                'price_unit':price,
                'taxes_id':([(6, 0, tax_ids)]),
                'order_id': purchase_id.id,
                'date_planned':datetime.today().strftime(DEFAULT_SERVER_DATETIME_FORMAT)
                })
        return True

    def generate_purchase_order(self, line):
        vendor_id = self._find_vendor(line[1])
        currency_id = self._find_currency(line[3])
        company_id = self._find_compnay(line[4])
        purchase_id = self.env['purchase.order'].search([('name', '=', line[0])])
        if purchase_id:
            if purchase_id.partner_id.id == vendor_id.id:
                if purchase_id.currency_id.id == currency_id.id:
                    if purchase_id.company_id.id == company_id.id:
                        self.generate_purchase_order_line(purchase_id, product=line[6], description=line[7], quantity=line[8], uom=line[9], price=line[10], tax=line[11])
                    else:
                        raise UserError(_('Company is different for %s, \n Please define same' % purchase_id.name))
                else:
                    raise UserError(_('Currency is different for %s, \n Please define same' % purchase_id.name))
            else:
                raise UserError(_('Vendor is different for %s, \n Please define same' % purchase_id.name))
        else:
            purchase_id = self.env['purchase.order'].create({
                    'name':self.env['ir.sequence'].next_by_code('purchase.order') if self.sequence_option == 'system' else line[0],
                    'partner_id':vendor_id.id,
                    'partner_ref': line[2],
                    'currency_id': currency_id.id,
                    'date_order': line[5],
                    'company_id':company_id.id,
                    'state':'draft',
                    'date_planned':datetime.today().strftime(DEFAULT_SERVER_DATETIME_FORMAT)
                })
            self.generate_purchase_order_line(purchase_id, product=line[6], description=line[7], quantity=line[8], uom=line[9], price=line[10], tax=line[11])
            if self.stage_option == 'confirm':
                purchase_id.button_confirm()

    def _find_product(self, product):
        if self.import_product_option == 'name':
            product_id = self.env['product.product'].search([('name', '=', product)])
        elif self.import_product_option == 'code':
            product_id = self.env['product.product'].search([('default_code', '=', product)])
        else:
            product_id = self.env['product.product'].search([('barcode', '=', product)])
        if product_id:
            return product_id
        else:
            raise UserError(_('"%s" Product not in your system') % product)

    def _find_uom(self, uom):
        uom_id = self.env['uom.uom'].search([('name', '=', uom)])
        if uom_id:
            return uom_id
        else:
            raise UserError(_('"%s" Unit Of Measure not in your system') % uom)

