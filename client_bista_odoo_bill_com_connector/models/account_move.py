# -*- encoding: utf-8 -*-
##############################################################################
#
# Bista Solutions Pvt. Ltd
# Copyright (C) 2020 (http://www.bistasolutions.com)
#
##############################################################################

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import date_utils
# from .connection import BillComService
import json
import base64
import requests
from functools import lru_cache

class AccountPaymentMethodLineInherit(models.Model):
    _inherit = "account.payment.method.line"

    payment_acquirer_id = fields.Many2one('payment.provider')
    payment_acquirer_state = fields.Selection([('none', 'None')])


    def action_open_acquirer_form(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Provider'),
            'view_mode': 'form',
            'res_model': 'payment.provider',
            'target': 'current',
            'res_id': self.payment_provider_id.id
        }

class AccountMove(models.Model):
    _inherit = 'account.move'

    is_lock = fields.Boolean(string="Is Lock", copy=False)
    invoice_purchase_order = fields.Char(string="Purchase Order #", tracking=True)

    def action_set_lock_invoice(self):
            self.write({
                'is_lock': True
                })
            if 'don_run' not in self._context:
                self._message_log(body="Invoice Locked")

    def action_set_unlock_invoice(self):
        self.write({
            'is_lock': False
            })
        if 'don_run' not in self._context:
            self._message_log(body="Invoice Unlocked")




    # @api.depends('amount_residual', 'move_type', 'state', 'company_id')
    # def _compute_payment_state(self):
    #     res = super(AccountMove, self)._compute_payment_state()
    #     payment_obj = self.env['account.payment']
    #     for each in self:
    #         if each.move_type == 'in_invoice':
    #             search_scheduled_payments = payment_obj.search(
    #                 [('ref', '=', each.name), ('bill_com_payment_status', '=', 'Scheduled')])
    #             if search_scheduled_payments:
    #                 each.payment_state = 'scheduled'

    @api.depends('amount_residual', 'move_type', 'state', 'company_id')
    def _compute_payment_state(self):
        super(AccountMove, self)._compute_payment_state()
        payment_obj = self.env['account.payment']
        invoice_names = self.filtered(lambda m: m.move_type == 'in_invoice').mapped('name')
        scheduled_payments = payment_obj.search_read(
            [('payment_reference', 'in', invoice_names), ('bill_com_payment_status', '=', 'Scheduled')],
            ['payment_reference']
        )
        scheduled_payment_refs = {payment['payment_reference'] for payment in scheduled_payments}

        for each in self:
            if each.move_type == 'in_invoice' and each.name in scheduled_payment_refs:
                each.payment_state = 'scheduled'


    bill_com_bill_id = fields.Char('Bill.com Bill ID', copy=False)
    bill_com_bill_sent_amount = fields.Monetary('Bill Total', copy=False)
    is_bill_com_bill = fields.Boolean("Is Bill Com Bill", default=False, copy=False)
    payment_state = fields.Selection(selection_add=[('scheduled', 'Scheduled')],
                                     string='Payment Status', store=True, readonly=True, copy=False, tracking=True,
                                     compute='_compute_payment_state')
    payment_ids = fields.Many2many('account.payment', 'account_invoice_payment_rel', 'invoice_id', 'payment_id',
                                   string="Payments", copy=False, readonly=True,
                                   help="""Technical field containing the payments for Invoices""")
    currency_exchange_rate = fields.Float('Exchange Rate', digits=(16, 5), store=True)

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        res = super(AccountMove, self)._onchange_partner_id()
        if self.partner_id and self.move_type in ['in_invoice', 'in_refund'] and \
                self.currency_id != self.partner_id.property_purchase_currency_id and \
                self.partner_id.property_purchase_currency_id.id:
            self.currency_id = self.partner_id.property_purchase_currency_id
        self._onchange_currency()
        return res

    @api.onchange('date', 'currency_id')
    def _onchange_currency(self):
        company_id = self.company_id
        company_currency_id = self.company_currency_id
        bill_currency = self.currency_id
        if bill_currency and company_currency_id != bill_currency:
            company_rec = bill_currency.rate_ids.filtered(lambda l: l.company_id == company_id)
            if company_rec:
                self.currency_exchange_rate = bill_currency.rate
            else:
                self.currency_exchange_rate = 1.00
        else:
            self.currency_exchange_rate = 0.00

    def action_bulk_send_bill_com_btn(self):
        context = self._context
        active_ids = context.get('active_ids')
        return {
            'name': _('Send to Bill.com'),
            'res_model': 'bulk.send.bill.com',
            'view_mode': 'form',
            'context': {
                'active_model': 'account.move',
                'active_ids': active_ids,
                # 'default_partner_id': self.id
            },
            'target': 'new',
            'type': 'ir.actions.act_window',
        }

    def check_line_description(self):
        if self._ids:
            cr = self._cr
            cr.execute("""select distinct(mv.name) from account_move_line line
            inner join account_move mv on mv.id= line.move_id
            where mv.move_type='in_invoice' and line.move_id in %s and line.name is null""",
                       (tuple(self.ids),))
            invoice_names = list(filter(None, map(lambda x: x[0], cr.fetchall())))
            if invoice_names:
                if len(invoice_names) == 1:
                    invoice_names = '\n'.join(invoice_names)
                    raise UserError(_("Please fill description in all invoice lines for %s.") % (invoice_names))
                else:
                    invoice_names = '\n'.join(invoice_names)
                    raise UserError(
                        _("Please fill description in all invoice lines for following invoices \n%s") % (invoice_names))

    def send_attachment_to_bill_com(self, attachment_id):
        error_logs_obj = self.env['bill.com.error.logs']
        attachment_id_brw = self.env['ir.attachment'].sudo().browse(attachment_id)
        res_id = attachment_id_brw.res_id
        bill_id_brw = self.env['account.move'].sudo().browse(res_id)
        company_id_brw = bill_id_brw.company_id
        bill_com_config_obj = self.env['bill.com.config']
        bill_com_config_obj = bill_com_config_obj.sudo().get_bill_com_config(company_id_brw.sudo().id)
        bill_name = bill_id_brw.name
        bill_com_bill_id = bill_id_brw.bill_com_bill_id
        attachment_name = attachment_id_brw.name
        try:
            if bill_com_config_obj:
                file_size = attachment_id_brw.file_size
                if file_size > 20000000:
                    raise Exception('File MUST be less than 20 MB.')
                mimetype = attachment_id_brw.mimetype
                file_name = attachment_id_brw.name
                bill_com_user_name = bill_com_config_obj.bill_com_user_name
                bill_com_password = bill_com_config_obj.bill_com_password
                bill_com_orgid = bill_com_config_obj.bill_com_orgid
                bill_com_devkey = bill_com_config_obj.bill_com_devkey
                bill_com_login_url = bill_com_config_obj.bill_com_login_url
                bill_com_bill_upload_attachment_url = bill_com_config_obj.bill_com_bill_upload_attachment_url
                if bill_com_bill_upload_attachment_url:
                    bill_com_service_obj = BillComService(bill_com_user_name, bill_com_password, bill_com_orgid, bill_com_devkey, bill_com_login_url)
                    bill_id_brw
                    data = {"id": bill_id_brw.bill_com_bill_id,"fileName": file_name}
                    final_dict = json.dumps(data)
                    file_path = '/tmp/%s' % (file_name)
                    fileobj = open(file_path, "wb+")
                    file_data = base64.decodebytes(attachment_id_brw.datas)
                    fileobj.write(file_data)
                    fileobj.close()
                    files = [('file',(file_name,open(file_path, 'rb+'),format(mimetype)))]
                    bill_com_upload_attachment_response = bill_com_service_obj.bill_upload_attachment(bill_com_bill_upload_attachment_url, final_dict, files)
                    if bill_com_upload_attachment_response:
                        documentUploadedId = bill_com_upload_attachment_response.get('documentUploadedId')
                        if documentUploadedId:
                            attachment_id_brw.write({'is_sent_on_bill_com': True, 'bill_com_document_upload_id': documentUploadedId})
                return {'type': 'ir.actions.client', 'tag': 'reload'}
        except Exception as e:
            error_message = "[(%s, (%s)], %s) - %s" % (bill_name, bill_com_bill_id, attachment_name, str(e))
            error_logs_obj.create_error_log('Upload Attachment', str(error_message))


    def set_bill_com_approvers(self):
        vendor_list = {
        '00901SVULPIIQQ36kcgg': {'vendor_name': 'L. P. Brown Company - Florence, AL','approver_name':'Dave Holden', 'bill_com_user_id': '00601CZEDQNZRSC6ckwl'},
        '00901FJVHBDOHI36kcgh': {'vendor_name': 'L. P. Brown Company - HQ','approver_name':'Dave Holden', 'bill_com_user_id': '00601CZEDQNZRSC6ckwl'},
        '00901UEIZBXUHZ14i2or': {'vendor_name': 'Southwestern Wire - HQ','approver_name':'Dave Holden', 'bill_com_user_id': '00601CZEDQNZRSC6ckwl'},
        '00901GSIFEBHGE36kd8e': {'vendor_name': 'Southwestern Wire - McClellan, CA','approver_name':'Dave Holden', 'bill_com_user_id': '00601CZEDQNZRSC6ckwl'},
        '00901CLDMJAVAP36kc6h': {'vendor_name': 'Beltservice Corporation - Grand Prairie, TX','approver_name':'Doug Cox', 'bill_com_user_id': '00601IXZVFLQIRE6ckzn'},
        '00901JKBZMHACQ109e7z': {'vendor_name': 'Beltservice Corporation - HQ','approver_name':'Doug Cox', 'bill_com_user_id': '00601IXZVFLQIRE6ckzn'},
        '00901UHZVPBLDH109e6a': {'vendor_name': 'Con-Belt Inc - HQ','approver_name':'Jeremy Axel', 'bill_com_user_id': '00601HVCVPWQNKP2tj3q'},
        '00901TRDSJGZCP109e6k': {'vendor_name': 'Christianson Systems, Inc. - HQ','approver_name':'Jeremy Axel', 'bill_com_user_id': '00601HVCVPWQNKP2tj3q'},
        '00901YPMBOIDKP2qaztg': {'vendor_name': 'AYEYE IO, LTD - HQ','approver_name':'Jeremy Axel', 'bill_com_user_id': '00601HVCVPWQNKP2tj3q'},
        '00901WBINHRSUPETecmz': {'vendor_name': 'Flywheel Brands (copy) - HQ','approver_name':'Jeremy Axel', 'bill_com_user_id': '00601UPULZEOWPDX4av0'},
        }
        bill_com_config_obj = self.env['bill.com.config']
        for bill_id_brw in self:
            vendor_id = bill_id_brw.partner_id
            company_id_brw = bill_id_brw.company_id
            bill_com_vendor_id = vendor_id.get_bill_com_vendor_id(vendor_id, company_id_brw)
            if bill_com_vendor_id and bill_com_vendor_id in vendor_list:
                bill_com_config_obj = bill_com_config_obj.sudo().get_bill_com_config(company_id_brw.sudo().id)
                bill_com_bill_id = bill_id_brw.bill_com_bill_id
                bill_com_user_id = vendor_list.get(bill_com_vendor_id).get('bill_com_user_id')
                final_dict = {"objectId": bill_com_bill_id, "entity": 'Bill', 'approvers': [bill_com_user_id]}
                final_dict = json.dumps(final_dict)
                bill_com_user_name = bill_com_config_obj.bill_com_user_name
                bill_com_password = bill_com_config_obj.bill_com_password
                bill_com_orgid = bill_com_config_obj.bill_com_orgid
                bill_com_devkey = bill_com_config_obj.bill_com_devkey
                bill_com_login_url = bill_com_config_obj.bill_com_login_url
                bill_com_set_bill_approver_url = bill_com_config_obj.bill_com_set_bill_approver_url
                if bill_com_set_bill_approver_url:
                    bill_com_service_obj = BillComService(bill_com_user_name, bill_com_password, bill_com_orgid, bill_com_devkey, bill_com_login_url)
                    bill_com_approver_response = bill_com_service_obj.set_billl_approvers(bill_com_set_bill_approver_url, final_dict)

    def send_to_bill_com(self):
        final_data, odoo_invoice_data = [], {}
        bill_com_config_obj = self.env['bill.com.config']
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        menu = self.env.ref('account.menu_finance')
        action_id = self.env.ref('account.action_move_in_invoice_type')
        # self.check_line_description()
        for each_inv in self:
            if each_inv.move_type == 'in_invoice':
                company_id_brw = each_inv.company_id
                bill_com_config_obj = bill_com_config_obj.sudo().get_bill_com_config(company_id_brw.sudo().id)
                if bill_com_config_obj:
                    invoice_line_ids = each_inv.invoice_line_ids
                    if not invoice_line_ids:
                        raise UserError(_("You cannot send this invoice as it doesn't contains bill lines."))
                    if menu and action_id:
                        invoice_url = base_url + '/web#id=%d&action=%s&view_type=form&model=account.move&menu_id=%s' % (each_inv.id, action_id.id, menu.id)
                    else:
                        invoice_url = base_url + '/web#id=%d&view_type=form&model=account.move' % (each_inv.id)
                    vendor_id = each_inv.partner_id
                    payment_term_id = each_inv.invoice_payment_term_id
                    odoo_payment_id = payment_term_id.get_bill_com_payment_term_id(payment_term_id, company_id_brw)
                    bill_com_vendor_id = vendor_id.get_bill_com_vendor_id(vendor_id, company_id_brw)
                    if not bill_com_vendor_id:
                        raise UserError(
                            _("Vendor not found! If a new Vendor is created, please ensure it is pushed to Bill.com."))
                    invoice_number = each_inv.ref if each_inv.ref else each_inv.name
                    amount_total = each_inv.amount_total
                    amount_residual = each_inv.amount_residual
                    odoo_invoice_data[invoice_number] = {'invoice_id': each_inv.id, 'invoice_total': amount_total}
                    invoice_date = each_inv.invoice_date.strftime('%Y-%m-%d')
                    invoice_date_due = each_inv.invoice_date_due
                    if invoice_date_due:
                        invoice_date_due = invoice_date_due.strftime('%Y-%m-%d')
                    else:
                        invoice_date_due = invoice_date
                    gl_posting_date = each_inv.date.strftime('%Y-%m-%d') or ''
                    exchangeRate = each_inv.currency_exchange_rate
                    all_line_items = []
                    if amount_total != amount_residual:
                        all_line_items = [
                            {"entity": "BillLineItem", "amount": amount_residual, 'description': 'Partial Payment',
                             "quantity": 1, "unitPrice": amount_residual}]
                        odoo_invoice_data[invoice_number].update({'invoice_total': amount_residual})
                    else:
                        for each_line in invoice_line_ids:
                            # price_subtotal = each_line.price_subtotal
                            quantity = each_line.quantity
                            name = each_line.name
                            price_unit = each_line.price_unit
                            # tax_ids = each_line.tax_ids
                            price_subtotal = each_line.price_total if each_line.price_total else each_line.price_subtotal
                            # price_subtotal = each_line._get_price_total_and_subtotal(price_unit=price_unit, taxes=tax_ids).get('price_total', 'price_subtotal')
                            a = {"entity": "BillLineItem", "amount": price_subtotal,"quantity": quantity, "unitPrice": price_unit}
                            if name:
                                a.update({"description": name})
                            account_id = each_line.account_id
                            if account_id and account_id.bill_com_coa_id:
                                a.update({"chartOfAccountId": account_id.bill_com_coa_id})
                            all_line_items.append(a)
                    data = {"obj": {"entity": "Bill", "isActive": "1", "vendorId": bill_com_vendor_id,
                                    "invoiceNumber": invoice_number, "invoiceDate": invoice_date,
                                    "dueDate": invoice_date_due, "glPostingDate": gl_posting_date,
                                    'description': invoice_url, 'poNumber': each_inv.invoice_origin[:20] if each_inv.invoice_origin else '',
                                    "billLineItems": all_line_items}}
                    if odoo_payment_id:
                        data["obj"].update({"paymentTermId": odoo_payment_id})
                    if exchangeRate > 0.0:
                        data["obj"].update({"exchangeRate": exchangeRate})
                    final_data.append(data)
        if final_data:
            if bill_com_config_obj.state == 'expired':
                raise ValidationError('Can not Send Bills To Bill.com as your subscription expired.')
            else:
                final_dict = {"bulk": final_data}
                # final_dict = json.dumps(final_dict)
                bill_com_user_name = bill_com_config_obj.bill_com_user_name
                bill_com_password = bill_com_config_obj.bill_com_password
                bill_com_orgid = bill_com_config_obj.bill_com_orgid
                bill_com_devkey = bill_com_config_obj.bill_com_devkey
                bill_com_login_url = bill_com_config_obj.bill_com_login_url
                bill_com_bill_create_url = bill_com_config_obj.bill_com_bill_create_url
                if bill_com_bill_create_url:
                    data = {
                        'bill_com_bill_create_url': bill_com_bill_create_url,
                        'bill_com_user_name': bill_com_user_name,
                        'bill_com_password': bill_com_password,
                        'bill_com_orgid': bill_com_orgid,
                        'bill_com_devkey': bill_com_devkey,
                        'bill_com_login_url': bill_com_login_url,
                        'final_dict': final_dict,
                    }
                    url = self.env['ir.config_parameter'].sudo().get_param('client_subscription.host_db_url')
                    if not url:
                        raise UserError("Please Configure Sevice DB URL in General settings.")

                    bill_data_response = requests.post(
                        f"{url}/send_to_bill_com",
                        json=data,
                        headers={'Content-Type': 'application/json'},
                        verify=False
                    )
                    print(" >>>>>>>>>>>>>>>>>>>>>>>> bill_data_response ", bill_data_response)
                    result = bill_data_response.json()
                    print("================ result", result)
                    if result.get('result') and result['result'].get('status') == 'success':
                        bill_com_invoice_data = result['result'].get('data', [])
                        print("====================== bill_com_invoice_data", bill_com_invoice_data)
                        if bill_com_invoice_data:
                            for invoice_number, bill_com_bill_id in bill_com_invoice_data.items():
                                print("===============================", odoo_invoice_data)
                                odoo_inv_data = odoo_invoice_data.get(invoice_number)
                                print("===============================", odoo_inv_data)
                                odoo_inv_id = odoo_inv_data.get('invoice_id', False)
                                odoo_invoice_total = odoo_inv_data.get('invoice_total', False)
                                odoo_inv_id_brw = self.browse(odoo_inv_id)
                                print(">>>>>>>>>>>>>>>>>>>>>. odoo_inv_id_brw", odoo_inv_id_brw)
                                odoo_inv_id_brw.write({'bill_com_bill_id': bill_com_bill_id, 'bill_com_bill_sent_amount': odoo_invoice_total, 'is_bill_com_bill' : True})
        attachment_id_brw = self.env['ir.attachment'].sudo().search([('res_id', 'in', self.ids), ('res_model', '=', 'account.move')])
        for each_attch in attachment_id_brw:
            self.send_attachment_to_bill_com(each_attch.id)
        self.set_bill_com_approvers()    

    def update_to_bill_com(self):
        final_data, odoo_invoice_data = [], {}
        bill_com_config_obj = self.env['bill.com.config']
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        menu = self.env.ref('account.menu_finance')
        action_id = self.env.ref('account.action_move_in_invoice_type')
        # self.check_line_description()
        for each_inv in self:
            if each_inv.move_type == 'in_invoice':
                company_id_brw = each_inv.company_id
                bill_com_config_obj = bill_com_config_obj.sudo().get_bill_com_config(company_id_brw.sudo().id)
                bill_com_bill_id = each_inv.bill_com_bill_id
                if bill_com_config_obj and bill_com_bill_id:
                    invoice_line_ids = each_inv.invoice_line_ids
                    if not invoice_line_ids:
                        raise UserError(_("You cannot send this invoice as it doesn't contains bill lines."))
                    if menu and action_id:
                        invoice_url = base_url + '/web#id=%d&action=%s&view_type=form&model=account.move&menu_id=%s' % (each_inv.id, action_id.id, menu.id)
                    else:
                        invoice_url = base_url + '/web#id=%d&view_type=form&model=account.move' % (each_inv.id)
                    vendor_id = each_inv.partner_id
                    payment_term_id = each_inv.invoice_payment_term_id
                    odoo_payment_id = payment_term_id.get_bill_com_payment_term_id(payment_term_id, company_id_brw)
                    bill_com_vendor_id = vendor_id.get_bill_com_vendor_id(vendor_id, company_id_brw)
                    if not bill_com_vendor_id:
                        raise UserError(
                            _("Vendor not found! If a new Vendor is created, please ensure it is pushed to Bill.com."))
                    invoice_number = each_inv.ref if each_inv.ref else each_inv.name
                    odoo_invoice_data[invoice_number] = each_inv.id
                    invoice_date = each_inv.invoice_date.strftime('%Y-%m-%d')
                    invoice_date_due = each_inv.invoice_date_due
                    if invoice_date_due:
                        invoice_date_due = invoice_date_due.strftime('%Y-%m-%d')
                    else:
                        invoice_date_due = invoice_date
                    gl_posting_date = each_inv.date.strftime('%Y-%m-%d') or ''
                    exchangeRate = each_inv.currency_exchange_rate
                    all_line_items = []
                    for each_line in invoice_line_ids:
                        # price_subtotal = each_line.price_subtotal
                        quantity = each_line.quantity
                        name = each_line.name
                        price_unit = each_line.price_unit
                        # tax_ids = each_line.tax_ids
                        price_subtotal = each_line.price_total if each_line.price_total else each_line.price_subtotal
                        # price_subtotal = each_line._get_price_total_and_subtotal(price_unit=price_unit, taxes=tax_ids).get('price_total','price_subtotal')
                        a = {"entity": "BillLineItem", "amount": price_subtotal,"quantity": quantity, "unitPrice": price_unit}
                        if name:
                            a.update({"description": name})
                        account_id = each_line.account_id
                        if account_id and account_id.bill_com_coa_id:
                            a.update({"chartOfAccountId": account_id.bill_com_coa_id})
                        else:
                            a.update({"chartOfAccountId": ""})
                        all_line_items.append(a)
                    isActive = '2' if each_inv.state == 'draft' else '1'
                    data = {"obj": {"entity": "Bill", "id": bill_com_bill_id, "isActive": isActive,
                                    "vendorId": bill_com_vendor_id, "invoiceNumber": invoice_number,
                                    "invoiceDate": invoice_date, "dueDate": invoice_date_due,
                                    "glPostingDate": gl_posting_date, 'description': invoice_url,
                                    'poNumber': each_inv.invoice_origin[:20] if each_inv.invoice_origin else '', "billLineItems": all_line_items}}
                    if odoo_payment_id:
                        data["obj"].update({"paymentTermId": odoo_payment_id})
                    if exchangeRate > 0.0:
                        data["obj"].update({"exchangeRate": exchangeRate})
                    final_data.append(data)
        if final_data:
            final_dict = {"bulk": final_data}
            final_dict = json.dumps(final_dict)
            bill_com_user_name = bill_com_config_obj.bill_com_user_name
            bill_com_password = bill_com_config_obj.bill_com_password
            bill_com_orgid = bill_com_config_obj.bill_com_orgid
            bill_com_devkey = bill_com_config_obj.bill_com_devkey
            bill_com_login_url = bill_com_config_obj.bill_com_login_url
            bill_com_bill_update_url = bill_com_config_obj.bill_com_bill_update_url
            if bill_com_bill_update_url:
                bill_com_service_obj = BillComService(bill_com_user_name, bill_com_password, bill_com_orgid,
                                                      bill_com_devkey, bill_com_login_url)
                bill_com_invoice_data = bill_com_service_obj.create_update_bill_api(bill_com_bill_update_url,
                                                                                    final_dict)
        self.set_bill_com_approvers()

    def button_draft(self):
        context = self._context
        res = super(AccountMove, self).button_draft()
        if 'default_move_type' in context:
            self.update_to_bill_com()
        return res

    def action_post(self):
        context = self._context
        res = super(AccountMove, self).action_post()
        if 'from_import_bill' not in context:
            self.update_to_bill_com()
        return res


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    @api.depends('currency_id', 'company_id', 'move_id.date')
    def _compute_currency_rate(self):
        @lru_cache()
        def get_rate(from_currency, to_currency, company, date):
            return self.env['res.currency']._get_conversion_rate(
                from_currency=from_currency,
                to_currency=to_currency,
                company=company,
                date=date,
            )
        for line in self:
            if line.move_id and line.move_id.currency_exchange_rate:
                line.currency_rate = line.move_id.currency_exchange_rate
            else:
                line.currency_rate = get_rate(
                    from_currency=line.company_currency_id,
                    to_currency=line.currency_id,
                    company=line.company_id,
                    date=line.move_id.invoice_date or line.move_id.date or fields.Date.context_today(line),
                )
            
    def _get_computed_price_unit(self):
        product_price_unit = super(AccountMoveLine, self)._get_computed_price_unit()
        company = self.move_id.company_id
        currency = self.move_id.currency_id
        company_currency = company.currency_id
        if currency and currency != company_currency:
            product_price_unit = self.product_id.standard_price * self.move_id.currency_exchange_rate
        return product_price_unit

    def remove_move_reconcile(self):
        context = self._context
        if not 'from_bill_com_cancel' in context:
            for each in self:
                payment_id = each.payment_id
                if payment_id and payment_id.bill_com_payment_id:
                    raise ValidationError(_("Error! Payment has been processed via Bill.com for this Bill."))
        res = super(AccountMoveLine, self).remove_move_reconcile()
        return res
