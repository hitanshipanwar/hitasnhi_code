# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.

from email.policy import strict
from odoo import models, fields, api, _
from datetime import timedelta
from datetime import datetime
from odoo.exceptions import ValidationError
import calendar
import io
import xlwt
import base64
from odoo.exceptions import UserError
import uuid
import logging
_logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    _inherit = 'res.partner'

    start_date = fields.Date('Start Date')
    end_date = fields.Date('End Date')
    date_filter_type = fields.Selection([('this_month','This Month'),('last_month','Last Month'),('this_quarter','This Quarter'),('last_quarter','Last Quarter'),('this_year','This Year'),('last_year','Last Year'),('custom','Custom')],string="Date Filter")
    payment_type = fields.Selection([('fully_paid','Fully Paid'),('partial_paid','Partial Paid Or Not Paid')],string="Payment Type")
    customer_payment_type = fields.Selection([('fully_paid','Fully Paid'),('partial_paid','Partial Paid Or Not Paid')],string="Customer Payment Type")
    sh_filter_customer_statement_ids = fields.One2many(
        'sh.res.partner.filter.statement', 'partner_id', string='Customer Filtered Statements')
    sh_filter_customer_current = fields.Float('current')
    sh_filter_customer_zero_to_thiry = fields.Float('1-30')
    sh_filter_customer_thirty_to_sixty = fields.Float('31-60')
    sh_filter_customer_sixty_to_ninety = fields.Float('61-90')
    sh_filter_customer_ninety_plus = fields.Float('Older Than 90')
    sh_filter_customer_total = fields.Float('Total')
    sh_customer_statement_ids = fields.One2many(
        'sh.customer.statement', 'partner_id', string='Customer Statements')
    sh_customer_current = fields.Float('current')
    sh_customer_zero_to_thiry = fields.Float('1-30')
    sh_customer_thirty_to_sixty = fields.Float('31-60')
    sh_customer_sixty_to_ninety = fields.Float('61-90')
    sh_customer_ninety_plus = fields.Float('Older Than 90')
    sh_customer_total = fields.Float('Total')
    sh_dont_send_customer_statement_auto = fields.Boolean("Don't send statement auto ?")
    sh_dont_send_due_customer_statement_auto = fields.Boolean(
        "Don't send Overdue statement auto ?")
    sh_customer_due_statement_ids = fields.One2many(
        'sh.customer.due.statement', 'partner_id', string='Customer Overdue Statements')
    sh_customer_due_current = fields.Float('current')
    sh_customer_due_zero_to_thiry = fields.Float('1-30')
    sh_customer_due_thirty_to_sixty = fields.Float('31-60')
    sh_customer_due_sixty_to_ninety = fields.Float('61-90')
    sh_customer_due_ninety_plus = fields.Float('Older Than 90')
    sh_customer_due_total = fields.Float('Total')
    sh_customer_compute_boolean = fields.Boolean(
        'Boolean', compute='_compute_customer_statements')
    company_id = fields.Many2one('res.company', string='Company',
                                 default=lambda self: self.env.company)
    sh_cfs_statement_report_url = fields.Char(compute='_compute_cfs_report_url')
    sh_cust_statement_report_url = fields.Char(compute='_compute_cust_report_url')
    sh_cust_due_statement_report_url = fields.Char(compute='_compute_cust_due_report_url')
    report_token = fields.Char("Access Token")
    portal_statement_url_wp = fields.Char(compute='_compute_statement_portal_url_wp')

    sh_customer_statement_config=fields.Many2many('sh.customer.statement.config',string="Customer Statement Config",readonly=True)

    @api.onchange('date_filter_type')
    def onchange_date_filter(self):
        if self.date_filter_type:
            filter_type = self.date_filter_type
            if filter_type == 'this_month':
                self.start_date = datetime.now().date().replace(day=1)
                self.end_date = datetime.now().date()
            elif filter_type == 'last_month':                
                self.start_date = (datetime.now().date() - timedelta(days=datetime.now().date().day)).replace(day=1)
                self.end_date = datetime.now().date().replace(day=1) - timedelta(days=1)
            elif filter_type == 'this_quarter':
                self.start_date = self.get_first_day_of_the_quarter(datetime.now().date())
                self.end_date = self.get_last_day_of_the_quarter(datetime.now().date())
            elif filter_type == 'last_quarter':
                previous_quarter = self.previous_quarter(datetime.now().date())
                self.start_date = self.get_first_day_of_the_quarter(previous_quarter)
                self.end_date = previous_quarter
            elif filter_type == 'this_year':
                self.start_date = datetime.now().date().replace(day=1,month=1)
                self.end_date = datetime.now().date().replace(day=31,month=12)
            elif filter_type == 'last_year':
                self.start_date = datetime.now().date().replace(day=1,month=1,year=datetime.now().date().year-1)
                self.end_date = datetime.now().date().replace(day=31,month=12,year=datetime.now().date().year-1)
            else:
                self.start_date = False
                self.end_date = False

    def get_quarter(self,date):
        return (date.month - 1) / 3 + 1

    def get_first_day_of_the_quarter(self,date):
        quarter = self.get_quarter(date)
        return datetime(date.year, 3 * int(quarter) - 2, 1)

    def get_last_day_of_the_quarter(self,date):
        quarter = self.get_quarter(date)
        month = 3 * int(quarter)
        remaining = int(month / 12)
        return datetime(date.year + remaining, month % 12 + 1, 1) + timedelta(days=-1)

    def previous_quarter(self,ref):
        if ref.month < 4:
            return datetime(ref.year - 1, 12, 31)
        elif ref.month < 7:
            return datetime(ref.year, 3, 31)
        elif ref.month < 10:
            return datetime(ref.year, 6, 30)
        return datetime(ref.year, 9, 30)

    def _compute_statement_portal_url_wp(self):
        for rec in self:
            rec.portal_statement_url_wp = False
            if rec.company_id.sh_statement_url_in_message:
                base_url = self.env['ir.config_parameter'].sudo(
                ).get_param('web.base.url')
                ticket_url = ''
                if rec.customer_rank > 0:
                    ticket_url = base_url+'/my/customer_statements'
                rec.portal_statement_url_wp = ticket_url

    def _get_token(self):
        """ Get the current record access token """
        if self.report_token:
            return self.report_token
        else:
            report_token = str(uuid.uuid4())
            self.write({'report_token': report_token})
            return report_token

    def get_download_report_url(self):
        url = ''
        if self.id:
            self.ensure_one()
            url = '/download/cfs/' + '%s?access_token=%s' % (
                self.id,
                self._get_token()
            )
        return url
    
    def get_cust_statement_download_report_url(self):
        url = ''
        if self.id:
            self.ensure_one()
            url = '/download/cs/' + '%s?access_token=%s' % (
                self.id,
                self._get_token()
            )
        return url
    
    def get_cust_due_statement_download_report_url(self):
        url = ''
        if self.id:
            self.ensure_one()
            url = '/download/cds/' + '%s?access_token=%s' % (
                self.id,
                self._get_token()
            )
        return url
    
    def _compute_cfs_report_url(self):
        for rec in self:
            rec.sh_cfs_statement_report_url = False
            if rec.company_id.sh_statement_pdf_in_message:
                base_url = self.env['ir.config_parameter'].sudo(
                ).get_param('web.base.url')
                if rec.customer_rank > 0:
                    rec.sh_cfs_statement_report_url = base_url+rec.get_download_report_url()
    
    def _compute_cust_report_url(self):
        for rec in self:
            rec.sh_cust_statement_report_url = False
            if rec.company_id.sh_statement_pdf_in_message:
                base_url = self.env['ir.config_parameter'].sudo(
                ).get_param('web.base.url')
                if rec.customer_rank > 0:
                    rec.sh_cust_statement_report_url = base_url+rec.get_cust_statement_download_report_url()
    
    def _compute_cust_due_report_url(self):
        for rec in self:
            rec.sh_cust_due_statement_report_url = False
            if rec.company_id.sh_statement_pdf_in_message:
                base_url = self.env['ir.config_parameter'].sudo(
                ).get_param('web.base.url')
                if rec.customer_rank > 0:
                    rec.sh_cust_due_statement_report_url = base_url+rec.get_cust_due_statement_download_report_url()
    
    def _get_cfs_report_base_filename(self):
        self.ensure_one()
        return '%s %s' % ('Customer Statement Filter By Date', self.name)
    
    def _get_cs_report_base_filename(self):
        self.ensure_one()
        return '%s %s' % ('Customer Statement', self.name)

    def _get_cds_report_base_filename(self):
        self.ensure_one()
        return '%s %s' % ('Customer Due/Overdue Statement', self.name)
    
    def action_send_filter_customer_whatsapp(self):
        self.ensure_one()
        if not self.mobile:
            raise UserError(_("Partner Mobile Number Not Exist !"))
        template = self.env.ref(
            'sh_customer_statement.sh_send_customer_filter_whatsapp_email_template')
        ctx = {
            'default_model': 'res.partner',
            'default_res_id': self.ids[0],
            'default_use_template': bool(template.id),
            'default_template_id': template.id,
            'default_composition_mode': 'comment',
            'force_email': True,
            'default_is_customer_statement': True,
        }
        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(False, 'form')],
            'view_id': False,
            'target': 'new',
            'context': ctx,
        }
    
    def action_send_customer_whatsapp(self):
        self.ensure_one()
        if not self.mobile:
            raise UserError(_("Partner Mobile Number Not Exist !"))
        template = self.env.ref(
            'sh_customer_statement.sh_send_customer_whatsapp_email_template')
        ctx = {
            'default_model': 'res.partner',
            'default_res_id': self.ids[0],
            'default_use_template': bool(template.id),
            'default_template_id': template.id,
            'default_composition_mode': 'comment',
            'force_email': True,
            'default_is_customer_statement': True,
        }
        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(False, 'form')],
            'view_id': False,
            'target': 'new',
            'context': ctx,
        }
    
    def action_send_due_customer_whatsapp(self):
        self.ensure_one()
        if not self.mobile:
            raise UserError(_("Partner Mobile Number Not Exist !"))
        template = self.env.ref(
            'sh_customer_statement.sh_send_customer_due_whatsapp_email_template')
        ctx = {
            'default_model': 'res.partner',
            'default_res_id': self.ids[0],
            'default_use_template': bool(template.id),
            'default_template_id': template.id,
            'default_composition_mode': 'comment',
            'force_email': True,
            'default_is_customer_statement': True,
        }
        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(False, 'form')],
            'view_id': False,
            'target': 'new',
            'context': ctx,
        }

    def update_statement_config_manually_(self):
        view =self.env.ref('sh_customer_statement.sh_update_customers_statement_config_wizard')
        return {
            'type': 'ir.actions.act_window',
            'name': 'Mass Update Config',
            'view_mode': 'form',
            'views': [(view.id, 'form')],
            'res_model': 'sh.customer.config.mass.update',
            'view_id':view.id,
            'target': 'new',
            'context':{'default_sh_selected_partner_ids':self.ids},
        }

    @api.constrains('start_date', 'end_date')
    def _check_dates(self):
        if self.filtered(lambda c: c.end_date and c.start_date > c.end_date):
            raise ValidationError(_('start date must be less than end date.'))

    def _compute_customer_statements(self):
        for rec in self:
            rec.sh_customer_compute_boolean = False
            if rec.customer_rank > 0:
                rec.sh_customer_statement_ids = False
                rec.sh_customer_due_statement_ids = False
                statement_lines = []
                partner_list = [rec]
                if rec.child_ids:
                    for child in rec.child_ids:
                        partner_list.append(child)
                moves_list = []
                payment_list = []
                payment_inbound_list = []
                payment_outbound_list = []
                for partner in partner_list:                   
                    if rec.customer_payment_type:
                        if rec.customer_payment_type == 'fully_paid':
                            moves = self.env['account.move'].sudo().search(
                            [('partner_id', '=', partner.id), ('move_type', 'in', ['out_invoice', 'out_refund']), ('state','not in',['draft','cancel']),('payment_state', '=', 'paid')])
                        elif rec.customer_payment_type == 'partial_paid':
                            moves = self.env['account.move'].sudo().search(
                            [('partner_id', '=', partner.id), ('move_type', 'in', ['out_invoice', 'out_refund']), ('state','not in',['draft','cancel']),('payment_state', 'not in', ['paid'])])
                    else:
                        moves = self.env['account.move'].sudo().search(
                            [('partner_id', '=', partner.id), ('move_type', 'in', ['out_invoice', 'out_refund']), ('state','not in',['draft','cancel'])])
                    
                    if moves:
                        moves_list.extend(moves.ids)
                        # moves_list.append(x.id: x for x in moves)
                        rec.sh_customer_statement_ids.unlink()
                        statement_lines.append((0, 0, {
                            'name':partner.name,
                            'display_type' : "line_section",
                            'sh_customer_amount' : 0.0,
                            'sh_customer_paid_amount' : 0.0,
                            'sh_customer_balance' : 0.0,
                            'currency_id' : moves[0].currency_id.id
                        }))
                        for move in moves:
                            statement_vals = {
                                'sh_account': partner.property_account_receivable_id.name,
                                'name': move.name,
                                'ref': move.ref,
                                'currency_id': move.currency_id.id,
                                'sh_customer_invoice_date': move.invoice_date,
                                'sh_customer_due_date': move.invoice_date_due,
                            }
                            if move.move_type == 'out_invoice':
                                statement_vals.update({
                                    # 'sh_customer_amount': move.amount_total,
                                    # 'sh_customer_paid_amount': move.amount_total - move.amount_residual,
                                    # 'sh_customer_balance': move.amount_total - (move.amount_total - move.amount_residual),
                                    'sh_customer_amount': move.amount_total,
                                    'sh_customer_paid_amount': move.amount_total - move.amount_residual,
                                    'sh_customer_balance': move.amount_total - (move.amount_total - move.amount_residual)
                                    })
                            elif move.move_type == 'out_refund':
                                statement_vals.update({
                                    'sh_customer_amount': -(move.amount_total),
                                    'sh_customer_paid_amount': -(move.amount_total - move.amount_residual),
                                    'sh_customer_balance': (move.amount_total - move.amount_residual) - move.amount_total
                                    })
                            statement_lines.append((0, 0, statement_vals))
                        rec.sh_customer_current = 0.0
                        rec.sh_customer_zero_to_thiry = 0.0
                        rec.sh_customer_thirty_to_sixty = 0.0
                        rec.sh_customer_sixty_to_ninety = 0.0
                        rec.sh_customer_ninety_plus = 0.0
                        today = fields.Date.today()
                        # current_date = 
                        date_before_30 = today - timedelta(days=30)
                        date_before_60 = date_before_30 - timedelta(days=30)
                        date_before_90 = date_before_60 - timedelta(days=30)
                        moves_before_30_days = self.env['account.move'].sudo().search([
                            ('move_type', 'in', ['out_invoice', 'out_refund']),
                            ('partner_id', '=', partner.id),
                            ('invoice_date', '>=', date_before_30),
                            ('invoice_date', '<=', fields.Date.today()),
                            ('state','not in',['draft','cancel'])
                        ])

                        payments_before_30_days = self.env['account.payment'].sudo().search([
                            ('partner_id','=',partner.id),
                            ('state','in',['posted']),
                            ('date', '>=', date_before_30),
                            ('date', '<=', fields.Date.today()),
                            ('partner_type','in',['customer'])])

                        moves_before_60_days = self.env['account.move'].sudo().search([
                            ('move_type', 'in', ['out_invoice', 'out_refund']),
                            ('partner_id', '=', partner.id),
                            ('invoice_date', '>=', date_before_60),
                            ('invoice_date', '<', date_before_30),
                            ('state','not in',['draft','cancel'])
                        ])

                        payments_before_60_days = self.env['account.payment'].sudo().search([
                            ('partner_id','=',partner.id),
                            ('state','in',['posted']),
                            ('date', '>=', date_before_60),
                            ('date', '<', date_before_30),
                            ('partner_type','in',['customer'])])

                        moves_before_90_days = self.env['account.move'].sudo().search([
                            ('move_type', 'in', ['out_invoice', 'out_refund']),
                            ('partner_id', '=', partner.id),
                            ('invoice_date', '>=', date_before_90),
                            ('invoice_date', '<', date_before_60),
                            ('state','not in',['draft','cancel'])
                        ])

                        payments_before_90_days = self.env['account.payment'].sudo().search([
                            ('partner_id','=',partner.id),
                            ('state','in',['posted']),
                            ('date', '>=', date_before_90),
                            ('date', '<', date_before_60),
                            ('partner_type','in',['customer'])])

                        moves_90_plus = self.env['account.move'].sudo().search([
                            ('move_type', 'in', ['out_invoice', 'out_refund']),
                            ('partner_id', '=', partner.id),
                            ('invoice_date', '<', date_before_90),
                            ('state','not in',['draft','cancel'])
                        ])

                        payments_90_plus = self.env['account.payment'].sudo().search([
                            ('partner_id','=',partner.id),
                            ('state','in',['posted']),
                            ('date', '<', date_before_90),
                            ('partner_type','in',['customer'])])

                    

                        # if moves_before_30_days or payments_before_30_days:
                        #     total_paid = 0.0
                        #     total_amount = 0.0
                        #     total_balance = 0.0
                        #     # amt = 0.0
                        #     for move_before_30 in moves_before_30_days:
                        #         # if move_before_30.id == move.id:
                        #         if move_before_30.id in moves_list:
                        #             if move_before_30.move_type == 'out_invoice':
                        #                 total_amount += move_before_30.amount_residual
                        #                 # total_paid += move_before_30.amount_total - move_before_30.amount_residual
                        #             elif move_before_30.move_type == 'out_refund':
                        #                 total_paid += (move_before_30.amount_residual)
                        #                 # total_paid += -(move_before_30.amount_total - move_before_30.amount_residual)
                            
                        #     for payments_before_30_day in payments_before_30_days:
                        #         if payments_before_30_day.payment_type == 'inbound':
                        #             total_paid = total_paid + payments_before_30_day.amount
                        #         else:
                        #             total_amount = total_amount + payments_before_30_day.amount
                        # # amt += total_amount
                        #     total_balance = total_amount - total_paid
                        #     rec.sh_customer_zero_to_thiry = total_balance
                        # if moves_before_60_days or payments_before_60_days:
                        #     total_paid = 0.0
                        #     total_amount = 0.0
                        #     total_balance = 0.0
                        #     for move_before_60 in moves_before_60_days:
                        #         if move_before_60.move_type == 'out_invoice':
                        #             total_amount += move_before_60.amount_residual
                        #             # total_paid += move_before_60.amount_total - move_before_60.amount_residual
                        #         elif move_before_60.move_type == 'out_refund':
                        #             total_paid += (move_before_60.amount_residual)
                        #             # total_paid += -(move_before_60.amount_total - move_before_60.amount_residual)

                        #     for payments_before_60_day in payments_before_60_days:
                        #         if payments_before_60_day.payment_type == 'inbound':
                        #             total_paid = total_paid + payments_before_60_day.amount
                        #         else:
                        #             total_amount = total_amount + payments_before_60_day.amount
                            
                        #     total_balance = total_amount - total_paid
                        #     total_balance = total_amount - total_paid
                        #     rec.sh_customer_thirty_to_sixty = total_balance
                        # if moves_before_90_days or payments_before_90_days:
                        #     total_paid = 0.0
                        #     total_amount = 0.0
                        #     total_balance = 0.0
                        #     for move_before_90 in moves_before_90_days:
                        #         if move_before_90.move_type == 'out_invoice':
                        #             total_amount += move_before_90.amount_residual
                        #             # total_paid += move_before_90.amount_total - move_before_90.amount_residual
                        #         elif move_before_90.move_type == 'out_refund':
                        #             total_paid += (move_before_90.amount_residual)
                        #             # total_paid += -(move_before_90.amount_total - move_before_90.amount_residual)
                            
                        #     for payments_before_90_day in payments_before_90_days:
                        #         if payments_before_90_day.payment_type == 'inbound':
                        #             total_paid = total_paid + payments_before_90_day.amount
                        #         else:
                        #             total_amount = total_amount + payments_before_90_day.amount

                        #     total_balance = total_amount - total_paid
                        #     rec.sh_customer_sixty_to_ninety = total_balance

                        # if moves_90_plus or payments_90_plus:
                        #     total_paid = 0.0
                        #     total_amount = 0.0
                        #     total_balance = 0.0
                        #     for move_90_plus in moves_90_plus:
                        #         if move_90_plus.move_type == 'out_invoice':
                        #             total_amount += move_90_plus.amount_residual
                        #             # total_paid += move_90_plus.amount_total - move_90_plus.amount_residual
                        #         elif move_90_plus.move_type == 'out_refund':
                        #             total_paid += (move_90_plus.amount_residual)
                        #             # total_paid += -(move_90_plus.amount_total - move_90_plus.amount_residual)

                        #     for payment_90_plus in payments_90_plus:
                        #         if payment_90_plus.payment_type == 'inbound':
                        #             total_paid = total_paid + payment_90_plus.amount
                        #         else:
                        #             total_amount = total_amount + payment_90_plus.amount
                                
                        #     total_balance = total_amount - total_paid
                        #     rec.sh_customer_ninety_plus = total_balance
                        # rec.sh_customer_total = rec.sh_customer_zero_to_thiry + rec.sh_customer_thirty_to_sixty + \
                        #     rec.sh_customer_sixty_to_ninety + rec.sh_customer_ninety_plus
                    if rec.customer_payment_type:
                        
                        if rec.customer_payment_type == 'fully_paid':
                            # payment_inbound_list = []
                            advanced_payments_inbound = self.env['account.payment'].sudo().search([
                                    ('partner_id','=',partner.id),
                                    ('state','in',['posted']),
                                    # ('payment_type','in',['inbound']),
                                    ('partner_type','in',['customer']),
                                    ('is_reconciled', '=', True)
                                ])
                            if advanced_payments_inbound:
                                for advance_payment in advanced_payments_inbound:
                                    total_paid_amount = 0.0
                                    if advance_payment.reconciled_invoice_ids:
                                        advance_payment_amount = advance_payment.amount
                                        for invoice in advance_payment.reconciled_invoice_ids:
                                            total_paid_amount+=(invoice.amount_total - invoice.amount_residual)
                                        # if total_paid_amount < advance_payment_amount and advance_payment.amount - total_paid_amount != 0.0:
                                        payment_inbound_list.append(advance_payment.id)
                                        statement_vals = {
                                            'sh_account':
                                            advance_payment.destination_account_id.name,
                                            'name': advance_payment.name,
                                            'currency_id': advance_payment.currency_id.id,
                                            'sh_customer_invoice_date': advance_payment.date,
                                            'sh_customer_amount': 0.0,
                                            'sh_customer_paid_amount': -(advance_payment.amount + sum(advance_payment.move_id.line_ids.mapped('amount_residual'))) if advance_payment.payment_type == "outbound" else (advance_payment.amount - sum(advance_payment.move_id.line_ids.mapped('amount_residual'))),
                                            'sh_customer_balance': -(advance_payment.amount - sum(advance_payment.move_id.line_ids.mapped('amount_residual'))) if advance_payment.payment_type == "inbound" else (advance_payment.amount + sum(advance_payment.move_id.line_ids.mapped('amount_residual'))),
                                        }

                                        statement_lines.append((0, 0, statement_vals))
                                    elif advance_payment.amount != 0.0:
                                        payment_inbound_list.append(advance_payment.id)
                                        statement_vals = {
                                            'sh_account':
                                            advance_payment.destination_account_id.name,
                                            'name': advance_payment.name,
                                            'currency_id': advance_payment.currency_id.id,
                                            'sh_customer_invoice_date': advance_payment.date,
                                            'sh_customer_amount': 0.0,
                                            'sh_customer_paid_amount': -(advance_payment.amount + sum(advance_payment.move_id.line_ids.mapped('amount_residual'))) if advance_payment.payment_type == "outbound" else (advance_payment.amount - sum(advance_payment.move_id.line_ids.mapped('amount_residual'))),
                                            'sh_customer_balance': -(advance_payment.amount - sum(advance_payment.move_id.line_ids.mapped('amount_residual'))) if advance_payment.payment_type == "inbound" else (advance_payment.amount + sum(advance_payment.move_id.line_ids.mapped('amount_residual'))),
                                        }
                                        statement_lines.append((0, 0, statement_vals))

                        elif rec.customer_payment_type == 'partial_paid':
                            # payment_outbound_list = []
                            advanced_payments_outbound = self.env['account.payment'].sudo().search([
                                ('partner_id','=',partner.id),
                                ('state','in',['posted']),
                                # ('payment_type','in',['outbound']),
                                ('partner_type','in',['customer']),
                                 ('is_reconciled', '=', False)
                            ])
                            if advanced_payments_outbound:
                                for advance_payment in advanced_payments_outbound:
                                    total_paid_amount = 0.0
                                    if advance_payment.reconciled_invoice_ids:
                                        advance_payment_amount = advance_payment.amount
                                        for invoice in advance_payment.reconciled_invoice_ids:
                                            total_paid_amount+=(invoice.amount_total - invoice.amount_residual)
                                        # if total_paid_amount < advance_payment_amount and advance_payment.amount - total_paid_amount != 0.0:
                                        payment_inbound_list.append(advance_payment.id)
                                        statement_vals = {
                                            'sh_account':
                                            advance_payment.destination_account_id.name,
                                            'name': advance_payment.name,
                                            'currency_id': advance_payment.currency_id.id,
                                            'sh_customer_invoice_date': advance_payment.date,
                                            'sh_customer_amount': 0.0,
                                            'sh_customer_paid_amount': - (advance_payment.amount + sum(advance_payment.move_id.line_ids.mapped('amount_residual'))) if advance_payment.payment_type == 'outbound' else (advance_payment.amount - sum(advance_payment.move_id.line_ids.mapped('amount_residual'))),
                                            'sh_customer_balance': -(advance_payment.amount - sum(advance_payment.move_id.line_ids.mapped('amount_residual'))) if advance_payment.payment_type == 'inbound' else ( advance_payment.amount + sum(advance_payment.move_id.line_ids.mapped('amount_residual'))),
                                        }

                                        statement_lines.append((0, 0, statement_vals))
                                    elif advance_payment.amount != 0.0:
                                        payment_inbound_list.append(advance_payment.id)
                                        statement_vals = {
                                            'sh_account':
                                            advance_payment.destination_account_id.name,
                                            'name': advance_payment.name,
                                            'currency_id': advance_payment.currency_id.id,
                                            'sh_customer_invoice_date': advance_payment.date,
                                            'sh_customer_amount': 0.0,
                                            'sh_customer_paid_amount': - (advance_payment.amount + sum(advance_payment.move_id.line_ids.mapped('amount_residual'))) if advance_payment.payment_type == 'outbound' else (advance_payment.amount - sum(advance_payment.move_id.line_ids.mapped('amount_residual'))),
                                            'sh_customer_balance': -(advance_payment.amount - sum(advance_payment.move_id.line_ids.mapped('amount_residual'))) if advance_payment.payment_type == 'inbound' else (advance_payment.amount + sum(advance_payment.move_id.line_ids.mapped('amount_residual'))),
                                        }

                                        statement_lines.append((0, 0, statement_vals))
                            
                    else:
                        advanced_payments_inbound = self.env['account.payment'].sudo().search([
                                    ('partner_id','=',partner.id),
                                    ('state','in',['posted']),
                                    # ('payment_type','in',['inbound', 'outbound']),
                                    ('partner_type','in',['customer'])
                                ])

                        # payment_inbound_list = []
                        # advanced_payments_inbound = self.env['account.payment'].sudo().search([
                        #         ('partner_id','=',partner.id),
                        #         ('state','in',['posted']),
                        #         ('payment_type','in',['inbound']),
                        #         ('partner_type','in',['customer'])
                        #     ])
                        if advanced_payments_inbound:
                            for advance_payment in advanced_payments_inbound:
                                total_paid_amount = 0.0
                                if advance_payment.reconciled_invoice_ids:
                                    advance_payment_amount = advance_payment.amount
                                    for invoice in advance_payment.reconciled_invoice_ids:
                                        total_paid_amount+=(invoice.amount_total - invoice.amount_residual)
                                    # if total_paid_amount < advance_payment_amount and advance_payment.amount - total_paid_amount != 0.0:
                                    payment_inbound_list.append(advance_payment.id)
                                    statement_vals = {
                                        'sh_account':
                                        advance_payment.destination_account_id.name,
                                        'name': advance_payment.name,
                                        'currency_id': advance_payment.currency_id.id,
                                        'sh_customer_invoice_date': advance_payment.date,
                                        'sh_customer_amount': 0.0,
                                        # 'sh_customer_paid_amount': advance_payment.amount - sum(advance_payment.move_id.line_ids.mapped('amount_residual')) if advance_payment.payment_type == 'inbound' else -(advance_payment.amount + sum(advance_payment.move_id.line_ids.mapped('amount_residual'))),
                                        'sh_customer_paid_amount': -(advance_payment.amount + sum(advance_payment.move_id.line_ids.mapped('amount_residual'))) if advance_payment.payment_type == 'outbound' else advance_payment.amount - sum(advance_payment.move_id.line_ids.mapped('amount_residual')),
                                        'sh_customer_balance': -(advance_payment.amount - sum(advance_payment.move_id.line_ids.mapped('amount_residual'))) if advance_payment.payment_type == "inbound" else advance_payment.amount + sum(advance_payment.move_id.line_ids.mapped('amount_residual')),
                                    }

                                    statement_lines.append((0, 0, statement_vals))
                                elif advance_payment.amount != 0.0:
                                    payment_inbound_list.append(advance_payment.id)
                                    statement_vals = {
                                        'sh_account':
                                        advance_payment.destination_account_id.name,
                                        'name': advance_payment.name,
                                        'currency_id': advance_payment.currency_id.id,
                                        'sh_customer_invoice_date': advance_payment.date,
                                        'sh_customer_amount': 0.0,
                                        # 'sh_customer_paid_amount': advance_payment.amount - sum(advance_payment.move_id.line_ids.mapped('amount_residual')) if advance_payment.payment_type == 'inbound' else ,
                                        'sh_customer_paid_amount': -(advance_payment.amount + sum(advance_payment.move_id.line_ids.mapped('amount_residual'))) if advance_payment.payment_type == 'outbound' else advance_payment.amount - sum(advance_payment.move_id.line_ids.mapped('amount_residual')),
                                        'sh_customer_balance': -(advance_payment.amount - sum(advance_payment.move_id.line_ids.mapped('amount_residual'))) if advance_payment.payment_type == "inbound" else advance_payment.amount + sum(advance_payment.move_id.line_ids.mapped('amount_residual')),
                                    }
                                    statement_lines.append((0, 0, statement_vals))

                        # payment_outbound_list = []
                        # advanced_payments_outbound = self.env['account.payment'].sudo().search([
                        #     ('partner_id','=',partner.id),
                        #     ('state','in',['posted']),
                        #     ('payment_type','in',['outbound']),
                        #     ('partner_type','in',['customer'])
                        # ])
                        # if advanced_payments_outbound:
                        #     for advance_payment in advanced_payments_outbound:
                        #         total_paid_amount = 0.0
                        #         if advance_payment.reconciled_invoice_ids:
                        #             advance_payment_amount = advance_payment.amount
                        #             for invoice in advance_payment.reconciled_invoice_ids:
                        #                 total_paid_amount+=(invoice.amount_total - invoice.amount_residual)
                        #             if total_paid_amount < advance_payment_amount and advance_payment.amount - total_paid_amount != 0.0:
                        #                 payment_outbound_list.append(advance_payment.id)
                        #                 statement_vals = {
                        #                     'sh_account':
                        #                     advance_payment.destination_account_id.name,
                        #                     'name': advance_payment.name,
                        #                     'currency_id': advance_payment.currency_id.id,
                        #                     'sh_customer_invoice_date': advance_payment.date,
                        #                     'sh_customer_amount': advance_payment.amount - total_paid_amount,
                        #                     'sh_customer_paid_amount': 0.0,
                        #                     'sh_customer_balance': advance_payment.amount - total_paid_amount,
                        #                 }
                        #                 statement_lines.append((0, 0, statement_vals))
                        #         elif advance_payment.amount != 0.0:
                        #             payment_outbound_list.append(advance_payment.id)
                        #             statement_vals = {
                        #                 'sh_account':
                        #                 advance_payment.destination_account_id.name,
                        #                 'name': advance_payment.name,
                        #                 'currency_id': advance_payment.currency_id.id,
                        #                 'sh_customer_invoice_date': advance_payment.date,
                        #                 'sh_customer_amount': advance_payment.amount,
                        #                 'sh_customer_paid_amount': 0.0,
                        #                 'sh_customer_balance': advance_payment.amount,
                        #             }
                        #             statement_lines.append((0, 0, statement_vals))


                payment_list = payment_inbound_list + payment_outbound_list
                # payment_list = payment_inbound_list
                rec.sh_customer_statement_ids = statement_lines

                moves = self.env['account.move'].browse(moves_list)
                payments = self.env['account.payment'].browse(payment_list)

                current_statement = 0.0
                between_1_to_30 = 0.0
                between_31_to_60 = 0.0
                between_61_to_90 = 0.0
                more_than_90 = 0.0

                current_payment = 0.0
                payment_between_1_to_30 = 0.0
                payment_between_31_to_60 = 0.0
                payment_between_61_to_90 = 0.0
                payment_more_than_90 = 0.0

                for move in moves:
                    # payment = self.env['account.payment'].search([('ref' ,'=', move.name)])
                    diff_date = fields.Date.today() - move.invoice_date_due
                    if diff_date.days <= 0:
                        # current_statement += move.amount_residual
                        current_statement += move.amount_residual if move.move_type == 'out_invoice' else (- move.amount_residual)
                    elif diff_date.days >= 1 and diff_date.days <= 30:
                        # between_1_to_30 += move.amount_residual
                        between_1_to_30 += move.amount_residual if move.move_type == 'out_invoice' else (- move.amount_residual)
                    elif diff_date.days >= 31 and diff_date.days <= 60:
                        # between_31_to_60 += move.amount_residual
                        between_31_to_60 += move.amount_residual if move.move_type == 'out_invoice' else (- move.amount_residual)
                    elif diff_date.days >= 61 and diff_date.days <= 90:
                        # between_61_to_90 += move.amount_residual
                        between_61_to_90 += move.amount_residual if move.move_type == 'out_invoice' else (- move.amount_residual)
                    else:
                        # more_than_90 += move.amount_residual
                        more_than_90 += move.amount_residual if move.move_type == 'out_invoice' else (- move.amount_residual)
                for payment in payments:
                    diff_date = fields.Date.today() - payment.date
                    if diff_date.days <= 0:
                        current_payment +=  -(payment.amount - sum(payment.move_id.line_ids.mapped('amount_residual'))) if payment.payment_type == "inbound" else (payment.amount + sum(payment.move_id.line_ids.mapped('amount_residual')))
                        # current_payment +=  -(payment.amount - sum(payment.move_id.line_ids.mapped('amount_residual'))) if payment.payment_type == "inbound" else (payment.amount - sum(payment.move_id.line_ids.mapped('amount_residual')))
                    elif diff_date.days >= 1 and diff_date.days <= 30:
                        payment_between_1_to_30 +=  -(payment.amount - sum(payment.move_id.line_ids.mapped('amount_residual'))) if payment.payment_type == "inbound" else (payment.amount + sum(payment.move_id.line_ids.mapped('amount_residual')))
                        # payment_between_1_to_30 +=  -(payment.amount - sum(payment.move_id.line_ids.mapped('amount_residual'))) if payment.payment_type == "inbound" else (payment.amount - sum(payment.move_id.line_ids.mapped('amount_residual')))
                    elif diff_date.days >= 31 and diff_date.days <= 60:
                        payment_between_31_to_60 += -(payment.amount - sum(payment.move_id.line_ids.mapped('amount_residual'))) if payment.payment_type == "inbound" else (payment.amount + sum(payment.move_id.line_ids.mapped('amount_residual')))
                        # payment_between_31_to_60 += -(payment.amount - sum(payment.move_id.line_ids.mapped('amount_residual'))) if payment.payment_type == "inbound" else (payment.amount - sum(payment.move_id.line_ids.mapped('amount_residual')))
                    elif diff_date.days >= 61 and diff_date.days <= 90:
                        payment_between_61_to_90 += -(payment.amount - sum(payment.move_id.line_ids.mapped('amount_residual'))) if payment.payment_type == "inbound" else (payment.amount + sum(payment.move_id.line_ids.mapped('amount_residual')))
                        # payment_between_61_to_90 += -(payment.amount - sum(payment.move_id.line_ids.mapped('amount_residual'))) if payment.payment_type == "inbound" else (payment.amount - sum(payment.move_id.line_ids.mapped('amount_residual')))
                    else:
                        # payment_more_than_90 += payment.amount if payment.payment_type == 'outbound' else -(payment.amount)
                        payment_more_than_90 += -(payment.amount - sum(payment.move_id.line_ids.mapped('amount_residual'))) if payment.payment_type == "inbound" else (payment.amount + sum(payment.move_id.line_ids.mapped('amount_residual')))
                        # payment_more_than_90 += -(payment.amount - sum(payment.move_id.line_ids.mapped('amount_residual'))) if payment.payment_type == "inbound" else (payment.amount - sum(payment.move_id.line_ids.mapped('amount_residual')))
                rec.sh_customer_current = current_statement + current_payment
                rec.sh_customer_zero_to_thiry = between_1_to_30 + payment_between_1_to_30
                rec.sh_customer_thirty_to_sixty = between_31_to_60  + payment_between_31_to_60
                rec.sh_customer_sixty_to_ninety = between_61_to_90 + payment_between_61_to_90
                rec.sh_customer_ninety_plus = more_than_90 + payment_more_than_90
                rec.sh_customer_total = between_1_to_30 + between_31_to_60 + between_61_to_90 + more_than_90 + payment_between_1_to_30 + payment_between_31_to_60 + payment_between_61_to_90 + payment_more_than_90 + current_statement + current_payment




                # for payment in payment_list:
                #     total_paid_amount = 0.0
                #     if payment.reconciled_invoice_ids:
                #         advance_payment_amount = payment.amount
                #         for invoice in payment.reconciled_invoice_ids:
                #             total_paid_amount+=(invoice.amount_total - invoice.amount_residual)
                #                 if total_paid_amount < advance_payment_amount and payment.amount - total_paid_amount != 0.0:




                overdue_moves = False
                if self.env.company.sh_display_due_statement == 'due':
                    overdue_moves = moves.filtered(
                        lambda x: x.invoice_date_due and x.invoice_date_due >= fields.Date.today() and x.amount_residual > 0.00)
                elif self.env.company.sh_display_due_statement == 'overdue':
                    overdue_moves = moves.filtered(
                        lambda x: x.invoice_date_due and x.invoice_date_due < fields.Date.today() and x.amount_residual > 0.00)
                elif self.env.company.sh_display_due_statement == 'both':
                    overdue_moves = moves.filtered(
                        lambda x: x.amount_residual > 0.00)
                if overdue_moves:
                    rec.sh_customer_due_statement_ids.unlink()
                    overdue_statement_lines = []
                    overdue_statement_lines.append((0, 0, {
                        'name':partner.name,
                        'display_type' : "line_section",
                        'currency_id': overdue_moves[0].currency_id.id,
                        'sh_due_customer_amount' : 0.0,
                        'sh_due_customer_paid_amount' : 0.0,
                        'sh_due_customer_balance' : 0.0,
                    }))
                    for overdue in overdue_moves:
                        # if overdue.partner_id.id == rec.id:
                        # if overdue.partner_id.id == partner.id:
                        overdue_statement_vals = {
                            'sh_account': rec.property_account_receivable_id.name,
                            'currency_id': overdue.currency_id.id,
                            'name': overdue.name,
                            'ref': overdue.ref,
                            'sh_today': fields.Date.today(),
                            'sh_due_customer_invoice_date': overdue.invoice_date,
                            'sh_due_customer_due_date': overdue.invoice_date_due,
                        }
                        if overdue.move_type == 'out_invoice':
                            overdue_statement_vals.update({
                                'sh_due_customer_amount': overdue.amount_total,
                                'sh_due_customer_paid_amount': overdue.amount_total - overdue.amount_residual,
                                'sh_due_customer_balance': overdue.amount_total - (overdue.amount_total - overdue.amount_residual),
                            })
                        elif overdue.move_type == 'out_refund':
                            overdue_statement_vals.update({
                                'sh_due_customer_amount': -(overdue.amount_total),
                                'sh_due_customer_paid_amount': -(overdue.amount_total - overdue.amount_residual),
                                'sh_due_customer_balance': (overdue.amount_total - overdue.amount_residual) - overdue.amount_total, 
                                # 'sh_due_customer_amount': (overdue.amount_total - overdue.amount_residual),
                                # 'sh_due_customer_paid_amount': overdue.amount_total,
                                # 'sh_due_customer_balance': (overdue.amount_total - overdue.amount_residual) - overdue.amount_total,
                            })
                        overdue_statement_lines.append(
                        (0, 0, overdue_statement_vals))
                    rec.sh_customer_due_statement_ids = overdue_statement_lines

                due_current = 0.0
                due_zero_to_thiry = 0.0
                due_thirty_to_sixty = 0.0
                due_sixty_to_ninety = 0.0
                due_ninety_plus = 0.0
                for dues in overdue_moves:
                    diff_date = fields.Date.today() - dues.invoice_date_due
                    if diff_date.days <1:
                        # due_current += dues.amount_residual
                        due_current += dues.amount_residual if dues.move_type == 'out_invoice' else (- dues.amount_residual)
                    elif diff_date.days >= 1 and diff_date.days <= 30:
                        # due_zero_to_thiry += dues.amount_residual
                        due_zero_to_thiry += dues.amount_residual if dues.move_type == 'out_invoice' else (- dues.amount_residual)
                    elif diff_date.days >= 31 and diff_date.days <= 60:
                        # due_thirty_to_sixty += dues.amount_residual
                        due_thirty_to_sixty += dues.amount_residual if dues.move_type == 'out_invoice' else (- dues.amount_residual)
                    elif diff_date.days >= 61 and diff_date.days <= 90:
                        # due_sixty_to_ninety += dues.amount_residual
                        due_sixty_to_ninety += dues.amount_residual if dues.move_type == 'out_invoice' else (- dues.amount_residual)
                    else :
                        # due_ninety_plus += dues.amount_residual
                        due_ninety_plus += dues.amount_residual if dues.move_type == 'out_invoice' else (- dues.amount_residual)
                rec.sh_customer_due_current = due_current 
                rec.sh_customer_due_zero_to_thiry = due_zero_to_thiry 
                rec.sh_customer_due_thirty_to_sixty = due_thirty_to_sixty 
                rec.sh_customer_due_sixty_to_ninety = due_sixty_to_ninety 
                rec.sh_customer_due_ninety_plus = due_ninety_plus
                rec.sh_customer_due_total = due_current + due_zero_to_thiry + due_thirty_to_sixty + due_sixty_to_ninety + due_ninety_plus
                
                

    def send_customer_statement(self):
        for rec in self:
            if rec.customer_rank > 0 and rec.sh_customer_statement_ids:
                template = self.env.ref(
                    'sh_customer_statement.sh_customer_statement_mail_template')
                if template:
                    mail = template.sudo().send_mail(rec.id, force_send=True)
                    mail_id = self.env['mail.mail'].sudo().browse(mail)
                    if mail_id:
                        self.env['sh.customer.mail.history'].sudo().create({
                            'name': 'Customer Account Statement',
                            'sh_statement_type': 'customer_statement',
                            'sh_current_date': fields.Datetime.now(),
                            'sh_partner_id': rec.id,
                            'sh_mail_id': mail_id.id,
                            'sh_mail_status': mail_id.state,
                        })

    def send_customer_overdue_statement(self):
        for rec in self:
            if rec.customer_rank > 0 and rec.sh_customer_due_statement_ids:
                template = self.env.ref(
                    'sh_customer_statement.sh_customer_due_statement_mail_template')
                if template:
                    mail = template.sudo().send_mail(rec.id, force_send=True)
                    mail_id = self.env['mail.mail'].sudo().browse(mail)
                    if mail_id:
                        self.env['sh.customer.mail.history'].sudo().create({
                            'name': 'Customer Account Overdue Statement',
                            'sh_statement_type': 'customer_overdue_statement',
                            'sh_current_date': fields.Datetime.now(),
                            'sh_partner_id': rec.id,
                            'sh_mail_id': mail_id.id,
                            'sh_mail_status': mail_id.state,
                        })

    def action_print_customer_statement(self):
        return self.env.ref('sh_customer_statement.action_report_sh_customer_statement').report_action(self)

    def action_send_customer_statement(self):
        # self.ensure_one()
        # template = self.env.ref(
        #     'sh_customer_statement.sh_customer_statement_mail_template')
        # if template:
        #     mail = template.sudo().send_mail(self.id, force_send=True)
        #     mail_id = self.env['mail.mail'].sudo().browse(mail)
        #     if mail_id:
        #         self.env['sh.customer.mail.history'].sudo().create({
        #             'name': 'Customer Account Statement',
        #             'sh_statement_type': 'customer_statement',
        #             'sh_current_date': fields.Datetime.now(),
        #             'sh_partner_id': self.id,
        #             'sh_mail_id': mail_id.id,
        #             'sh_mail_status': mail_id.state,
        #         })
        self.ensure_one()
        template = self.env.ref(
            'sh_customer_statement.sh_customer_statement_mail_template')
        ctx = {
            'default_model': 'res.partner',
            'default_res_id': self.ids[0],
            'default_use_template': bool(template.id),
            'default_template_id': template.id,
            'default_composition_mode': 'comment',
            'force_email': True,
        }
        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(False, 'form')],
            'view_id': False,
            'target': 'new',
            'context': ctx,
        }

    def action_print_customer_due_statement(self):
        return self.env.ref('sh_customer_statement.action_report_sh_customer_due_statement').report_action(self)

    def action_send_customer_due_statement(self):
        # self.ensure_one()
        # template = self.env.ref(
        #     'sh_customer_statement.sh_customer_due_statement_mail_template')
        # if template:
        #     mail = template.sudo().send_mail(self.id, force_send=True)
        #     mail_id = self.env['mail.mail'].sudo().browse(mail)
        #     if mail_id:
        #         self.env['sh.customer.mail.history'].sudo().create({
        #             'name': 'Customer Account Overdue Statement',
        #             'sh_statement_type': 'customer_overdue_statement',
        #             'sh_current_date': fields.Datetime.now(),
        #             'sh_partner_id': self.id,
        #             'sh_mail_id': mail_id.id,
        #             'sh_mail_status': mail_id.state,
        #         })
        self.ensure_one()
        template = self.env.ref(
            'sh_customer_statement.sh_customer_due_statement_mail_template')
        ctx = {
            'default_model': 'res.partner',
            'default_res_id': self.ids[0],
            'default_use_template': bool(template.id),
            'default_template_id': template.id,
            'default_composition_mode': 'comment',
            'force_email': True,
        }
        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(False, 'form')],
            'view_id': False,
            'target': 'new',
            'context': ctx,
        }
        

    def action_get_customer_statement(self):
        self.ensure_one()
        if self.customer_rank > 0 and self.start_date and self.end_date:
            
            self.sh_filter_customer_statement_ids.unlink()
            statement_lines = []

            #########
            account_id =  self.property_account_receivable_id.id

            payment = ['payment']
            partner = []
            partner_list = [self.id]
            if self.child_ids:
                for child in self.child_ids:
                    partner_list.append(child.id)
            partner.extend(partner_list + payment)   

            move_lines = self.env['account.move.line'].search([
                ('partner_id', 'in', partner_list),
                ('date', '<', self.start_date),
                ('account_id','=',account_id),
                ('parent_state','=','posted'),
            ])
            
            balance = sum(move_lines.mapped('debit')) - sum(move_lines.mapped('credit'))
            statement_lines.append((0,0,{
                'name' : 'Opening Balance',
                'currency_id': move_lines[0].currency_id.id if move_lines else self.currency_id.id,
                'sh_filter_balance':balance,
                'sh_filter_amount': sum(move_lines.mapped('debit')),
                'sh_filter_paid_amount': sum(move_lines.mapped('credit')),
            }))
            #########
            move_list = []
            payment_list = []
            for partner in partner_list:
                if self.payment_type:
                    if self.payment_type == 'fully_paid':
                        moves = self.env['account.move'].sudo().search([('partner_id', '=', partner), ('move_type', 'in', [
                        'out_invoice', 'out_refund']), ('invoice_date', '>=', self.start_date), ('invoice_date', '<=', self.end_date),('state','not in',['draft','cancel']),('payment_state', '=', 'paid')])
                    elif self.payment_type == 'partial_paid':
                        moves = self.env['account.move'].sudo().search([('partner_id', '=', partner), ('move_type', 'in', [
                        'out_invoice', 'out_refund']), ('invoice_date', '>=', self.start_date), ('invoice_date', '<=', self.end_date),('state','not in',['draft','cancel']),('payment_state', 'not in', ['paid'])])
                else:
                    moves = self.env['account.move'].sudo().search([('partner_id', '=', partner), ('move_type', 'in', [
                        'out_invoice', 'out_refund']), ('invoice_date', '>=', self.start_date), ('invoice_date', '<=', self.end_date),('state','not in',['draft','cancel'])])
                if moves:
                    partner_object = self.env['res.partner'].browse(partner)
                    statement_lines.append((0,0,{
                        'name' : partner_object.name,
                        'currency_id': move_lines[0].currency_id.id if move_lines else self.currency_id.id,
                        'sh_filter_balance':0.0,
                        'sh_filter_amount':0.0,
                        'display_type' : 'line_section'
                    }))
                    for move in moves:
                        move_list.append(move.id)
                        statement_vals = {
                            'sh_account': self.property_account_receivable_id.name,
                            'name': move.name,
                            'currency_id': move.currency_id.id,
                            'sh_filter_invoice_date': move.invoice_date,
                            'sh_filter_due_date': move.invoice_date_due,
                            'ref': move.ref,
                        }
                        if move.move_type == 'out_invoice':
                            statement_vals.update({
                                'sh_filter_amount': move.amount_total,
                                'sh_filter_paid_amount': move.amount_total - move.amount_residual,
                                'sh_filter_balance': move.amount_total - (move.amount_total - move.amount_residual)
                            })
                        elif move.move_type == 'out_refund':
                            statement_vals.update({
                                # 'sh_filter_amount': move.amount_total - move.amount_residual,
                                'sh_filter_amount': -(move.amount_total),
                                'sh_filter_paid_amount': -(move.amount_total - move.amount_residual),
                                # 'sh_filter_balance': -(move.amount_total - move.amount_residual),
                                'sh_filter_balance': (move.amount_total - move.amount_residual) - move.amount_total
                            })
                        statement_lines.append((0, 0, statement_vals))

                if self.payment_type:
                    if self.payment_type == 'fully_paid':
                        advanced_payments_inbound = self.env['account.payment'].sudo().search([
                            ('partner_id','=',partner),
                            ('date', '>=', self.start_date),
                            ('date', '<=', self.end_date),
                            ('state','in',['posted']),
                            # ('payment_type','in',['inbound']),
                            ('partner_type','in',['customer']),
                            ('is_reconciled', '=', True)
                        ])
                        if advanced_payments_inbound:
                            for advance_payment in advanced_payments_inbound:
                                payment_list.append(advance_payment.id)
                                total_paid_amount = 0.0
                                if advance_payment.reconciled_invoice_ids:
                                    advance_payment_amount = advance_payment.amount
                                    for invoice in advance_payment.reconciled_invoice_ids: 

                                        if invoice.invoice_date >= self.start_date and invoice.invoice_date <= self.end_date:
                                            
                                            total_paid_amount+= (invoice.amount_total - invoice.amount_residual)

                                    # if total_paid_amount < advance_payment_amount and advance_payment.amount - total_paid_amount != 0.0:
                                    statement_vals = {
                                        'sh_account':
                                        advance_payment.destination_account_id.name,
                                        'name': advance_payment.name,
                                        'currency_id': advance_payment.currency_id.id,
                                        'sh_filter_invoice_date': advance_payment.date,
                                        'sh_filter_amount': 0.0,
                                        'sh_filter_paid_amount':-(advance_payment.amount + sum(advance_payment.move_id.line_ids.mapped('amount_residual'))) if advance_payment.payment_type == "outbound" else (advance_payment.amount - sum(advance_payment.move_id.line_ids.mapped('amount_residual'))),
                                        'sh_filter_balance': -(advance_payment.amount - sum(advance_payment.move_id.line_ids.mapped('amount_residual'))) if advance_payment.payment_type == "inbound" else (advance_payment.amount + sum(advance_payment.move_id.line_ids.mapped('amount_residual'))),
                                    }
                                    statement_lines.append((0, 0, statement_vals))
                                elif advance_payment.amount != 0.0:
                                    statement_vals = {
                                        'sh_account':
                                        advance_payment.destination_account_id.name,
                                        'name': advance_payment.name,
                                        'currency_id': advance_payment.currency_id.id,
                                        'sh_filter_invoice_date': advance_payment.date,
                                        'sh_filter_amount': 0.0,
                                        'sh_filter_paid_amount':  -(advance_payment.amount + sum(advance_payment.move_id.line_ids.mapped('amount_residual'))) if advance_payment.payment_type == "outbound" else (advance_payment.amount - sum(advance_payment.move_id.line_ids.mapped('amount_residual'))),
                                        'sh_filter_balance': -(advance_payment.amount - sum(advance_payment.move_id.line_ids.mapped('amount_residual'))) if advance_payment.payment_type == "inbound" else (advance_payment.amount + sum(advance_payment.move_id.line_ids.mapped('amount_residual'))),
                                    }
                                    statement_lines.append((0, 0, statement_vals))
                    elif self.payment_type == 'partial_paid':
                        advanced_payments_outbound = self.env['account.payment'].sudo().search([
                            ('partner_id','=',partner),
                            ('date', '>=', self.start_date),
                            ('date', '<=', self.end_date),
                            ('state','in',['posted']),
                            # ('payment_type','in',['outbound']),
                            ('partner_type','in',['customer']),
                            ('is_reconciled', '=', False)
                        ])
                        if advanced_payments_outbound:
                            for advance_payment in advanced_payments_outbound:
                                payment_list.append(advance_payment.id)
                                total_paid_amount = 0.0
                                if advance_payment.reconciled_invoice_ids:
                                    advance_payment_amount = advance_payment.amount
                                    for invoice in advance_payment.reconciled_invoice_ids: 

                                        if invoice.invoice_date >= self.start_date and invoice.invoice_date <= self.end_date:
                                            
                                            total_paid_amount+= (invoice.amount_total - invoice.amount_residual)

                                    # if total_paid_amount < advance_payment_amount and advance_payment.amount - total_paid_amount != 0.0:
                                    statement_vals = {
                                        'sh_account':
                                        advance_payment.destination_account_id.name,
                                        'name': advance_payment.name,
                                        'currency_id': advance_payment.currency_id.id,
                                        'sh_filter_invoice_date': advance_payment.date,
                                        'sh_filter_amount': 0.0,
                                        'sh_filter_paid_amount': -(advance_payment.amount + sum(advance_payment.move_id.line_ids.mapped('amount_residual'))) if advance_payment.payment_type == 'outbound' else (advance_payment.amount - sum(advance_payment.move_id.line_ids.mapped('amount_residual'))),
                                        'sh_filter_balance': -(advance_payment.amount - sum(advance_payment.move_id.line_ids.mapped('amount_residual'))) if advance_payment.payment_type == 'inbound' else (advance_payment.amount + sum(advance_payment.move_id.line_ids.mapped('amount_residual'))),
                                    }
                                    statement_lines.append((0, 0, statement_vals))
                                elif advance_payment.amount != 0.0:
                                    statement_vals = {
                                        'sh_account':
                                        advance_payment.destination_account_id.name,
                                        'name': advance_payment.name,
                                        'currency_id': advance_payment.currency_id.id,
                                        'sh_filter_invoice_date': advance_payment.date,
                                        'sh_filter_amount': 0.0,
                                        'sh_filter_paid_amount': -(advance_payment.amount + sum(advance_payment.move_id.line_ids.mapped('amount_residual'))) if advance_payment.payment_type == 'outbound' else (advance_payment.amount - sum(advance_payment.move_id.line_ids.mapped('amount_residual'))),
                                        'sh_filter_balance': -(advance_payment.amount - sum(advance_payment.move_id.line_ids.mapped('amount_residual'))) if advance_payment.payment_type == 'inbound' else (advance_payment.amount + sum(advance_payment.move_id.line_ids.mapped('amount_residual'))),
                                    }
                                    statement_lines.append((0, 0, statement_vals))
                        
                else:
                    advanced_payments_both = self.env['account.payment'].sudo().search([
                            ('partner_id','=',partner),
                            ('date', '>=', self.start_date),
                            ('date', '<=', self.end_date),
                            ('state','in',['posted']),
                            ('payment_type','in',['inbound', 'outbound']),
                            ('partner_type','in',['customer'])
                        ])

                    advanced_payments_inbound = self.env['account.payment'].sudo().search([
                            ('partner_id','=',partner),
                            ('date', '>=', self.start_date),
                            ('date', '<=', self.end_date),
                            ('state','in',['posted']),
                            ('payment_type','in',['inbound']),
                            ('partner_type','in',['customer'])
                        ])
                    if advanced_payments_inbound:
                        for advance_payment in advanced_payments_inbound:
                            payment_list.append(advance_payment.id)
                            total_paid_amount = 0.0
                            if advance_payment.reconciled_invoice_ids:
                                advance_payment_amount = advance_payment.amount
                                for invoice in advance_payment.reconciled_invoice_ids: 

                                    if invoice.invoice_date >= self.start_date and invoice.invoice_date <= self.end_date:
                                        
                                        total_paid_amount+= (invoice.amount_total - invoice.amount_residual)
                                # if total_paid_amount < advance_payment_amount and advance_payment.amount - total_paid_amount != 0.0:
                                statement_vals = {
                                    'sh_account':
                                    advance_payment.destination_account_id.name,
                                    'name': advance_payment.name,
                                    'currency_id': advance_payment.currency_id.id,
                                    'sh_filter_invoice_date': advance_payment.date,
                                    'sh_filter_amount': 0.0,
                                    'sh_filter_paid_amount': advance_payment.amount - sum(advance_payment.move_id.line_ids.mapped('amount_residual')),
                                    'sh_filter_balance': -(advance_payment.amount - sum(advance_payment.move_id.line_ids.mapped('amount_residual'))),
                                }
                                statement_lines.append((0, 0, statement_vals))
                            elif advance_payment.amount != 0.0:
                                statement_vals = {
                                    'sh_account':
                                    advance_payment.destination_account_id.name,
                                    'name': advance_payment.name,
                                    'currency_id': advance_payment.currency_id.id,
                                    'sh_filter_invoice_date': advance_payment.date,
                                    'sh_filter_amount': 0.0,
                                    'sh_filter_paid_amount': advance_payment.amount - sum(advance_payment.move_id.line_ids.mapped('amount_residual')),
                                    'sh_filter_balance': -(advance_payment.amount - sum(advance_payment.move_id.line_ids.mapped('amount_residual'))),
                                }
                                statement_lines.append((0, 0, statement_vals))
                
                    advanced_payments_outbound = self.env['account.payment'].sudo().search([
                                ('partner_id','=',partner),
                                ('date', '>=', self.start_date),
                                ('date', '<=', self.end_date),
                                ('state','in',['posted']),
                                ('payment_type','in',['outbound']),
                                ('partner_type','in',['customer'])
                            ])
                    if advanced_payments_outbound:
                        for advance_payment in advanced_payments_outbound:
                            payment_list.append(advance_payment.id)
                            total_paid_amount = 0.0
                            if advance_payment.reconciled_invoice_ids:
                                advance_payment_amount = advance_payment.amount
                                for invoice in advance_payment.reconciled_invoice_ids: 

                                    if invoice.invoice_date >= self.start_date and invoice.invoice_date <= self.end_date:
                                        
                                        total_paid_amount+= (invoice.amount_total - invoice.amount_residual)

                                # if total_paid_amount < advance_payment_amount and advance_payment.amount - total_paid_amount != 0.0:
                                statement_vals = {
                                    'sh_account':
                                    advance_payment.destination_account_id.name,
                                    'name': advance_payment.name,
                                    'currency_id': advance_payment.currency_id.id,
                                    'sh_filter_invoice_date': advance_payment.date,
                                    'sh_filter_amount': 0.0,
                                    'sh_filter_paid_amount': -(advance_payment.amount + sum(advance_payment.move_id.line_ids.mapped('amount_residual'))),
                                    'sh_filter_balance': advance_payment.amount + sum(advance_payment.move_id.line_ids.mapped('amount_residual')),
                                }
                                statement_lines.append((0, 0, statement_vals))
                            elif advance_payment.amount != 0.0:
                                statement_vals = {
                                    'sh_account':
                                    advance_payment.destination_account_id.name,
                                    'name': advance_payment.name,
                                    'currency_id': advance_payment.currency_id.id,
                                    'sh_filter_invoice_date': advance_payment.date,
                                    'sh_filter_amount': 0.0,
                                    'sh_filter_paid_amount': -(advance_payment.amount + sum(advance_payment.move_id.line_ids.mapped('amount_residual'))),
                                    'sh_filter_balance': advance_payment.amount + sum(advance_payment.move_id.line_ids.mapped('amount_residual')),
                                }
                                statement_lines.append((0, 0, statement_vals))
            moves = self.env['account.move'].browse(move_list)
            payments = self.env['account.payment'].browse(payment_list)

            current_statement = 0.0
            between_1_to_30 = 0.0
            between_31_to_60 = 0.0
            between_61_to_90 = 0.0
            more_than_90 = 0.0

            current_payment = 0.0
            payment_between_1_to_30 = 0.0
            payment_between_31_to_60 = 0.0
            payment_between_61_to_90 = 0.0
            payment_more_than_90 = 0.0

            for move in moves:
                # payment = self.env['account.payment'].search([('ref' ,'=', move.name)])
                diff_date = fields.Date.today() - move.invoice_date_due
                if diff_date.days <= 0:
                    # current_statement += move.amount_residual
                    current_statement += move.amount_residual if move.move_type == 'out_invoice' else (- move.amount_residual)
                elif diff_date.days >= 1 and diff_date.days <= 30:
                    # between_1_to_30 += move.amount_residual
                    between_1_to_30 += move.amount_residual if move.move_type == 'out_invoice' else (- move.amount_residual)
                elif diff_date.days >= 31 and diff_date.days <= 60:
                    # between_31_to_60 += move.amount_residual
                    between_31_to_60 += move.amount_residual if move.move_type == 'out_invoice' else (- move.amount_residual)
                elif diff_date.days >= 61 and diff_date.days <= 90:
                    # between_61_to_90 += move.amount_residual
                    between_61_to_90 += move.amount_residual if move.move_type == 'out_invoice' else (- move.amount_residual)
                else:
                    # more_than_90 += move.amount_residual
                    more_than_90 += move.amount_residual if move.move_type == 'out_invoice' else (- move.amount_residual)
            for payment in payments:
                diff_date = fields.Date.today() - payment.date
                if diff_date.days <= 0:
                    # current_payment +=  -(payment.amount - sum(payment.move_id.line_ids.mapped('amount_residual'))) if payment.payment_type == "inbound" else (payment.amount - sum(payment.move_id.line_ids.mapped('amount_residual')))
                    current_payment +=  -(payment.amount - sum(payment.move_id.line_ids.mapped('amount_residual'))) if payment.payment_type == "inbound" else (payment.amount + sum(payment.move_id.line_ids.mapped('amount_residual')))
                elif diff_date.days >= 1 and diff_date.days <= 30:
                    # payment_between_1_to_30 +=  -(payment.amount - sum(payment.move_id.line_ids.mapped('amount_residual'))) if payment.payment_type == "inbound" else (payment.amount - sum(payment.move_id.line_ids.mapped('amount_residual')))
                    payment_between_1_to_30 +=  -(payment.amount - sum(payment.move_id.line_ids.mapped('amount_residual'))) if payment.payment_type == "inbound" else (payment.amount + sum(payment.move_id.line_ids.mapped('amount_residual')))
                elif diff_date.days >= 31 and diff_date.days <= 60:
                    # payment_between_31_to_60 += -(payment.amount - sum(payment.move_id.line_ids.mapped('amount_residual'))) if payment.payment_type == "inbound" else (payment.amount - sum(payment.move_id.line_ids.mapped('amount_residual')))
                    payment_between_31_to_60 += -(payment.amount - sum(payment.move_id.line_ids.mapped('amount_residual'))) if payment.payment_type == "inbound" else (payment.amount + sum(payment.move_id.line_ids.mapped('amount_residual')))
                elif diff_date.days >= 61 and diff_date.days <= 90:
                    # payment_between_61_to_90 += -(payment.amount - sum(payment.move_id.line_ids.mapped('amount_residual'))) if payment.payment_type == "inbound" else (payment.amount - sum(payment.move_id.line_ids.mapped('amount_residual')))
                    payment_between_61_to_90 += -(payment.amount - sum(payment.move_id.line_ids.mapped('amount_residual'))) if payment.payment_type == "inbound" else (payment.amount + sum(payment.move_id.line_ids.mapped('amount_residual')))
                else:
                    # payment_more_than_90 += payment.amount if payment.payment_type == 'outbound' else -(payment.amount)
                    # payment_more_than_90 += -(payment.amount - sum(payment.move_id.line_ids.mapped('amount_residual'))) if payment.payment_type == "inbound" else (payment.amount - sum(payment.move_id.line_ids.mapped('amount_residual')))
                    payment_more_than_90 += -(payment.amount - sum(payment.move_id.line_ids.mapped('amount_residual'))) if payment.payment_type == "inbound" else (payment.amount + sum(payment.move_id.line_ids.mapped('amount_residual')))
            self.sh_filter_customer_current = current_statement + current_payment
            self.sh_filter_customer_zero_to_thiry = between_1_to_30 + payment_between_1_to_30
            self.sh_filter_customer_thirty_to_sixty = between_31_to_60  + payment_between_31_to_60
            self.sh_filter_customer_sixty_to_ninety = between_61_to_90 + payment_between_61_to_90
            self.sh_filter_customer_ninety_plus = more_than_90 + payment_more_than_90
            self.sh_filter_customer_total = between_1_to_30 + between_31_to_60 + between_61_to_90 + more_than_90 + payment_between_1_to_30 + payment_between_31_to_60 + payment_between_61_to_90 + payment_more_than_90 + current_statement + current_payment

            self.sh_filter_customer_statement_ids = statement_lines

    def action_print_filter_customer_statement(self):
        return self.env.ref('sh_customer_statement.action_report_sh_customer_filtered_statement').report_action(self)

    def action_send_filter_customer_statement(self):
        # self.ensure_one()
        # template = self.env.ref(
        #     'sh_customer_statement.sh_customer_filter_statement_mail_template')
        # if template:
        #     mail = template.sudo().send_mail(self.id, force_send=True)
        #     mail_id = self.env['mail.mail'].sudo().browse(mail)
        #     if mail_id:
        #         self.env['sh.customer.mail.history'].sudo().create({
        #             'name': 'Customer Account Statement by Date',
        #             'sh_statement_type': 'customer_statement_filter',
        #             'sh_current_date': fields.Datetime.now(),
        #             'sh_partner_id': self.id,
        #             'sh_mail_id': mail_id.id,
        #             'sh_mail_status': mail_id.state,
        #         })
        self.ensure_one()
        template = self.env.ref(
            'sh_customer_statement.sh_customer_filter_statement_mail_template')
        ctx = {
            'default_model': 'res.partner',
            'default_res_id': self.ids[0],
            'default_use_template': bool(template.id),
            'default_template_id': template.id,
            'default_composition_mode': 'comment',
            'force_email': True,
        }
        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(False, 'form')],
            'view_id': False,
            'target': 'new',
            'context': ctx,
        }
        

    def action_view_customer_history(self):
        self.ensure_one()
        return{
            'name': 'Mail Log History',
            'type': 'ir.actions.act_window',
            'res_model': 'sh.customer.mail.history',
            'view_mode': 'tree,form',
            'domain': [('sh_partner_id', '=', self.id)],
            'target': 'current',
        }
    
    def action_print_filter_customer_statement_xls(self):
        workbook = xlwt.Workbook()
        heading_format = xlwt.easyxf(
            'font:height 300,bold True;pattern: pattern solid, fore_colour gray25;align: horiz center;align: vert center;borders: left thin, right thin, bottom thin,top thin,top_color gray40,bottom_color gray40,left_color gray40,right_color gray40'
        )
        normal = xlwt.easyxf(
            'font:bold True;align: horiz center;align: vert center')
        cyan_text = xlwt.easyxf(
            'font:bold True,color aqua;align: horiz center;align: vert center')
        green_text = xlwt.easyxf(
            'font:bold True,color green;align: horiz center;align: vert center'
        )
        red_text = xlwt.easyxf(
            'font:bold True,color red;align: horiz center;align: vert center')
        bold_center = xlwt.easyxf(
            'font:height 225,bold True;pattern: pattern solid,fore_colour gray25;align: horiz center;align: vert center;borders: left thin, right thin, bottom thin,top thin,top_color gray40,bottom_color gray40,left_color gray40,right_color gray40'
        )
        date = xlwt.easyxf(
            'font:height 225,bold True;pattern: pattern solid,fore_colour gray25;align: vert center;align: horiz right;borders: left thin, right thin, bottom thin,top thin,top_color gray40,bottom_color gray40,left_color gray40,right_color gray40'
        )
        totals = xlwt.easyxf(
            'font:height 225,bold True;pattern: pattern solid,fore_colour gray25;align: horiz center;align: vert center;borders: left thin, right thin, bottom thin,top thin,top_color gray40,bottom_color gray40,left_color gray40,right_color gray40'
        )
        worksheet = workbook.add_sheet(u'Customer Statement Filter By Date',
                                       cell_overwrite_ok=True)

        worksheet.row(1).height = 380
        worksheet.row(2).height = 320
        worksheet.row(8).height = 400
        worksheet.col(2).width = 4800
        worksheet.col(3).width = 4800
        worksheet.col(4).width = 5500
        worksheet.col(5).width = 5500
        worksheet.col(6).width = 5500
        worksheet.col(0).width = 5500
        worksheet.col(1).width = 6000
        worksheet.write(1, 0, "Date From", date)
        if self.start_date:
            worksheet.write(1, 1, str(self.start_date), normal)
        worksheet.write(1, 2, "Date To", date)
        if self.end_date:
            worksheet.write(1, 3, str(self.end_date), normal)
        worksheet.write_merge(4, 5, 0, 6, self.name, heading_format)
        worksheet.write(8, 0, "Number", bold_center)
        worksheet.write(8, 1, "Customer Reference", bold_center)
        worksheet.write(8, 2, "Date", bold_center)
        worksheet.write(8, 3, "Due Date", bold_center)
        worksheet.write(8, 4, "Total Amount", bold_center)
        worksheet.write(8, 5, "Paid Amount", bold_center)
        worksheet.write(8, 6, "Balance", bold_center)

        total_amount = 0
        total_paid_amount = 0
        total_balance = 0
        k = 9

        if self.sh_filter_customer_statement_ids:
            for i in self.sh_filter_customer_statement_ids:
                for j in i:
                    worksheet.row(k).height = 350
                    if j.sh_filter_amount == j.sh_filter_balance:
                        worksheet.write(k, 0, j.name, cyan_text)
                        worksheet.write(k, 1, i.ref, cyan_text)
                        worksheet.write(k, 2, str(j.sh_filter_invoice_date),
                                        cyan_text)
                        if j.sh_filter_due_date:
                            worksheet.write(k, 3, str(j.sh_filter_due_date),
                                            cyan_text)
                        else:
                            worksheet.write(k, 3, '',
                                            cyan_text)
                        worksheet.write(
                            k, 4,
                            str(i.currency_id.symbol) +
                            str("{:.2f}".format(j.sh_filter_amount)), cyan_text)
                        worksheet.write(
                            k, 5,
                            str(i.currency_id.symbol) +
                            str("{:.2f}".format(j.sh_filter_paid_amount)), cyan_text)
                        worksheet.write(
                            k, 6,
                            str(i.currency_id.symbol) +
                            str("{:.2f}".format(j.sh_filter_balance)), cyan_text)
                    elif j.sh_filter_balance == 0:
                        worksheet.write(k, 0, j.name, green_text)
                        worksheet.write(k, 1, i.ref, green_text)
                        worksheet.write(k, 2, str(j.sh_filter_invoice_date),
                                        green_text)
                        if j.sh_filter_due_date:
                            worksheet.write(k, 3, str(j.sh_filter_due_date),
                                            green_text)
                        else:
                            worksheet.write(k, 3, '',
                                            green_text)
                        worksheet.write(
                            k, 4,
                            str(i.currency_id.symbol) +
                            str("{:.2f}".format(j.sh_filter_amount)), green_text)
                        worksheet.write(
                            k, 5,
                            str(i.currency_id.symbol) +
                            str("{:.2f}".format(j.sh_filter_paid_amount)), green_text)
                        worksheet.write(
                            k, 6,
                            str(i.currency_id.symbol) +
                            str("{:.2f}".format(j.sh_filter_balance)), green_text)
                    else:
                        worksheet.write(k, 0, j.name, red_text)
                        worksheet.write(k, 1, i.ref, red_text)
                        worksheet.write(k, 2, str(j.sh_filter_invoice_date),
                                        red_text)
                        if j.sh_filter_due_date:
                            worksheet.write(k, 3, str(j.sh_filter_due_date),
                                            red_text)
                        else:
                            worksheet.write(k, 3, '',
                                            red_text)
                        worksheet.write(
                            k, 4,
                            str(i.currency_id.symbol) +
                            str("{:.2f}".format(j.sh_filter_amount)), red_text)
                        worksheet.write(
                            k, 5,
                            str(i.currency_id.symbol) +
                            str("{:.2f}".format(j.sh_filter_paid_amount)), red_text)
                        worksheet.write(
                            k, 6,
                            str(i.currency_id.symbol) +
                            str("{:.2f}".format(j.sh_filter_balance)), red_text)
                    k = k + 1
                total_amount = total_amount + j.sh_filter_amount
                total_paid_amount = total_paid_amount + j.sh_filter_paid_amount
                total_balance = total_balance + j.sh_filter_balance
        if self.sh_filter_customer_statement_ids:
            worksheet.write(k, 4,
                            str("{:.2f}".format(total_amount)),
                            totals)
            worksheet.row(k).height = 350
            worksheet.write(k, 5,
                            str("{:.2f}".format(total_paid_amount)),
                            totals)
            worksheet.write(k, 6,
                            str("{:.2f}".format(total_balance)),
                            totals)

        fp = io.BytesIO()
        workbook.save(fp)
        data = base64.encodestring(fp.getvalue())
        IrAttachment = self.env['ir.attachment']
        attachment_vals = {
            "name": "Customer Statement Filter By Date.xls",
            "res_model": "ir.ui.view",
            "type": "binary",
            "datas": data,
            "public": True,
        }
        fp.close()

        attachment = IrAttachment.search(
            [('name', '=', 'Customer Statement Filter By Date'),
             ('type', '=', 'binary'), ('res_model', '=', 'ir.ui.view')],
            limit=1)
        if attachment:
            attachment.write(attachment_vals)
        else:
            attachment = IrAttachment.create(attachment_vals)
        #TODO: make user error here
        if not attachment:
            raise UserError('There is no attachments...')

        url = "/web/content/" + str(attachment.id) + "?download=true"
        return {
            'type': 'ir.actions.act_url',
            'url': url,
            'target': 'current',
        }
    
    def action_print_customer_statement_xls(self):
        workbook = xlwt.Workbook()
        heading_format = xlwt.easyxf(
            'font:height 300,bold True;pattern: pattern solid, fore_colour gray25;align: horiz center;align: vert center;borders: left thin, right thin, bottom thin,top thin,top_color gray40,bottom_color gray40,left_color gray40,right_color gray40'
        )
        normal = xlwt.easyxf(
            'font:bold True;align: horiz center;align: vert center')
        cyan_text = xlwt.easyxf(
            'font:bold True,color aqua;align: horiz center;align: vert center')
        green_text = xlwt.easyxf(
            'font:bold True,color green;align: horiz center;align: vert center'
        )
        red_text = xlwt.easyxf(
            'font:bold True,color red;align: horiz center;align: vert center')
        bold_center = xlwt.easyxf(
            'font:height 225,bold True;pattern: pattern solid,fore_colour gray25;align: horiz center;borders: left thin, right thin, bottom thin,top thin,top_color gray40,bottom_color gray40,left_color gray40,right_color gray40'
        )
        totals = xlwt.easyxf(
            'font:height 225,bold True;pattern: pattern solid,fore_colour gray25;align: horiz center;borders: left thin, right thin, bottom thin,top thin,top_color gray40,bottom_color gray40,left_color gray40,right_color gray40'
        )
        worksheet = workbook.add_sheet(u'Customer Statement',
                                       cell_overwrite_ok=True)

        worksheet.row(5).height = 400
        worksheet.row(12).height = 400
        worksheet.row(13).height = 400
        worksheet.row(10).height = 350
        worksheet.row(11).height = 350
        worksheet.col(2).width = 4800
        worksheet.col(3).width = 4800
        worksheet.col(4).width = 5500
        worksheet.col(5).width = 5500
        worksheet.col(6).width = 5500
        worksheet.col(0).width = 5500
        worksheet.col(1).width = 6000
        worksheet.write_merge(2, 3, 0, 6, self.name, heading_format)
        worksheet.write(5, 0, "Number", bold_center)
        worksheet.write(5, 1, "Customer Reference", bold_center)
        worksheet.write(5, 2, "Date", bold_center)
        worksheet.write(5, 3, "Due Date", bold_center)
        worksheet.write(5, 4, "Total Amount", bold_center)
        worksheet.write(5, 5, "Paid Amount", bold_center)
        worksheet.write(5, 6, "Balance", bold_center)

        total_amount = 0
        total_paid_amount = 0
        total_balance = 0
        k = 6

        if self.sh_customer_statement_ids:
            for i in self.sh_customer_statement_ids:
                for j in i:
                    worksheet.row(k).height = 350
                    if j.sh_customer_amount == j.sh_customer_balance:
                        worksheet.write(k, 0, j.name, cyan_text)
                        worksheet.write(k, 1, i.ref, cyan_text)
                        worksheet.write(k, 2, str(j.sh_customer_invoice_date),
                                        cyan_text)
                        if j.sh_customer_due_date:
                            worksheet.write(k, 3, str(j.sh_customer_due_date),
                                            cyan_text)
                        else:
                            worksheet.write(k, 3, '',
                                            cyan_text)
                        worksheet.write(
                            k, 4,
                            str(i.currency_id.symbol) +
                            str("{:.2f}".format(j.sh_customer_amount)), cyan_text)
                        worksheet.write(
                            k, 5,
                            str(i.currency_id.symbol) +
                            str("{:.2f}".format(j.sh_customer_paid_amount)), cyan_text)
                        worksheet.write(
                            k, 6,
                            str(i.currency_id.symbol) +
                            str("{:.2f}".format(j.sh_customer_balance)), cyan_text)
                    elif j.sh_customer_balance == 0:
                        worksheet.write(k, 0, j.name, green_text)
                        worksheet.write(k, 1, i.ref, green_text)
                        worksheet.write(k, 2, str(j.sh_customer_invoice_date),
                                        green_text)
                        if j.sh_customer_due_date:
                            worksheet.write(k, 3, str(j.sh_customer_due_date),
                                            green_text)
                        else:
                            worksheet.write(k, 3, '',
                                            green_text)
                        worksheet.write(
                            k, 4,
                            str(i.currency_id.symbol) +
                            str("{:.2f}".format(j.sh_customer_amount)), green_text)
                        worksheet.write(
                            k, 5,
                            str(i.currency_id.symbol) +
                            str("{:.2f}".format(j.sh_customer_paid_amount)), green_text)
                        worksheet.write(
                            k, 6,
                            str(i.currency_id.symbol) +
                            str("{:.2f}".format(j.sh_customer_balance)), green_text)
                    else:
                        worksheet.write(k, 0, j.name, red_text)
                        worksheet.write(k, 1, i.ref, red_text)
                        worksheet.write(k, 2, str(j.sh_customer_invoice_date),
                                        red_text)
                        if j.sh_customer_due_date:
                            worksheet.write(k, 3, str(j.sh_customer_due_date),
                                            red_text)
                        else:
                            worksheet.write(k, 3, '',
                                            red_text)
                        worksheet.write(
                            k, 4,
                            str(i.currency_id.symbol) +
                            str("{:.2f}".format(j.sh_customer_amount)), red_text)
                        worksheet.write(
                            k, 5,
                            str(i.currency_id.symbol) +
                            str("{:.2f}".format(j.sh_customer_paid_amount)), red_text)
                        worksheet.write(
                            k, 6,
                            str(i.currency_id.symbol) +
                            str("{:.2f}".format(j.sh_customer_balance)), red_text)
                    k = k + 1
                total_amount = total_amount + float("{:.2f}".format(j.sh_customer_amount))
                total_paid_amount = total_paid_amount + float("{:.2f}".format(j.sh_customer_paid_amount))
                total_balance = total_balance + j.sh_customer_balance

        if self.sh_customer_statement_ids:
            worksheet.write(k, 4,
                            str("{:.2f}".format(total_amount)),
                            totals)
            worksheet.row(k).height = 350
            worksheet.write(k, 5,
                            str("{:.2f}".format(total_paid_amount)),
                            totals)
            worksheet.write(k, 6,
                            str("{:.2f}".format(total_balance)),
                            totals)
        worksheet.write(k + 3, 0, 'Aging Summary', bold_center)
        worksheet.write(k + 3, 1, '0-30(Days)', bold_center)
        worksheet.write(k + 3, 2, '30-60(Days)', bold_center)
        worksheet.write(k + 3, 3, '60-90(Days)', bold_center)
        worksheet.write(k + 3, 4, '90+(Days)', bold_center)
        worksheet.write(k + 3, 5, 'Total', bold_center)
        worksheet.write(k + 4, 0, 'Balance Amount', bold_center)
        if self.sh_customer_statement_ids:
            worksheet.write(
                k + 4, 1,
                str("{:.2f}".format(self.sh_customer_zero_to_thiry)), normal)
            worksheet.write(
                k + 4, 2,
                str("{:.2f}".format(self.sh_customer_thirty_to_sixty)), normal)
            worksheet.write(
                k + 4, 3,
                str("{:.2f}".format(self.sh_customer_sixty_to_ninety)), normal)
            worksheet.write(
                k + 4, 4,
                str("{:.2f}".format(self.sh_customer_ninety_plus)),
                normal)
            worksheet.write(
                k + 4, 5,
                str("{:.2f}".format(self.sh_customer_total)),
                normal)

        fp = io.BytesIO()
        workbook.save(fp)
        data = base64.encodestring(fp.getvalue())
        IrAttachment = self.env['ir.attachment']
        attachment_vals = {
            "name": "Customer Statement.xls",
            "res_model": "ir.ui.view",
            "type": "binary",
            "datas": data,
            "public": True,
        }
        fp.close()

        attachment = IrAttachment.search([('name', '=', 'Customer Statement'),
                                          ('type', '=', 'binary'),
                                          ('res_model', '=', 'ir.ui.view')],
                                         limit=1)
        if attachment:
            attachment.write(attachment_vals)
        else:
            attachment = IrAttachment.create(attachment_vals)
        #TODO: make user error here
        if not attachment:
            raise UserError('There is no attachments...')

        url = "/web/content/" + str(attachment.id) + "?download=true"
        return {
            'type': 'ir.actions.act_url',
            'url': url,
            'target': 'current',
        }
    
    def action_print_customer_due_statement_xls(self):
        workbook = xlwt.Workbook()
        heading_format = xlwt.easyxf(
            'font:height 300,bold True;pattern: pattern solid, fore_colour gray25;align: horiz center;align: vert center;borders: left thin, right thin, bottom thin,top thin,top_color gray40,bottom_color gray40,left_color gray40,right_color gray40'
        )
        red_text = xlwt.easyxf(
            'font:bold True,color red;align: horiz center;align: vert center')
        center_text = xlwt.easyxf(
            'align: horiz center;align: vert center')
        bold_center = xlwt.easyxf(
            'font:height 225,bold True;pattern: pattern solid,fore_colour gray25;align: horiz center;align: vert center;borders: left thin, right thin, bottom thin,top thin,top_color gray40,bottom_color gray40,left_color gray40,right_color gray40'
        )
        date = xlwt.easyxf(
            'font:height 225,bold True;pattern: pattern solid,fore_colour gray25;align: horiz center;borders: left thin, right thin, bottom thin;align: vert center;align: horiz left'
        )
        worksheet = workbook.add_sheet(u'Customer Overdue Statement',
                                       cell_overwrite_ok=True)

        now = datetime.now()
        today_date = now.strftime("%d/%m/%Y %H:%M:%S")

        worksheet.write(1, 0, str(str("Date") + str(": ") + str(today_date)),
                        date)
        worksheet.row(1).height = 350
        worksheet.row(6).height = 350
        worksheet.col(0).width = 8000
        worksheet.col(1).width = 6000
        worksheet.col(2).width = 4800
        worksheet.col(3).width = 4800
        worksheet.col(4).width = 5500
        worksheet.col(5).width = 5500
        worksheet.col(6).width = 5500
        worksheet.row(11).height = 350

        worksheet.write_merge(3, 4, 0, 6, self.name, heading_format)
        worksheet.write(6, 0, "Number", bold_center)
        worksheet.write(6, 1, "Customer Reference", bold_center)
        worksheet.write(6, 2, "Date", bold_center)
        worksheet.write(6, 3, "Due Date", bold_center)
        worksheet.write(6, 4, "Total Amount", bold_center)
        worksheet.write(6, 5, "Paid Amount", bold_center)
        worksheet.write(6, 6, "Balance", bold_center)

        total_amount = 0
        total_paid_amount = 0
        total_balance = 0
        k = 7

        if self.sh_customer_due_statement_ids:
            for i in self.sh_customer_due_statement_ids:
                worksheet.row(k).height = 350
                for j in i:
                    if j.sh_due_customer_due_date and j.sh_today and j.sh_due_customer_due_date < j.sh_today: 
                        worksheet.write(k, 0, j.name, red_text)
                        worksheet.write(k, 1, i.ref, red_text)
                        worksheet.write(k, 2, str(j.sh_due_customer_invoice_date),
                                        red_text)
                        if j.sh_due_customer_due_date:
                            worksheet.write(k, 3, str(j.sh_due_customer_due_date),
                                            red_text)
                        else:
                            worksheet.write(k, 3, '',
                                            red_text)
                        worksheet.write(
                            k, 4,
                            str(i.currency_id.symbol) +
                            str("{:.2f}".format(j.sh_due_customer_amount)), red_text)
                        worksheet.write(
                            k, 5,
                            str(i.currency_id.symbol) +
                            str("{:.2f}".format(j.sh_due_customer_paid_amount)), red_text)
                        worksheet.write(
                            k, 6,
                            str(i.currency_id.symbol) +
                            str("{:.2f}".format(j.sh_due_customer_balance)), red_text)
                    else:
                        worksheet.write(k, 0, j.name, center_text)
                        worksheet.write(k, 1, i.ref, center_text)
                        worksheet.write(k, 2, str(j.sh_due_customer_invoice_date),
                                        center_text)
                        if j.sh_due_customer_due_date:
                            worksheet.write(k, 3, str(j.sh_due_customer_due_date),
                                            center_text)
                        else:
                            worksheet.write(k, 3, '',
                                            center_text)
                        worksheet.write(
                            k, 4,
                            str(i.currency_id.symbol) +
                            str("{:.2f}".format(j.sh_due_customer_amount)), center_text)
                        worksheet.write(
                            k, 5,
                            str(i.currency_id.symbol) +
                            str("{:.2f}".format(j.sh_due_customer_paid_amount)), center_text)
                        worksheet.write(
                            k, 6,
                            str(i.currency_id.symbol) +
                            str("{:.2f}".format(j.sh_due_customer_balance)), center_text)
                    k = k + 1
                total_amount = total_amount + j.sh_due_customer_amount
                total_paid_amount = total_paid_amount + j.sh_due_customer_paid_amount
                total_balance = total_balance + j.sh_due_customer_balance
        if self.sh_customer_due_statement_ids:
            worksheet.write(k, 4,
                            str("{:.2f}".format(total_amount)),
                            bold_center)
            worksheet.row(k).height = 350
            worksheet.write(k, 5,
                            str("{:.2f}".format(total_paid_amount)),
                            bold_center)
            worksheet.write(k, 6,
                            str("{:.2f}".format(total_balance)),
                            bold_center)

        fp = io.BytesIO()
        workbook.save(fp)

        data = base64.encodestring(fp.getvalue())
        IrAttachment = self.env['ir.attachment']
        attachment_vals = {
            "name": "Customer Overdue Statement.xls",
            "res_model": "ir.ui.view",
            "type": "binary",
            "datas": data,
            "public": True,
        }
        fp.close()

        attachment = IrAttachment.search(
            [('name', '=', 'Customer Overdue Statement'),
             ('type', '=', 'binary'), ('res_model', '=', 'ir.ui.view')],
            limit=1)
        if attachment:
            attachment.write(attachment_vals)
        else:
            attachment = IrAttachment.create(attachment_vals)
        #TODO: make user error here
        if not attachment:
            raise UserError('There is no attachments...')

        url = "/web/content/" + str(attachment.id) + "?download=true"
        return {
            'type': 'ir.actions.act_url',
            'url': url,
            'target': 'current',
        }

    @api.model
    def _run_auto_send_customer_statements(self):
        temp=[]
        statement_partners_ids=self.env['sh.customer.statement.config'].sudo().search([])
        if statement_partners_ids:
            for statement in statement_partners_ids:
                for partner in statement.sh_partner_ids:
                    if partner.id not in temp:
                        temp.append(partner.id)
        partner_ids = self.env['res.partner'].sudo().search([('id','not in',temp)])
        for partner in partner_ids:
            try:
                #for customer
                if partner.customer_rank > 0:
                    #for statement
                    if not partner.sh_dont_send_customer_statement_auto:
                        if self.env.company.sh_customer_statement_auto_send and partner.sh_customer_statement_ids:
                            if self.env.company.sh_customer_statement_action == 'daily':
                                if self.env.company.sh_cus_daily_statement_template_id:
                                    mail = self.env.company.sh_cus_daily_statement_template_id.sudo().send_mail(partner.id, force_send=True)
                                    mail_id = self.env['mail.mail'].sudo().browse(mail)
                                    if mail_id and self.env.company.sh_cust_create_log_history:
                                        self.env['sh.customer.mail.history'].sudo().create({
                                            'name': 'Customer Account Statement',
                                            'sh_statement_type': 'customer_statement',
                                            'sh_current_date': fields.Datetime.now(),
                                            'sh_partner_id': partner.id,
                                            'sh_mail_id': mail_id.id,
                                            'sh_mail_status': mail_id.state,
                                        })
                            elif self.env.company.sh_customer_statement_action == 'weekly':
                                today = fields.Date.today().weekday()
                                if int(self.env.company.sh_cust_week_day) == today:
                                    if self.env.company.sh_cust_weekly_statement_template_id:
                                        mail = self.env.company.sh_cust_weekly_statement_template_id.sudo().send_mail(partner.id, force_send=True)
                                        mail_id = self.env['mail.mail'].sudo().browse(
                                            mail)
                                        if mail_id and self.env.company.sh_cust_create_log_history:
                                            self.env['sh.customer.mail.history'].sudo().create({
                                                'name': 'Customer Account Statement',
                                                'sh_statement_type': 'customer_statement',
                                                'sh_current_date': fields.Datetime.now(),
                                                'sh_partner_id': partner.id,
                                                'sh_mail_id': mail_id.id,
                                                'sh_mail_status': mail_id.state,
                                            })
                            elif self.env.company.sh_customer_statement_action == 'monthly':
                                monthly_day = self.env.company.sh_cust_monthly_date
                                today = fields.Date.today()
                                today_date = today.day
                                if self.env.company.sh_cust_monthly_end:
                                    last_day = calendar.monthrange(
                                        today.year, today.month)[1]
                                    if today_date == last_day:
                                        if self.env.company.sh_cust_monthly_template_id:
                                            mail = self.env.company.sh_cust_monthly_template_id.sudo(
                                            ).send_mail(partner.id, force_send=True)
                                            mail_id = self.env['mail.mail'].sudo().browse(
                                                mail)
                                            if mail_id and self.env.company.sh_cust_create_log_history:
                                                self.env['sh.customer.mail.history'].sudo().create({
                                                    'name': 'Customer Account Statement',
                                                    'sh_statement_type': 'customer_statement',
                                                    'sh_current_date': fields.Datetime.now(),
                                                    'sh_partner_id': partner.id,
                                                    'sh_mail_id': mail_id.id,
                                                    'sh_mail_status': mail_id.state,
                                                })
                                else:
                                    if today_date == monthly_day:
                                        if self.env.company.sh_cust_monthly_template_id:
                                            mail = self.env.company.sh_cust_monthly_template_id.sudo(
                                            ).send_mail(partner.id, force_send=True)
                                            mail_id = self.env['mail.mail'].sudo().browse(
                                                mail)
                                            if mail_id and self.env.company.sh_cust_create_log_history:
                                                self.env['sh.customer.mail.history'].sudo().create({
                                                    'name': 'Customer Account Statement',
                                                    'sh_statement_type': 'customer_statement',
                                                    'sh_current_date': fields.Datetime.now(),
                                                    'sh_partner_id': partner.id,
                                                    'sh_mail_id': mail_id.id,
                                                    'sh_mail_status': mail_id.state,
                                                })
                            elif self.env.company.sh_customer_statement_action == 'yearly':
                                today = fields.Date.today()
                                today_date = today.day
                                today_month = today.strftime("%B").lower()
                                if self.env.company.sh_cust_yearly_date == today_date and self.env.company.sh_cust_yearly_month == today_month:
                                    if self.env.company.sh_cust_yearly_template_id:
                                        mail = self.env.company.sh_cust_yearly_template_id.sudo(
                                        ).send_mail(partner.id, force_send=True)
                                        mail_id = self.env['mail.mail'].sudo().browse(
                                            mail)
                                        if mail_id and self.env.company.sh_cust_create_log_history:
                                            self.env['sh.customer.mail.history'].sudo().create({
                                                'name': 'Customer Account Statement',
                                                'sh_statement_type': 'customer_statement',
                                                'sh_current_date': fields.Datetime.now(),
                                                'sh_partner_id': partner.id,
                                                'sh_mail_id': mail_id.id,
                                                'sh_mail_status': mail_id.state,
                                            })
                    #for overdue statement
                    if not partner.sh_dont_send_due_customer_statement_auto:
                        if self.env.company.sh_customer_due_statement_auto_send and partner.sh_customer_due_statement_ids:
                            if self.env.company.sh_customer_due_statement_action == 'daily':
                                if self.env.company.sh_cus_due_daily_statement_template_id:
                                    mail = self.env.company.sh_cus_due_daily_statement_template_id.sudo(
                                    ).send_mail(partner.id, force_send=True)
                                    mail_id = self.env['mail.mail'].sudo().browse(
                                        mail)
                                    if mail_id and self.env.company.sh_cust_due_create_log_history:
                                        self.env['sh.customer.mail.history'].sudo().create({
                                            'name': 'Customer Account Overdue Statement',
                                            'sh_statement_type': 'customer_overdue_statement',
                                            'sh_current_date': fields.Datetime.now(),
                                            'sh_partner_id': partner.id,
                                            'sh_mail_id': mail_id.id,
                                            'sh_mail_status': mail_id.state,
                                        })
                            elif self.env.company.sh_customer_due_statement_action == 'weekly':
                                today = fields.Date.today().weekday()
                                if int(self.env.company.sh_cust_due_week_day) == today:
                                    if self.env.company.sh_cust_due_weekly_statement_template_id:
                                        mail = self.env.company.sh_cust_due_weekly_statement_template_id.sudo(
                                        ).send_mail(partner.id, force_send=True)
                                        mail_id = self.env['mail.mail'].sudo().browse(
                                            mail)
                                        if mail_id and self.env.company.sh_cust_due_create_log_history:
                                            self.env['sh.customer.mail.history'].sudo().create({
                                                'name': 'Customer Account Overdue Statement',
                                                'sh_statement_type': 'customer_overdue_statement',
                                                'sh_current_date': fields.Datetime.now(),
                                                'sh_partner_id': partner.id,
                                                'sh_mail_id': mail_id.id,
                                                'sh_mail_status': mail_id.state,
                                            })
                            elif self.env.company.sh_customer_due_statement_action == 'monthly':
                                monthly_day = self.env.company.sh_cust_due_monthly_date
                                today = fields.Date.today()
                                today_date = today.day
                                if self.env.company.sh_cust_due_monthly_end:
                                    last_day = calendar.monthrange(
                                        today.year, today.month)[1]
                                    if today_date == last_day:
                                        if self.env.company.sh_cust_due_monthly_template_id:
                                            mail = self.env.company.sh_cust_due_monthly_template_id.sudo(
                                            ).send_mail(partner.id, force_send=True)
                                            mail_id = self.env['mail.mail'].sudo().browse(
                                                mail)
                                            if mail_id and self.env.company.sh_cust_due_create_log_history:
                                                self.env['sh.customer.mail.history'].sudo().create({
                                                    'name': 'Customer Account Overdue Statement',
                                                    'sh_statement_type': 'customer_overdue_statement',
                                                    'sh_current_date': fields.Datetime.now(),
                                                    'sh_partner_id': partner.id,
                                                    'sh_mail_id': mail_id.id,
                                                    'sh_mail_status': mail_id.state,
                                                })
                                else:
                                    if today_date == monthly_day:
                                        if self.env.company.sh_cust_due_monthly_template_id:
                                            mail = self.env.company.sh_cust_due_monthly_template_id.sudo(
                                            ).send_mail(partner.id, force_send=True)
                                            mail_id = self.env['mail.mail'].sudo().browse(
                                                mail)
                                            if mail_id and self.env.company.sh_cust_due_create_log_history:
                                                self.env['sh.customer.mail.history'].sudo().create({
                                                    'name': 'Customer Account Overdue Statement',
                                                    'sh_statement_type': 'customer_overdue_statement',
                                                    'sh_current_date': fields.Datetime.now(),
                                                    'sh_partner_id': partner.id,
                                                    'sh_mail_id': mail_id.id,
                                                    'sh_mail_status': mail_id.state,
                                                })
     
                            elif self.env.company.sh_customer_due_statement_action == 'yearly':
                                today = fields.Date.today()
                                today_date = today.day
                                today_month = today.strftime("%B").lower()
                                if self.env.company.sh_cust_due_yearly_date == today_date and self.env.company.sh_cust_due_yearly_month == today_month:
                                    if self.env.company.sh_cust_due_yearly_template_id:
                                        mail = self.env.company.sh_cust_due_yearly_template_id.sudo(
                                        ).send_mail(partner.id, force_send=True)
                                        mail_id = self.env['mail.mail'].sudo().browse(
                                            mail)
                                        if mail_id and self.env.company.sh_cust_due_create_log_history:
                                            self.env['sh.customer.mail.history'].sudo().create({
                                                'name': 'Customer Account Overdue Statement',
                                                'sh_statement_type': 'customer_overdue_statement',
                                                'sh_current_date': fields.Datetime.now(),
                                                'sh_partner_id': partner.id,
                                                'sh_mail_id': mail_id.id,
                                                'sh_mail_status': mail_id.state,
                                            })
            except Exception as e:
                _logger.error("%s", e)

class FilterCustomerStateMent(models.Model):
    _name = 'sh.res.partner.filter.statement'
    _description = 'Filter Customer Statement'

    partner_id = fields.Many2one('res.partner', 'Partner')
    name = fields.Char('Invoice Number')
    currency_id = fields.Many2one('res.currency', 'Currency')
    sh_account = fields.Char('Account')
    sh_filter_invoice_date = fields.Date('Invoice Date')
    sh_filter_due_date = fields.Date('Invoice Due Date')
    sh_filter_amount = fields.Monetary('Total Amount')
    sh_filter_paid_amount = fields.Monetary('Paid Amount')
    sh_filter_balance = fields.Monetary('Balance')
    ref = fields.Char("Customer Reference")
    display_type = fields.Selection([
        ('line_section', "Section")], default=False)

class CustomerStateMent(models.Model):
    _name = 'sh.customer.statement'
    _description = 'Customer Statement'

    partner_id = fields.Many2one('res.partner', 'Partner')
    currency_id = fields.Many2one('res.currency', 'Currency')
    name = fields.Char('Invoice Number')
    sh_account = fields.Char('Account')
    sh_customer_invoice_date = fields.Date('Invoice Date')
    sh_customer_due_date = fields.Date('Invoice Due Date')
    sh_customer_amount = fields.Monetary('Total Amount')
    sh_customer_paid_amount = fields.Monetary('Paid Amount')
    sh_customer_balance = fields.Monetary('Balance')
    # ref = fields.Char("Customer Reference",related='partner_id.ref')
    ref = fields.Char("Customer Reference")
    display_type = fields.Selection([
        ('line_section', "Section")], default=False)

class CustomerDueStateMent(models.Model):
    _name = 'sh.customer.due.statement'
    _description = 'Customer Due Statement'

    partner_id = fields.Many2one('res.partner', 'Partner')
    name = fields.Char('Invoice Number')
    currency_id = fields.Many2one('res.currency', 'Currency')
    sh_account = fields.Char('Account')
    sh_today = fields.Date('Today')
    sh_due_customer_invoice_date = fields.Date('Invoice Date')
    sh_due_customer_due_date = fields.Date('Invoice Due Date')
    sh_due_customer_amount = fields.Monetary('Total Amount')
    sh_due_customer_paid_amount = fields.Monetary('Paid Amount')
    sh_due_customer_balance = fields.Monetary('Balance')
    # ref = fields.Char("Customer Reference",related='partner_id.ref')
    ref = fields.Char("Customer Reference")
    display_type = fields.Selection([
        ('line_section', "Section")], default=False)
