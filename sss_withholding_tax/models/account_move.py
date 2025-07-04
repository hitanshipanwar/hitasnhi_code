# Copyright 2020 Ecosoft Co., Ltd (https://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)
from odoo import api, fields, models,_
from contextlib import ExitStack, contextmanager
from odoo.tools import frozendict, formatLang, format_date, float_is_zero, float_compare


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    wt_tax_id = fields.Many2one(
        comodel_name="account.withholding.tax",
        string="WT",
        compute="_compute_wt_tax_id",
        store=True,
        readonly=False,
    )

    def create_wt_certificate(self):
        cert = self.env['withholding.tax.cert'].search([('wt_line.ref_move_line_id', '=' , self.id)])
        view = int(cert.id)
        view_id = cert.id if cert else False
        if cert:
            for rec in self:
                return {
                    "name": _("Withholding Tax Certs."),
                    "view_mode": "form",
                    "res_model": "withholding.tax.cert",
                    "res_id" : cert.id,
                    "view_id": self.env.ref('sss_withholding_tax.view_withholding_tax_cert_form').id,
                    "type": "ir.actions.act_window",
                    "domain": [("id", "=", cert.id)],
                }
        else:

            return {
                'name': _('WT Certificate Wizard'),
                'type': 'ir.actions.act_window',
                'res_model': 'create.withholding.tax.cert',
                'view_id': self.env.ref('sss_withholding_tax.create_withholding_tax_cert').id,
                'view_mode': 'form',
                'target': 'new'
                   }

            return

    @api.depends("product_id", "account_id")
    def _compute_wt_tax_id(self):
        for rec in self:
            # From invoice, default from product
            if rec.move_id.move_type in ("out_invoice", "out_refund", "in_receipt"):
                rec.wt_tax_id = rec.product_id.wt_tax_id
            elif rec.move_id.move_type in ("in_invoice", "in_refund", "out_receipt"):
                rec.wt_tax_id = rec.product_id.supplier_wt_tax_id
            elif (
                rec.payment_id and rec.payment_id.wt_tax_id.account_id == rec.account_id
            ):
                rec.wt_tax_id = rec.payment_id.wt_tax_id
            else:
                rec.wt_tax_id = False

    def _get_wt_base_amount(self, currency, currency_date):
        self.ensure_one()
        wt_base_amount = 0
        if not currency or self.currency_id == currency:
            # Same currency
            wt_base_amount = self.amount_currency
        elif currency == self.company_currency_id:
            # Payment expressed on the company's currency.
            wt_base_amount = self.balance
        else:
            # Foreign currency on payment different than the one set on the journal entries.
            wt_base_amount = self.company_currency_id._convert(
                self.balance, currency, self.company_id, currency_date
            )
        return wt_base_amount

    def _get_wt_amount(self, currency, currency_date):
        """Calculate withholding tax and base amount based on currency"""
        amount_base = 0
        amount_wt = 0
        for line in self:
            base_amount = line._get_wt_base_amount(currency, currency_date)
            amount_wt += line.wt_tax_id.amount / 100 * base_amount
            amount_base += base_amount
        return (amount_base, amount_wt)

    # @api.depends('tax_ids', 'wt_tax_id', 'currency_id', 'partner_id', 'analytic_distribution', 'balance', 'partner_id', 'move_id.partner_id', 'price_unit')
    # def _compute_all_tax(self):
    #     for line in self:
    #         # print("hitanshi wt tax id >>>>>>>>>>>>>>>>>>>>>>>>>", line.wt_tax_id)
    #         # print("hitanshi tax id >>>>>>>>>>>>>>>>>>>>>>>>>", line.tax_ids)
    #         sign = line.move_id.direction_sign
    #         # print("sign >>>>>>>>>>>>>>>>>>>>>>>>>", sign)
    #         if line.display_type == 'product' and line.move_id.is_invoice(True):
    #             amount_currency = sign * line.price_unit * (1 - line.discount / 100)
    #             amount = sign * line.price_unit / line.currency_rate * (1 - line.discount / 100)
    #             handle_price_include = True
    #             quantity = line.quantity
    #         else:
    #             amount_currency = line.amount_currency
    #             amount = line.balance
    #             handle_price_include = False
    #             quantity = 1
    #         compute_all_currency = line.tax_ids.compute_all(
    #             amount_currency,
    #             currency=line.currency_id,
    #             quantity=quantity,
    #             product=line.product_id,
    #             partner=line.move_id.partner_id or line.partner_id,
    #             is_refund=line.is_refund,
    #             handle_price_include=handle_price_include,
    #             include_caba_tags=line.move_id.always_tax_exigible,
    #             fixed_multiplicator=sign,
    #         )
    #         print('compute_all_currency >>>>>>>>>>>>>>>>>>>>>', compute_all_currency)
    #         print('compute_all_currency >>>>>>>>>>>>>>>>>>>>>', line.tax_ids.compute_all())
    #         rate = line.amount_currency / line.balance if line.balance else 1
    #         line.compute_all_tax_dirty = True
    #         # print('if not wt tax id >>>>>>>>>>>>>>>>>>>', line.wt_tax_id)
    #         # print('if not wt tax id >>>>>>>>>>>>>>>>>>>', line.tax_ids)
    #         if line.tax_ids:
    #             line.compute_all_tax = {
    #                 frozendict({
    #                     'tax_repartition_line_id': tax['tax_repartition_line_id'],
    #                     'group_tax_id': tax['group'] and tax['group'].id or False,
    #                     'account_id': tax['account_id'] or line.account_id.id,
    #                     'currency_id': line.currency_id.id,
    #                     'analytic_distribution': (tax['analytic'] or not tax['use_in_tax_closing']) and line.analytic_distribution,
    #                     'tax_ids': [(6, 0, tax['tax_ids'])],
    #                     'tax_tag_ids': [(6, 0, tax['tag_ids'])],
    #                     'partner_id': line.move_id.partner_id.id or line.partner_id.id,
    #                     'move_id': line.move_id.id,
    #                 }): {
    #                     'name': tax['name'],
    #                     'balance': tax['amount'] / rate,
    #                     'amount_currency': tax['amount'],
    #                     'tax_base_amount': tax['base'] / rate * (-1 if line.tax_tag_invert else 1),
    #                 }
    #                 for tax in compute_all_currency['taxes']
    #                 if tax['amount']
    #             }
    #         print('iffffffff >>>>>>>>>>   >>>>>>', line.compute_all_tax)
    #         # if line.wt_tax_id:
    #         #     name = line.wt_tax_id.name
    #         #     tax_amt = abs(line.price_unit * line.wt_tax_id.amount / 100)
    #         #     base_amt = line.price_unit
    #         #     line.compute_all_tax = {
    #         #         frozendict({
    #         #             'tax_repartition_line_id': tax['tax_repartition_line_id'],
    #         #             'group_tax_id': tax['group'] and tax['group'].id or False,
    #         #             'account_id': tax['account_id'] or line.account_id.id,
    #         #             'currency_id': line.currency_id.id,
    #         #             'analytic_distribution': (tax['analytic'] or not tax['use_in_tax_closing']) and line.analytic_distribution,
    #         #             'tax_ids': [(6, 0, tax['tax_ids'])],
    #         #             'tax_tag_ids': [(6, 0, tax['tag_ids'])],
    #         #             'partner_id': line.move_id.partner_id.id or line.partner_id.id,
    #         #             'move_id': line.move_id.id,
    #         #         }): {
    #         #             'name': name,
    #         #             'balance': abs(tax_amt),
    #         #             'amount_currency': tax_amt,
    #         #             'tax_base_amount': base_amt,
    #         #         }
    #         #         for tax in compute_all_currency['taxes']
    #         #         if tax['amount']
    #         #     }
    #         # print('iffffffff >>>>>>>>>>   >>>>>> wt tax ids ', line.compute_all_tax)
    #         # print('line.compute_all_tax^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^', line.wt_tax_id)
    #         # # print('line.compute_all_tax^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^', line.tax_ids)
    #         # if line.wt_tax_id:
    #         #     print('SSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSS')
    #         #     if not line.tax_repartition_line_id:
    #         #         line.compute_all_tax[frozendict({'id': line.id})] = {
    #         #             'tax_tag_ids': [(6, 0, compute_all_currency['base_tags'])],
    #         #         }
    #         # if line.tax_ids:
    #         print('HHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHH')
    #         if not line.tax_repartition_line_id:
    #             line.compute_all_tax[frozendict({'id': line.id + 1})] = {
    #                 'tax_tag_ids': [(6, 0, compute_all_currency['base_tags'])],
    #             }

    # @api.depends('wt_tax_id','tax_ids', 'currency_id', 'partner_id', 'analytic_distribution', 'balance', 'partner_id', 'move_id.partner_id', 'price_unit')
    # def _compute_all_tax(self):
    #     res = super(AccountMoveLine, self)._compute_all_tax()
    #     for line in self:
    #         #Hitanshi's Code For Tax Line List
    #         wt_tax = line.wt_tax_id.ids
    #         tax = line.tax_ids.ids
    #         line_lst = wt_tax + tax
    #         # print('tax line >>>>>>>>>>>>>>>>>>>', wt_tax)
    #         # print('tax line >>>>>>>>>>>>>>>>>>>', tax)
    #         # print('tax line >>>>>>>>>>>>>>>>>ss>>', line_lst)






    #         # if line.tax_ids:
    #         sign = line.move_id.direction_sign
    #         if line.display_type == 'product' and line.move_id.is_invoice(True):
    #             amount_currency = sign * line.price_unit * (1 - line.discount / 100)
    #             amount = sign * line.price_unit / line.currency_rate * (1 - line.discount / 100)
    #             handle_price_include = True
    #             quantity = line.quantity
    #         else:
    #             amount_currency = line.amount_currency
    #             amount = line.balance
    #             handle_price_include = False
    #             quantity = 1
    #         compute_all_currency = line.tax_ids.compute_all(
    #             amount_currency,
    #             currency=line.currency_id,
    #             quantity=quantity,
    #             product=line.product_id,
    #             partner=line.move_id.partner_id or line.partner_id,
    #             is_refund=line.is_refund,
    #             handle_price_include=handle_price_include,
    #             include_caba_tags=line.move_id.always_tax_exigible,
    #             fixed_multiplicator=sign,
    #         )
    #         print('compute_all_currency>>>>>>>>>>>>>>>>>', compute_all_currency)
    #         rate = line.amount_currency / line.balance if line.balance else 1
    #         line.compute_all_tax_dirty = True
    #         line.compute_all_tax = {}
    #         all_dict = []
    #         tax_dict = {}
    #         if line.tax_ids:
    #             tax_dict = [{
    #                 frozendict({
    #                     'tax_repartition_line_id': tax['tax_repartition_line_id'],
    #                     'group_tax_id': tax['group'] and tax['group'].id or False,
    #                     'account_id': tax['account_id'] or line.account_id.id,
    #                     'currency_id': line.currency_id.id,
    #                     'analytic_distribution': (tax['analytic'] or not tax['use_in_tax_closing']) and line.analytic_distribution,
    #                     'tax_ids': [(6, 0, tax['tax_ids'])],
    #                     'tax_tag_ids': [(6, 0, tax['tag_ids'])],
    #                     'partner_id': line.move_id.partner_id.id or line.partner_id.id,
    #                     'move_id': line.move_id.id,
    #                 }): {
    #                     'name': tax['name'],
    #                     'balance': tax['amount'] / rate,
    #                     'amount_currency': tax['amount'],
    #                     'tax_base_amount': tax['base'] / rate * (-1 if line.tax_tag_invert else 1),
    #                 }
    #                 for tax in compute_all_currency['taxes']
    #                 if tax['amount']
    #             }]
    #         print('>>>>>>>>>>>>>>>>>tax_dict', tax_dict)
    #         wt_tax_dict = {}
    #         if line.wt_tax_id:
    #             name = line.wt_tax_id.name
    #             tax_amt = abs(line.price_unit * line.wt_tax_id.amount / 100)
    #             # print("tax amt >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>", tax_amt)
    #             base_amt = line.price_unit
    #             line.compute_all_tax = {
    #                 frozendict({
    #                     'tax_repartition_line_id': tax['tax_repartition_line_id'],
    #                     'group_tax_id': tax['group'] and tax['group'].id or False,
    #                     'account_id': tax['account_id'] or line.wt_tax_id.account_id.id,
    #                     'currency_id': line.currency_id.id,
    #                     'analytic_distribution': (tax['analytic'] or not tax['use_in_tax_closing']) and line.analytic_distribution,
    #                     'tax_ids': [(6, 0, tax['tax_ids'])],
    #                     'tax_tag_ids': [(6, 0, tax['tag_ids'])],
    #                     'partner_id': line.move_id.partner_id.id or line.partner_id.id,
    #                     'move_id': line.move_id.id,
    #                 }): {
    #                     'name': name,
    #                     'balance': abs(tax_amt),
    #                     'amount_currency': tax_amt,
    #                     'tax_base_amount': base_amt,
    #                 }
    #                 for tax in compute_all_currency['taxes']
    #                 if tax['amount']
    #             }
    #             # print('>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>', compute_all_currency['taxes'])
    #             print('>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>wt_tax_dict>', wt_tax_dict)
    #             # wt_tax_dict = {
    #             #     'name': name,
    #             #     'balance': tax_amt,
    #             #     'amount_currency': tax_amt,
    #             #     'tax_base_amount': base_amt,
    #             # }
    #         # set(tuple(i) for i in l)
    #         # all_dict = tax_dict + wt_tax_dict
    #         # for rec in 
    #         # line.compute_all_tax.add(wt_tax_dict)
    #         # print('line.compute_all_tax^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^', all_dict)
    #         # if not line.tax_repartition_line_id:
    #         #     line.compute_all_tax = (tax_dict, wt_tax_dict)
    #         #     line.compute_all_tax = {
    #         #         'tax_tag_ids': [(6, 0, compute_all_currency['base_tags'])],
    #         #     }
    #         if not line.tax_repartition_line_id:
    #             line.compute_all_tax[frozendict({'id': line.id})] = {
    #                 'tax_tag_ids': [(6, 0, compute_all_currency['base_tags'])],
    #             }
            
    #         print("+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++", line.compute_all_tax)
    #         print("+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++", type(line.compute_all_tax))
    #         # print("+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++", line.compute_all_tax[frozendict({'id': line.id})])
    #     return res


class AccountMove(models.Model):
    _inherit = "account.move"

    cert_count = fields.Integer(string="Certificate Count", compute='_get_certificate')

    wt_cert_ids = fields.One2many(
        comodel_name="withholding.tax.cert",
        inverse_name="move_id",
        string="Withholding Tax Cert.",
        readonly=True,
    )
    wt_cert_cancel = fields.Boolean(
        compute="_compute_wt_cert_cancel",
        store=True,
        help="This document has WT Cert(s) and all are cancelled or not WT Cert",
    )

    @api.depends("wt_cert_ids.state")
    def _compute_wt_cert_cancel(self):
        for record in self:
            wt_state = list(set(record.wt_cert_ids.mapped("state")))
            wt_cancel = False
            if not wt_state or (len(wt_state) == 1 and "cancel" in wt_state):
                wt_cancel = True
            record.wt_cert_cancel = wt_cancel

    def button_wt_certs(self):
        # moves = self.wt_cert_ids.move_id.id
        # cert = self.env['withholding.tax.cert'].search([('move_id.id', '=', moves)])
        # result = self.env['ir.actions.act_window']._for_xml_id('sss_withholding_tax.action_withholding_tax_cert_menu')
        # if self.id == moves:
        #     if len(cert) > 1:
        #         result['domain'] = [('id', 'in', cert.ids)]
        #     elif len(cert) == 1:
        #         result['views'] = [(self.env.ref('sss_withholding_tax.view_withholding_tax_cert_form', False).id, 'form')]
        #         result['res_id'] = cert.id
        #     else:
        #         result = {'type': 'ir.actions.act_window_close'}
        #     return result
        return {
            "name": _("Withholding Tax Certs."),
            "view_mode": "tree,form",
            "res_model": "withholding.tax.cert",
            "view_id": False,
            "type": "ir.actions.act_window",
            "domain": [("id", "in", self.wt_cert_ids.ids)],
        }

    @api.depends('wt_cert_ids')
    def _get_certificate(self):
        for cert in self:
            certificate = cert.wt_cert_ids
            cert.cert_count = len(certificate)

    # Hitanshi's Code For Journal Entry

    # def write(self, vals):
    #     res = super(AccountMove, self).write(vals)
    #     print("res base create methon callllllllllll",res)
    #     for rec in self.invoice_line_ids:
    #         print("hitanshiiiiiiiiiiiiiiiiiii")
    #         if rec.wt_tax_id:
    #             wt_amt = rec.price_unit * rec.wt_tax_id.amount / 100
    #             base_amt = rec.price_unit
    #             name = rec.wt_tax_id.account_id.id
    #             self.line_ids.write([(0, 0, {
    #                 'name': name,
    #                 'debit': wt_amt,
    #                 'credit': 0.0,
    #             }), (0, 0, {
    #                 'name': 'Custom Journal Entry Line',
    #                 'debit': 0.0,
    #                 'credit': wt_amt,
    #             })])
    #             print('>>>>>>>>>>>>>>>>>>>>>>>>>>wt_amt', wt_amt)
    #             print('>>>>>>>>>>>>>>>>>>>>>>>>>>base_amt', base_amt)
    #             print('>>>>>>>>>>>>>>>>>>>>>>>>>>name', name)
    #             print('>>>>>>>>>>>>>>>>>>>>>>>>>>name', self.line_ids)
    #             rec.line_ids.write([])

    #     return res


    # @contextmanager
    # def _sync_dynamic_lines(self, container):
    #     # print('_sync_dynamic_lines===============custom call========')
    #     res = super(AccountMove, self)._sync_dynamic_lines(container)
    #     with self._disable_recursion(container, 'skip_invoice_sync') as disabled:
    #         if disabled:
    #             yield
    #             return
    #         # Only invoice-like and journal entries in "auto tax mode" are synced
    #         tax_filter = lambda m: (m.is_invoice(True) or m.line_ids.tax_ids and not m.tax_cash_basis_origin_move_id)
    #         invoice_filter = lambda m: (m.is_invoice(True))
    #         misc_filter = lambda m: (m.move_type == 'entry' and not m.tax_cash_basis_origin_move_id)

    #         #HITANSHI
    #         wt_tax_filter = lambda m: (m.is_invoice(True) or m.line_ids.wt_tax_id)

    #         tax_container = {'records': container['records'].filtered(tax_filter)}
    #         invoice_container = {'records': container['records'].filtered(invoice_filter)}
    #         misc_container = {'records': container['records'].filtered(misc_filter)}

    #         #HITASNHI
    #         wt_tax_contaier = {'records': container['records']. filtered(wt_tax_filter)}

    #         with ExitStack() as stack:
    #             stack.enter_context(self._sync_dynamic_line(
    #                 existing_key_fname='term_key',
    #                 needed_vals_fname='needed_terms',
    #                 needed_dirty_fname='needed_terms_dirty',
    #                 line_type='payment_term',
    #                 container=invoice_container,
    #             ))
    #             stack.enter_context(self._sync_unbalanced_lines(misc_container))
    #             stack.enter_context(self._sync_rounding_lines(invoice_container))
    #             stack.enter_context(self._sync_dynamic_line(
    #                 existing_key_fname='tax_key',
    #                 needed_vals_fname='line_ids.compute_all_tax',
    #                 needed_dirty_fname='line_ids.compute_all_tax_dirty',
    #                 line_type='tax',
    #                 container=tax_container,
    #             ))

    #             stack.enter_context(self._sync_dynamic_line(
    #                 existing_key_fname='epd_key',
    #                 needed_vals_fname='line_ids.epd_needed',
    #                 needed_dirty_fname='line_ids.epd_dirty',
    #                 line_type='epd',
    #                 container=invoice_container,
    #             ))

    #             # HITANSHI
    #             stack.enter_context(self._sync_dynamic_line(
    #                 existing_key_fname='wt_tax_key',
    #                 needed_vals_fname='line_ids._compute_all_tax',
    #                 needed_dirty_fname='line_ids.compute_all_tax_dirty',
    #                 line_type='tax',
    #                 container=wt_tax_contaier,
    #             ))

    #             stack.enter_context(self._sync_invoice(invoice_container))
    #             line_container = {'records': self.line_ids}
    #             with self.line_ids._sync_invoice(line_container):
    #                 yield
    #                 line_container['records'] = self.line_ids
    #             tax_container['records'] = container['records'].filtered(tax_filter)
    #             invoice_container['records'] = container['records'].filtered(invoice_filter)
    #             misc_container['records'] = container['records'].filtered(misc_filter)

    #             #HIANSHI
    #             wt_tax_contaier['records'] = container['records'].filtered(wt_tax_filter)

    #         # Delete the tax lines if the journal entry is not in "auto tax mode" anymore
    #         for move in container['records']:
    #             if move.move_type == 'entry' and not move.line_ids.tax_ids:
    #                 move.line_ids.filtered(
    #                     lambda l: l.display_type == 'tax'
    #                 ).with_context(dynamic_unlink=True).unlink()
    #     return res
    
    # @api.model_create_multi
    # def create(self, vals_list):
    #     print("hitanshiiiiiiiiiiiiiiiiiiiiiiiiiiii")
    #     res = super(AccountMove, self).create(vals_list)
    #     print('ressssssssssssssssssssssssssssssssss', res)
    #     # Add your custom journal entry
    #     for rec in self:
    #         for line in rec.invoice_line_ids:
    #             print('linessssssssssssssssssssss', line)
    #             if line.wt_tax_id:
    #                 name = line.wt_tax_id.name
    #                 tax_amt = line.price_unit * line.wt_tax_id.amount / 100
    #                 base_amt = line.price_unit
    #                 lines = rec.create({
    #                     'ref': 'Hitanshi',
    #                     'line_ids': [(0, 0, {
    #                         'name': name,
    #                         'account_id': line.wt_tax_id.account_id,
    #                         'debit': tax_amt,
    #                         'credit': 0.0,
    #                     }), (0, 0, {
    #                         'name': 'Custom Journal Entry Line',
    #                         'account_id': line.wt_tax_id.account_id,
    #                         'debit': 0.0,
    #                         'credit': tax_amt,
    #                     })]
    #                 })
    #                 print('lines##############################', lines)
    #     # journal_entry = self.env['account.move'].create({
    #     #     'ref': 'Hitanshi',
    #     #     'journal_id':
    #     #     'line_ids': [(0, 0, {
    #     #         'name': 'Custom Journal Entry Line',
    #     #         'account_id': 1, 
    #     #         'debit': 100.0,  
    #     #         'credit': 0.0,
    #     #     }), (0, 0, {
    #     #         'name': 'Custom Journal Entry Line',
    #     #         'account_id': 2,  
    #     #         'debit': 0.0,
    #     #         'credit': 100.0,
    #     #     })]
    #     # })

    #     return res