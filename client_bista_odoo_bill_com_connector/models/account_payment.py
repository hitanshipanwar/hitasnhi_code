# -*- encoding: utf-8 -*-
##############################################################################
#
# Bista Solutions Pvt. Ltd
# Copyright (C) 2020 (http://www.bistasolutions.com)
#
##############################################################################

from odoo import api, fields, models, _
import time
# from .connection import BillComService
import json
from datetime import timedelta, date
from odoo.exceptions import UserError, ValidationError


class account_payment(models.Model):
    _inherit = "account.payment"

    bill_com_payment_id = fields.Char('Bill.com Payment ID', copy=False)
    bill_com_payment_status = fields.Char('Bill.Com Payment Status', copy=False)
    currency_exchange_rate = fields.Float('Exchange Rate', digits=(16, 5))
    bill_com_fund_transfer_id = fields.Char('Bill.Com Batch ID', copy=False)
    vendor_name = fields.Char('Vendor Name', copy=False)
    payment_date = fields.Date(string='Payment Date', store=True, copy=False)

    @api.model
    def default_get(self, default_fields):
        rec = super(account_payment, self).default_get(default_fields)
        context = self._context or {}
        active_model = context.get('active_model', '')
        active_ids = context.get('active_ids', [])
        if active_model and active_model == 'account.move':
            selected_wrong_records = self.env[active_model].sudo().search([('id', 'in', active_ids),('bill_com_bill_id','!=', False)])
            if selected_wrong_records:
                raise ValidationError('Unauthorized Entry! Bills sent to Bill.com can only be paid in Bill.com system')
        return rec

    def bill_com_cancel(self):
        for each in self:
            bill_com_payment_id = each.bill_com_payment_id
            if bill_com_payment_id:
                company_id_brw = each.company_id
                bill_com_config_obj = self.env['bill.com.config'].sudo().get_bill_com_config(company_id_brw.sudo().id)
                if bill_com_config_obj:
                    bill_com_user_name = bill_com_config_obj.bill_com_user_name
                    bill_com_password = bill_com_config_obj.bill_com_password
                    bill_com_orgid = bill_com_config_obj.bill_com_orgid
                    bill_com_devkey = bill_com_config_obj.bill_com_devkey
                    bill_com_login_url = bill_com_config_obj.bill_com_login_url
                    bill_com_payment_import_url = bill_com_config_obj.bill_com_payment_import_url
                    bill_com_service_obj = BillComService(bill_com_user_name, bill_com_password, bill_com_orgid,
                                                          bill_com_devkey, bill_com_login_url)
                    filter_data = {"start": 0, "max": 999,
                                   "filters": [{"field": "id", "op": "=", "value": bill_com_payment_id}]}
                    filter_data = json.dumps(filter_data)
                    payment_data = bill_com_service_obj.import_bill_payments(bill_com_payment_import_url, filter_data)
                    if payment_data:
                        status = payment_data[0].get('status', '')
                        if status not in ('3', '4'):
                            raise UserError(_("You cannot cancel this payment because it is not cancelled on Bill.com"))
                        else:
                            each.with_context({'from_bill_com_cancel': True}).action_draft()
                            each.action_cancel()
                            each.bill_com_payment_status = 'Cancelled'

    def _prepare_move_line_default_vals(self, write_off_line_vals=None, force_balance=None):
        ''' Prepare the dictionary to create the default account.move.lines for the current payment.
        :param write_off_line_vals: Optional list of dictionaries to create a write-off account.move.line easily containing:
            * amount:       The amount to be added to the counterpart amount.
            * name:         The label to set on the line.
            * account_id:   The account on which create the write-off.
        :return: A list of python dictionary to be passed to the account.move.line's 'create' method.
        '''
        self.ensure_one()
        write_off_line_vals = write_off_line_vals or {}

        if not self.outstanding_account_id:
            raise UserError(_(
                "You can't create a new payment without an outstanding payments/receipts account set either on the company or the %s payment method in the %s journal.",
                self.payment_method_line_id.name, self.journal_id.display_name))

        # Compute amounts.
        write_off_line_vals_list = write_off_line_vals or []
        write_off_amount_currency = sum(x['amount_currency'] for x in write_off_line_vals_list)
        write_off_balance = sum(x['balance'] for x in write_off_line_vals_list)

        if self.payment_type == 'inbound':
            # Receive money.
            liquidity_amount_currency = self.amount
        elif self.payment_type == 'outbound':
            # Send money.
            liquidity_amount_currency = -self.amount
        else:
            liquidity_amount_currency = 0.0

        new_currency_exchange_rate = self.currency_exchange_rate
        if self.currency_id != self.company_id.currency_id and new_currency_exchange_rate > 0:
            write_off_balance = write_off_amount_currency / new_currency_exchange_rate
            liquidity_balance = liquidity_amount_currency / new_currency_exchange_rate
        else:
            write_off_balance = self.currency_id._convert(
                write_off_amount_currency,
                self.company_id.currency_id,
                self.company_id,
                self.date,
            )

            liquidity_balance = self.currency_id._convert(
                liquidity_amount_currency,
                self.company_id.currency_id,
                self.company_id,
                self.date,
            )
        counterpart_amount_currency = -liquidity_amount_currency - write_off_amount_currency
        counterpart_balance = -liquidity_balance - write_off_balance
        currency_id = self.currency_id.id

        # Compute a default label to set on the journal items.
        # liquidity_line_name = ''.join(x[1] for x in self._get_liquidity_aml_display_name_list())
        # counterpart_line_name = ''.join(x[1] for x in self._get_counterpart_aml_display_name_list())
        liquidity_line_name = ''.join(x[1] for x in self._get_aml_default_display_name_list())
        counterpart_line_name = ''.join(x[1] for x in self._get_aml_default_display_name_list())


        line_vals_list = [
            # Liquidity line.
            {
                'name': liquidity_line_name,
                'date_maturity': self.date,
                'amount_currency': liquidity_amount_currency,
                'currency_id': currency_id,
                'debit': liquidity_balance if liquidity_balance > 0.0 else 0.0,
                'credit': -liquidity_balance if liquidity_balance < 0.0 else 0.0,
                'partner_id': self.partner_id.id,
                'account_id': self.outstanding_account_id.id,
            },
            # Receivable / Payable.
            {
                'name': counterpart_line_name,
                'date_maturity': self.date,
                'amount_currency': counterpart_amount_currency,
                'currency_id': currency_id,
                'debit': counterpart_balance if counterpart_balance > 0.0 else 0.0,
                'credit': -counterpart_balance if counterpart_balance < 0.0 else 0.0,
                'partner_id': self.partner_id.id,
                'account_id': self.destination_account_id.id,
            },
        ]
        return line_vals_list + write_off_line_vals_list

class payment_register(models.TransientModel):
    _inherit = 'account.payment.register'

    group_payment_invisible = fields.Boolean('Group Payment Invisible', copy=False, default=False)

    @api.model
    def default_get(self, fields_list):
        active_ids = self._context.get('active_ids', [])
        if active_ids:
            account_move_obj = self.env['account.move'] 
            invoices = account_move_obj.browse(active_ids)
            selected_wrong_records = account_move_obj.sudo().search([('id', 'in', active_ids),('bill_com_bill_id','!=', False)])
            if selected_wrong_records:
                raise ValidationError('Unauthorized Entry! Bills sent to Bill.com can only be paid in Bill.com system.')
        return super(payment_register, self).default_get(fields_list)