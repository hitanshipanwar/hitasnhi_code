from odoo import models, fields, api
from dateutil.relativedelta import relativedelta
from odoo.tools.float_utils import float_compare, float_is_zero, float_round
from odoo.osv import expression
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, format_amount, format_date, formatLang, get_lang, groupby
from odoo.exceptions import UserError, ValidationError
from odoo import api, fields, models, _
from datetime import date

class PurchaseOrderInheritForVendorDashboard(models.Model):
    _inherit = "purchase.order"

    purchase_due_amount  = fields.Float(string='Amount Due for Billing')
    rest_percentage  = fields.Integer(string='Rest Bill Percentage',default=100)
    can_create_bill = fields.Boolean(string='Can Create Bill', default=True)
    create_bill_count = fields.Integer(string='Create bill Count', default=0)
    vendor_location = fields.Many2one('res.partner', string="Vendor Location")


    def action_create_invoice(self):
        print("###############################")
        """Create the invoice associated to the PO.
        """
        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')

        # 1) Prepare invoice vals and clean-up the section lines
        invoice_vals_list = []
        sequence = 10
        for order in self:
            if order.invoice_status != 'to invoice':
                continue

            order = order.with_company(order.company_id)
            pending_section = None
            # Invoice values.
            invoice_vals = order._prepare_invoice()
            # Invoice line values (keep only necessary sections).
            for line in order.order_line:
                if line.display_type == 'line_section':
                    pending_section = line
                    continue
                if not float_is_zero(line.qty_to_invoice, precision_digits=precision):
                    if pending_section:
                        line_vals = pending_section._prepare_account_move_line()
                        line_vals.update({'sequence': sequence})
                        invoice_vals['invoice_line_ids'].append((0, 0, line_vals))
                        sequence += 1
                        pending_section = None
                    line_vals = line._prepare_account_move_line()
                    line_vals.update({'sequence': sequence})
                    invoice_vals['invoice_line_ids'].append((0, 0, line_vals))
                    sequence += 1
            invoice_vals_list.append(invoice_vals)

        if not invoice_vals_list:
            raise UserError(_('There is no invoiceable line. If a product has a control policy based on received quantity, please make sure that a quantity has been received.'))

        # 2) group by (company_id, partner_id, currency_id) for batch creation
        new_invoice_vals_list = []
        for grouping_keys, invoices in groupby(invoice_vals_list, key=lambda x: (x.get('company_id'), x.get('partner_id'), x.get('currency_id'))):
            origins = set()
            payment_refs = set()
            refs = set()
            ref_invoice_vals = None
            for invoice_vals in invoices:
                if not ref_invoice_vals:
                    ref_invoice_vals = invoice_vals
                else:
                    ref_invoice_vals['invoice_line_ids'] += invoice_vals['invoice_line_ids']
                origins.add(invoice_vals['invoice_origin'])
                payment_refs.add(invoice_vals['payment_reference'])
                refs.add(invoice_vals['ref'])
            ref_invoice_vals.update({
                'ref': ', '.join(refs)[:2000],
                'invoice_origin': ', '.join(origins),
                'payment_reference': len(payment_refs) == 1 and payment_refs.pop() or False,
            })
            new_invoice_vals_list.append(ref_invoice_vals)
        invoice_vals_list = new_invoice_vals_list

        # 3) Create invoices.
        moves = self.env['account.move']
        AccountMove = self.env['account.move'].with_context(default_move_type='in_invoice')
        for vals in invoice_vals_list:
            moves |= AccountMove.with_company(vals['company_id']).create(vals)

        # 4) Some moves might actually be refunds: convert them if the total amount is negative
        # We do this after the moves have been created since we need taxes, etc. to know if the total
        # is actually negative or not
        moves.filtered(lambda m: m.currency_id.round(m.amount_total) < 0).action_switch_move_type()
        # moves.filtered(lambda m: m.currency_id.round(m.amount_total) < 0).action_switch_invoice_into_refund_credit_note()

        print("self.name ***********  " , self.name)
        account_moves = self.env['account.move'].sudo().search([('id', '=', moves.id)])  
        print("======account_moves============" , account_moves)
        account_move_to_update = account_moves[0] if account_moves else False
        print("=account_move_to_update==========",account_move_to_update)
        if account_move_to_update:
            account_move_to_update.write({'invoice_purchase_order': self.name,  'invoice_date': date.today()})
            # account_move_to_update.action_post()
            # account_move_to_update.send_to_bill_com()

        return self.action_view_invoice(moves)

    def get_invoice_per(self, term_per):
        if term_per:
            if '%' in term_per:
                # lcl_term_per = int(term_per.replace('%', ''))
                lcl_term_per = (term_per.replace('%', ''))
                for invoice in self.invoice_ids:
                    # lcl_per = int(invoice.amount_total) / int(self.amount_total) * 100
                    # local_term =int(lcl_per)
                    local_term = int((invoice.amount_total) / (self.amount_total) * 100)
                    if int(lcl_term_per) == local_term:
                        return True
        return False

    def get_bill_record(self, term_per):
        if term_per:
            if '%' in term_per:
                # lcl_term_per = int(term_per.replace('%', ''))
                lcl_term_per = (term_per.replace('%', ''))
                for invoice in self.invoice_ids:
                    # lcl_per = int(invoice.amount_total) / int(self.amount_total) * 100
                    # local_term = int(lcl_per)
                    local_term = int((invoice.amount_total) / (self.amount_total) * 100)
                    if int(lcl_term_per) == local_term:
                        return invoice
        return False

    def return_default_due_date(self):
        today = fields.Date.context_today(self)
        if self.payment_term_id and self.payment_term_id.due_date:
            due_date_days = self.payment_term_id.due_date.split('net_')
            return today + relativedelta(days=int(due_date_days[1]))
        else:
            payment_term = self.env['account.payment.term'].search([('default_payment_term','=',True)])
            print("====payment_term================== " , payment_term)
            due_date_days = payment_term.due_date.split('net_')
            print("=====due_date_days===========" , due_date_days)
            return today + relativedelta(days=int(due_date_days[1]))

class AccountMove(models.Model):
    _name = 'account.move'
    _inherit = ['account.move']
    
    vendors_bill_per = fields.Char(string="Bill(%)")
    invoice_purchase_order = fields.Char(string="Purchase Order #", tracking=True)

class PartnerIdForDashboard(models.Model):
    _inherit = 'res.partner'

    is_phone_verified = fields.Boolean(string="Is Phone Number Verified", default=False)
    is_email_verified = fields.Boolean(string="Is Email Id Verified", default=False)

class UsersIdForDashboard(models.Model):
    _inherit = 'res.users'

    def unlink(self):
        for record in self:
            if record.partner_id:
                record.partner_id.is_phone_verified = False
                record.partner_id.is_email_verified = False
        return super(UsersIdForDashboard, self).unlink()

class AccountPaymentTermInh(models.Model):
    _inherit = "account.payment.term"

    cust_vend_type = fields.Selection(
        selection=[
            ("customer", "Customer"),
            ("vendor", "Vendor"),
        ],required=True)
    default_payment_term = fields.Boolean("Default Payment Terms", default=False, copy=False)
    due_date = fields.Selection(
        selection=[
            ("net_15", "NET 15"),
            ("net_30", "NET 30"),
            ("net_45", "NET 45"),
            ("net_75", "NET 75"),
        ])
    bill_com_payment_term_id = fields.Char()
