from odoo import models, fields, api, _
from odoo.fields import Command
from datetime import datetime, timedelta
import logging
_logger = logging.getLogger(__name__)
import base64
import io
import pandas as pd
import requests
from odoo.exceptions import UserError

class SaleOrder(models.Model):
    _inherit = 'crm.team'

    is_check = fields.Boolean(string="DST")

class StockPicking(models.Model):

    _inherit = 'stock.picking'

    def button_validate(self):
        res = super().button_validate()
        for picking in self:
            _logger.info("Validating Picking: %s", picking.name)
            if picking.picking_type_id.code == 'outgoing' and picking.sale_id:
                order = picking.sale_id
                if order and order.team_id and order.team_id.is_check:
                    updated_quantities = {}
                    for move in picking.move_ids_without_package:
                        sale_line = move.sale_line_id
                        if sale_line:
                            updated_quantities[sale_line.id] = updated_quantities.get(sale_line.id, 0) + move.quantity
                    if order.invoice_status == 'to invoice' and updated_quantities:
                        context = {
                            'invoice_from_backorder': True,
                            'updated_quantities': updated_quantities,
                            'default_invoice_origin': picking.name,
                        }
                        search_inv = self.env['account.move'].search([('invoice_origin','=', picking.name)])
                        _logger.info("search_inv ***************%s", search_inv)
                        if not search_inv:
                            invoice = order.with_context(**context)._create_invoices()
                            _logger.info("invoice ************%s", invoice)
                            if invoice:
                                invoice.write({'invoice_origin': picking.name})
                                invoice.action_post()
        return res

class SaleOrderInherit(models.Model):
    _inherit = 'sale.order'


    is_sale_draft = fields.Boolean(string="Sale Order Update")
    is_shopify_mismatch = fields.Boolean(string="Shopify Mismatch")
    shopify_payment_id = fields.Char(string="Payment Id")
    txn_amount_shopify = fields.Float(string="Shopify Amount")
    txn_status = fields.Char(string="Txn Status")
    shopify_payment_id_capture = fields.Char(string="Capture Payment Id")
    txn_amount_shopify_capture = fields.Float(string="Shopify Capture Amount")
    txn_status_capture = fields.Char(string="Txn Capture Status")
    is_auth_capture_mismatch = fields.Boolean(string="Capture Auth Mismatch")
    shopify_payment_id_refund = fields.Char(string="Refund Payment Id")
    txn_amount_shopify_refund = fields.Float(string="Shopify Refund Amount")
    txn_status_refund = fields.Char(string="Txn Refund Status")

    def transaction_value_update(self):
        self.ensure_one()

        channel_mapping_ids = self.channel_mapping_ids and self.channel_mapping_ids[0] or False
        channel_id = channel_mapping_ids.channel_id if channel_mapping_ids else False
        order_id = channel_mapping_ids.store_order_id if channel_mapping_ids else False

        if not channel_id or not order_id:
            _logger.info("Missing channel or order ID.")
            return

        channel = self.env['multi.channel.sale'].search([('id', '=', channel_id.id)], limit=1)
        if not channel:
            _logger.info("Multi-channel sale record not found.")
            return

        shop_url = channel.url.replace("http://", "https://")
        access_token = channel.api_key

        if not access_token:
            _logger.info("Access token not found.")
            return

        endpoint = f"{shop_url}/admin/api/2025-04/orders/{order_id}/transactions.json"
        headers = {
            "Content-Type": "application/json",
            "X-Shopify-Access-Token": access_token,
        }

        try:
            response = requests.get(endpoint, headers=headers)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            _logger.error("Shopify API request failed: %s", e)
            return

        transactions = response.json().get('transactions', [])
        _logger.info("transactions ********* %s", transactions)

        if not transactions:
            _logger.info("No transactions found for this order.")
            return

        # Authorization
        transaction_data = next(
            (txn for txn in transactions
             if not txn.get('parent_id') and (len(transactions) == 1 or txn.get('status') == 'success') 
             and txn.get('kind') == 'authorization'),
            False
        ) # Abhishek

        # Sale transaction
        if not transaction_data:
            transaction_data = next(
                (txn for txn in transactions
                 if not txn.get('parent_id') and (len(transactions) == 1 or txn.get('status') == 'success') 
                 and txn.get('kind') == 'sale'),
                False
            ) # Abhishek

        # Capture transaction
        transaction_data_capture = next(
            (txn for txn in transactions
             if (len(transactions) == 1 or txn.get('status') == 'success')
             and txn.get('kind') == 'capture'),
            False
        ) #Abhishek

        if transaction_data or transaction_data_capture:
            payment_id = gateway = amount = status = None
            payment_id_trimmed = None
            if transaction_data:
                payment_id = transaction_data.get('payment_id')
                gateway = transaction_data.get('gateway')
                amount = transaction_data.get('amount')
                status = transaction_data.get('status')

            if payment_id and gateway and gateway.startswith('authorize'):
                payment_id_trimmed = payment_id[:-5]
            else:
                payment_id_trimmed = payment_id

            # Process capture txn
            gateway_capture = payment_id_capture = txn_amount_capture = txn_status_capture = None
            if transaction_data_capture:
                gateway_capture = transaction_data_capture.get('gateway')
                txn_amount_capture = transaction_data_capture.get('amount')
                txn_status_capture = transaction_data_capture.get('status')

                if gateway_capture and gateway_capture.startswith('authorize'):
                    payment_id_capture = transaction_data_capture.get('payment_id')

            # Update sale.order
            self.env.cr.execute("""
                UPDATE sale_order
                SET shopify_payment_id = %s,
                    txn_amount_shopify = %s,
                    txn_status = %s,
                    shopify_payment_id_capture = %s,
                    txn_amount_shopify_capture = %s,
                    txn_status_capture = %s
                WHERE id = %s
            """, (
                payment_id_trimmed, amount, status,
                payment_id_capture, txn_amount_capture, txn_status_capture,
                self.id
            ))

            # Update account.move (invoices)
            if self.invoice_ids:
                invoice_ids = tuple(self.invoice_ids.ids)
                self.env.cr.execute("""
                    UPDATE account_move
                    SET shopify_payment_id = %s,
                        txn_amount_shopify = %s,
                        txn_status = %s,
                        shopify_payment_id_capture = %s,
                        txn_amount_shopify_capture = %s,
                        txn_status_capture = %s,
                        payment_reference = %s,
                        ref = %s
                    WHERE id IN %s
                """, (
                    payment_id_trimmed, amount, status,
                    payment_id_capture, txn_amount_capture, txn_status_capture,
                    payment_id_trimmed, payment_id_trimmed,
                    invoice_ids
                ))

                for invoice in self.invoice_ids:
                    payments = self.env['account.payment'].search([
                        ('ref', '=', invoice.ref)
                    ])
                    for payment in payments:
                        payment.write({
                            'shopify_payment_id': payment_id_trimmed,
                            'txn_amount_shopify': amount,
                            'txn_status': status,
                            'shopify_payment_id_capture': payment_id_capture,
                            'txn_amount_shopify_capture': txn_amount_capture,
                            'txn_status_capture': txn_status_capture,
                            'ref': payment_id_trimmed,
                        })
        else:
            _logger.info("No valid transaction found.")
         # === Refund transaction logic (added after existing logic) ===
        transaction_data_refund = next(
            (txn for txn in transactions
             if (len(transactions) == 1 or txn.get('status') == 'success')
             and txn.get('kind') == 'refund'),
            False
        )

        if transaction_data_refund:
            gateway_refund = transaction_data_refund.get('gateway')
            payment_id_refund = transaction_data_refund.get('receipt', {}).get('network_trans_id')
            txn_amount_refund = transaction_data_refund.get('amount')
            txn_status_refund = transaction_data_refund.get('status')

            # Update sale.order
            self.env.cr.execute("""
                UPDATE sale_order
                SET shopify_payment_id_refund = %s,
                    txn_amount_shopify_refund = %s,
                    txn_status_refund = %s
                WHERE id = %s
            """, (
                payment_id_refund,
                txn_amount_refund,
                txn_status_refund,
                self.id
            ))

            # Update account.move
            if self.invoice_ids:
                invoice_ids = tuple(self.invoice_ids.ids)
                self.env.cr.execute("""
                    UPDATE account_move
                    SET shopify_payment_id_refund = %s,
                        txn_amount_shopify_refund = %s,
                        txn_status_refund = %s
                    WHERE id IN %s
                """, (
                    payment_id_refund,
                    txn_amount_refund,
                    txn_status_refund,
                    invoice_ids
                ))

                for invoice in self.invoice_ids:
                    payments = self.env['account.payment'].search([
                        ('ref', '=', invoice.ref)
                    ])
                    for payment in payments:
                        payment.write({
                            'shopify_payment_id_refund': payment_id_refund,
                            'txn_amount_shopify_refund': txn_amount_refund,
                            'txn_status_refund': txn_status_refund,
                        })

    @api.model
    def create(self, vals):
        if not vals.get('name'):
            if vals.get('team_id'):
                team_id = self.env['crm.team'].browse(vals.get('team_id'))
                if team_id.is_check:
                    sequence = self.env['ir.sequence'].next_by_code('sale.order.reference')
                    vals['name'] = sequence
        return super(SaleOrderInherit, self).create(vals)

    def _prepare_invoice(self):
        values = super(SaleOrderInherit, self)._prepare_invoice()
        values['shopify_payment_id'] = self.shopify_payment_id
        values['txn_amount_shopify'] = self.txn_amount_shopify
        values['txn_status'] = self.txn_status
        #Abhishek
        values['shopify_payment_id_capture'] = self.shopify_payment_id_capture
        values['txn_amount_shopify_capture'] = self.txn_amount_shopify_capture
        values['txn_status_capture'] = self.txn_status_capture
        #Abhishek
        values['shopify_payment_id_refund'] = self.shopify_payment_id_refund
        values['txn_amount_shopify_refund'] = self.txn_amount_shopify_refund
        values['txn_status_refund'] = self.txn_status_refund
        if self.shopify_payment_id:
            values['ref'] = self.shopify_payment_id
            values['payment_reference'] = self.shopify_payment_id
        return values

class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    partner_last_name = fields.Char(related='partner_id.name', string='Last Name')

class AccountMoveInh(models.Model):
    _inherit = 'account.move'

    is_account_payment = fields.Boolean(string="Invoice update")
    shopify_payment_id = fields.Char(string="Payment Id")
    txn_amount_shopify = fields.Float(string="Shopify Amount")
    txn_status = fields.Char(string="Txn Status")
    shopify_payment_id_capture = fields.Char(string="Capture Payment Id")
    txn_amount_shopify_capture = fields.Float(string="Shopify Capture Amount")
    txn_status_capture = fields.Char(string="Txn Capture Status")
    shopify_payment_id_refund = fields.Char(string="Refund Payment Id")
    txn_amount_shopify_refund = fields.Float(string="Shopify Refund Amount")
    txn_status_refund = fields.Char(string="Txn Refund Status")

# Inheriting account payment model
class O2bRegisterPaymentInh(models.TransientModel):
    _inherit = "account.payment.register"

    shopify_payment_id = fields.Char(string="Payment Id")
    txn_amount_shopify = fields.Float(string="Shopify Amount")
    txn_status = fields.Char(string="Txn Status")
    shopify_payment_id_capture = fields.Char(string="Capture Payment Id")
    txn_amount_shopify_capture = fields.Float(string="Shopify Capture Amount")
    txn_status_capture = fields.Char(string="Txn Capture Status")
    shopify_payment_id_refund = fields.Char(string="Refund Payment Id")
    txn_amount_shopify_refund = fields.Float(string="Shopify Refund Amount")
    txn_status_refund = fields.Char(string="Txn Refund Status")

    @api.model
    def _get_wizard_values_from_batch(self, batch_result):
        ''' Extract values from the batch passed as parameter (see '_get_batches')
        to be mounted in the wizard view.
        :param batch_result:    A batch returned by '_get_batches'.
        :return:                A dictionary containing valid fields
        '''
        payment_values = batch_result['payment_values']
        lines = batch_result['lines']
        company = min(lines.company_id, key=lambda c: len(c.parent_ids))

        source_amount = abs(sum(lines.mapped('amount_residual')))
        if payment_values['currency_id'] == company.currency_id.id:
            source_amount_currency = source_amount
        else:
            source_amount_currency = abs(sum(lines.mapped('amount_residual_currency')))

        move_id = lines.mapped('move_id')
        return {
            'company_id': company.id,
            'partner_id': payment_values['partner_id'],
            'partner_type': payment_values['partner_type'],
            'payment_type': payment_values['payment_type'],
            'source_currency_id': payment_values['currency_id'],
            'source_amount': source_amount,
            'source_amount_currency': source_amount_currency,
            'shopify_payment_id': move_id.shopify_payment_id,
            'txn_amount_shopify': move_id.txn_amount_shopify,
            'txn_status': move_id.txn_status,
            'shopify_payment_id_capture': move_id.shopify_payment_id_capture,
            'txn_amount_shopify_capture': move_id.txn_amount_shopify_capture,
            'txn_status_capture': move_id.txn_status_capture,
            'shopify_payment_id_refund': move_id.shopify_payment_id_refund,
            'txn_amount_shopify_refund': move_id.txn_amount_shopify_refund,
            'txn_status_refund': move_id.txn_status_refund,
        }

    @api.model
    def _create_payment_vals_from_wizard(self, batch_result):
        payment_vals = super()._create_payment_vals_from_wizard(batch_result)
        payment_vals['shopify_payment_id'] = self.shopify_payment_id
        payment_vals['txn_amount_shopify'] = self.txn_amount_shopify
        payment_vals['txn_status'] = self.txn_status
        # Abhishek
        payment_vals['shopify_payment_id_capture'] = self.shopify_payment_id_capture
        payment_vals['txn_amount_shopify_capture'] = self.txn_amount_shopify_capture
        payment_vals['txn_status_capture'] = self.txn_status_capture
        # Abhishek
        payment_vals['shopify_payment_id_refund'] = self.shopify_payment_id_refund
        payment_vals['txn_amount_shopify_refund'] = self.txn_amount_shopify_refund
        payment_vals['txn_status_refund'] = self.txn_status_refund

        return payment_vals

class BankRecWidget(models.Model):
    _inherit = 'bank.rec.widget'

    def _prepare_embedded_views_data(self):
        self.ensure_one()
        st_line = self.st_line_id

        context = {
            'search_view_ref': 'account_accountant.view_account_move_line_search_bank_rec_widget',
            'tree_view_ref': 'account_accountant.view_account_move_line_list_bank_rec_widget',
        }

        # Default filter to search by statement line's amount
        # if st_line.amount:
        #     context['search_default_name'] = abs(st_line.amount)

        # Default filter to search by filtering out the last name from statement label
        # last_name = None
        # if st_line.payment_ref:
        #     parts = st_line.payment_ref.strip().split()
        #     email_index = next((i for i, part in enumerate(parts) if '@' in part), None)
        #     if email_index is not None and email_index > 0:
        #         name_parts = parts[:email_index]
        #     else:
        #         name_parts = parts
        #     if name_parts:
        #         last_name = name_parts[-1]
        #         context['search_default_partner_last_name'] = last_name

        # # Odoo's default filter to search by partner (Modified: To be used last name is not found)
        # if not last_name and self.partner_id:
        #     context['search_default_partner_id'] = self.partner_id.id

        if st_line.ref:
            context['search_default_name'] = st_line.ref

        dynamic_filters = []

        # == Dynamic Customer/Vendor filter ==
        journal = st_line.journal_id

        account_ids = set()

        inbound_accounts = journal._get_journal_inbound_outstanding_payment_accounts() - journal.default_account_id
        outbound_accounts = journal._get_journal_outbound_outstanding_payment_accounts() - journal.default_account_id

        # Matching on debit account.
        for account in inbound_accounts:
            account_ids.add(account.id)

        # Matching on credit account.
        for account in outbound_accounts:
            account_ids.add(account.id)

        rec_pay_matching_filter = {
            'name': 'receivable_payable_matching',
            'description': _("Customer/Vendor"),
            'domain': [
                '|',
                # Matching invoices.
                '&',
                ('account_id.account_type', 'in', ('asset_receivable', 'liability_payable')),
                ('payment_id', '=', False),
                # Matching Payments.
                '&',
                ('account_id', 'in', tuple(account_ids)),
                ('payment_id', '!=', False),
            ],
            'no_separator': True,
            'is_default': False,
        }

        misc_matching_filter = {
            'name': 'misc_matching',
            'description': _("Misc"),
            'domain': ['!'] + rec_pay_matching_filter['domain'],
            'is_default': False,
        }

        dynamic_filters.append(rec_pay_matching_filter)
        dynamic_filters.append(misc_matching_filter)

        # Default filter to search matching entries 3 days prior and 3 days next to statement date
        # if st_line.date:
        #     date_format = '%Y-%m-%d'
        #     st_date = datetime.strptime(str(st_line.date), date_format)
        #     date_from = (st_date - timedelta(days=3)).strftime(date_format)
        #     date_to = (st_date + timedelta(days=3)).strftime(date_format)
        #     date_domain = [('date', '>=', date_from),('date', '<=', date_to)]
        #     date_filter = {
        #         'name': '3_days_difference',
        #         'description': ('3 Days Diff'),
        #         'domain': date_domain,
        #         'is_default': True,
        #         'no_separator': False,
        #     }
        #     dynamic_filters.append(date_filter)

        # Stringify the domain.
        for dynamic_filter in dynamic_filters:
            dynamic_filter['domain'] = str(dynamic_filter['domain'])

        return {
            'amls': {
                'domain': st_line._get_default_amls_matching_domain(),
                'dynamic_filters': dynamic_filters,
                'context': context,
            },
        }

class ShopifyMismatchImport(models.TransientModel):
    _name = 'shopify.mismatch.import'
    _description = 'Import Shopify Mismatches'

    file = fields.Binary("Upload Excel File", required=True)
    file_name = fields.Char("File Name")

    def action_import(self):
        # Decode file
        data = base64.b64decode(self.file)
        df = pd.read_excel(io.BytesIO(data))

        for index, row in df.iterrows():
            order_name = str(row.get('Name')).replace('#', '')
            order = self.env['sale.order'].search([('name', 'ilike', order_name)], limit=1)
            if order:
                order.is_shopify_mismatch = True

class AccountPayment(models.Model):
    _inherit = 'account.payment'

    shopify_payment_id = fields.Char(string="Payment Id")
    txn_amount_shopify = fields.Float(string="Shopify Amount")
    txn_status = fields.Char(string="Txn Status")
    shopify_payment_id_capture = fields.Char(string="Capture Payment Id")
    txn_amount_shopify_capture = fields.Float(string="Shopify Capture Amount")
    txn_status_capture = fields.Char(string="Txn Capture Status")
    shopify_payment_id_refund = fields.Char(string="Refund Payment Id")
    txn_amount_shopify_refund = fields.Float(string="Shopify Refund Amount")
    txn_status_refund = fields.Char(string="Txn Refund Status")

    # @api.model_create_multi
    # def create(self, vals):
    #     records = super(AccountPayment, self).create(vals)
    #     for record in records:
    #         # Invoice Order
    #         invoice_order = False
    #         if record and record.ref:
    #             invoice_order = self.env['account.move'].search([('name', '=', record.ref)], limit=1)

    #         if not invoice_order:
    #             _logger.info("Invoice Order Not Found.")

    #         # Sale Order
    #         sale_order = False
    #         if invoice_order:
    #             sale_order = self.env['sale.order'].search([('name', '=', invoice_order.invoice_origin)], limit=1)

    #         if not sale_order:
    #             _logger.info("Sale Order Not Found.")

    #         _logger.info("sale_order.channel_mapping_ids ********** %s", sale_order.channel_mapping_ids)
    #         channel_mapping_ids = False
    #         channel_id = False
    #         order_id = False

    #         if sale_order and sale_order.channel_mapping_ids:
    #             channel_mapping_ids = sale_order.channel_mapping_ids[0]
    #             channel_id = channel_mapping_ids.channel_id
    #             order_id = channel_mapping_ids.store_order_id
    #         else:
    #             _logger.info("No channel mappings.")

    #         channel = False

    #         if channel_id:
    #             channel = self.env['multi.channel.sale'].search([('id', '=', channel_id.id )], limit=1)

    #         if not channel:
    #             _logger.info("Multi-channel sale record not found.")

    #         shop_url = channel.url.replace("http://", "https://")

    #         access_token = channel.api_key

    #         if not order_id:
    #             _logger.info("Shopify Order ID not set.")

    #         if not access_token:
    #             _logger.info("Access Token not found.")

    #         if access_token and order_id:
    #             endpoint = f"{shop_url}/admin/api/2025-04/orders/{order_id}/transactions.json"

    #             headers = {
    #                 "Content-Type": "application/json",
    #                 "X-Shopify-Access-Token": access_token,
    #             }

    #             response = requests.get(endpoint, headers=headers)
    #             _logger.info("response *********** %s", response)

    #             if response.status_code != 200:
    #                 _logger.info(f"Error fetching transactions: {response.status_code} - {response.text}")

    #             transactions = response.json().get('transactions', [])
    #             _logger.info("transactions ********* %s", transactions)

    #             if not transactions:
    #                 _logger.info("No transactions found for this order.")

    #             transaction_data = False
    #             if len(transactions) == 1:
    #                 txn = transactions[0]
    #                 if not txn.get('parent_id'):
    #                     transaction_data = txn
    #             else:
    #                 for txn in transactions:
    #                     if not txn.get('parent_id') and txn.get('status') == 'success':
    #                         transaction_data = txn
    #                         break

    #             if transaction_data:
    #                 ref = record.ref or ''
    #                 payment_id = transaction_data.get('payment_id')
    #                 payment_id_trimmed = False
    #                 if payment_id:
    #                     payment_id_trimmed = payment_id[:-5] if payment_id else ''
    #                 amount = transaction_data.get('amount')
    #                 status = transaction_data.get('status')
    #                 if ref and payment_id_trimmed:
    #                     ref = f"{ref} - {payment_id_trimmed}"
    #                 elif payment_id_trimmed:
    #                     ref = payment_id_trimmed

    #                 record.write({
    #                     'ref': ref,
    #                     'shopify_payment_id': payment_id_trimmed,
    #                     'amount_shopify': amount,
    #                     'status': status,
    #                 })
    #             else:
    #                 _logger.info("No valid transaction found!")
    #         else:
    #             _logger.info("access token not found.")

    #     return records