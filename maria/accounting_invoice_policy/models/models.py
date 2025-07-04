# -*- coding: utf-8 -*-

from odoo import models, fields
from itertools import groupby
from odoo.exceptions import AccessError


class ResPartner(models.Model):
    _inherit = 'res.partner'

    accounting_invoice_policy = fields.Selection([('combine_invoices', 'Combine Invoices'),
                                                  ('never_combine_invoice', 'Never Combine Invoices'),
                                                  ('split_invoice_per_vat', 'Split Invoice per VAT')],
                                                 required=True, default='combine_invoices',
                                                 string="Accounting Invoice Policy")


class SaleOrderLine(models.Model):
    _inherit = 'sale.order'

    def _create_invoices(self, grouped=False, final=False, date=None):
        if not self.env['account.move'].check_access_rights('create', False):
            try:
                self.check_access_rights('write')
                self.check_access_rule('write')
            except AccessError:
                return self.env['account.move']

        invoice_vals_list = []
        invoice_item_sequence = 0
        for order in self:
            order = order.with_company(order.company_id)
            # current_section_vals = None
            # down_payments = order.env['sale.order.line']
            invoice_vals = order._prepare_invoice()
            invoiceable_lines = order._get_invoiceable_lines(final)
            if not any(not line.display_type for line in invoiceable_lines):
                continue
            invoice_line_vals = []
            down_payment_section_added = False
            for line in invoiceable_lines:
                if not down_payment_section_added and line.is_downpayment:
                    invoice_line_vals.append(
                        (0, 0, order._prepare_down_payment_section_line(
                            sequence=invoice_item_sequence,
                        )),
                    )
                    down_payment_section_added = True
                    invoice_item_sequence += 1
                invoice_line_vals.append(
                    (0, 0, line._prepare_invoice_line(
                        sequence=invoice_item_sequence,
                    )),
                )
                invoice_item_sequence += 1

            invoice_vals['invoice_line_ids'] += invoice_line_vals
            invoice_vals_list.append(invoice_vals)
        if not grouped:
            new_invoice_vals_list = []
            invoice_grouping_keys = self._get_invoice_grouping_keys()
            invoice_vals_list = sorted(
                invoice_vals_list,
                key=lambda x: [
                    x.get(grouping_key) for grouping_key in invoice_grouping_keys
                ]
            )
            group_invoice = []
            create_invoice_vals_list = []
            Partner = self.env['res.partner']
            print('\n\n\n\ninvoice_vals_list>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>',invoice_vals_list)
            for invoice in invoice_vals_list:
                partner = Partner.browse(invoice['partner_id'])
                if partner.accounting_invoice_policy == 'never_combine_invoice':
                    create_invoice_vals_list.append(invoice)
                else:
                    group_invoice.append(invoice)

            for grouping_keys, invoices in groupby(group_invoice, key=lambda x: [x.get(grouping_key) for grouping_key in
                                                                                 invoice_grouping_keys]):
                partner = Partner.browse(grouping_keys[1])
                if partner.accounting_invoice_policy == 'split_invoice_per_vat':
                    group_line = dict()
                    ref_invoice_vals = False
                    for invoice in invoices:
                        new_invoice_dict = invoice.copy()
                        origins = set()
                        payment_refs = set()
                        refs = set()
                        ref_invoice_vals = new_invoice_dict
                        origins.add(new_invoice_dict['invoice_origin'])
                        payment_refs.add(new_invoice_dict['payment_reference'])
                        refs.add(new_invoice_dict['ref'])
                        ref_invoice_vals.update({
                            'ref': ', '.join(refs)[:2000],
                            'invoice_origin': ', '.join(origins),
                            'payment_reference': len(payment_refs) == 1 and payment_refs.pop() or False,
                        })
                        for i in range(len(invoice['invoice_line_ids'])):
                            print('\n\n\n\n>>>>>>>>>>>>>>>>>>>>>.......iiiiiiiiii',i)
                            skip = False
                            for key in group_line.keys():
                                line = group_line[key]
                                if not line['tax_ids'] and not invoice['invoice_line_ids'][i][2]['tax_ids']:
                                    print('line[tax_ids]>>>>>>>>.>>>>>>>>>>>>>>>>>>>',line['tax_ids'])
                                    print('======================================',invoice['invoice_line_ids'])
                                    print('>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>',invoice['invoice_line_ids'][i][2]['tax_ids'])
                                    group_line[key]['keys'].append(invoice['invoice_line_ids'][i])
                                    skip = True
                                    break
                                if line['tax_ids'] and invoice['invoice_line_ids'][i][2]['tax_ids'] and \
                                        line['tax_ids'][0] == invoice['invoice_line_ids'][i][2]['tax_ids'][0][2][0]:
                                    group_line[key]['keys'].append(invoice['invoice_line_ids'][i])
                                    skip = True
                                    break

                            if skip:
                                continue
                            group_line[i] = {
                                'tax_ids': invoice['invoice_line_ids'][i][2]['tax_ids'][0][2] if
                                invoice['invoice_line_ids'][i][2]['tax_ids'][0][2] and len(
                                    invoice['invoice_line_ids'][i][2]['tax_ids']) else False,
                                'keys': [invoice['invoice_line_ids'][i]]
                            }
                            print('group_line>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>',group_line)
                    ref_invoice_vals['invoice_line_ids'] = []
                    for key in group_line.keys():
                        line = group_line[key]
                        new_invoice = ref_invoice_vals.copy()
                        new_invoice['invoice_line_ids'] = line['keys']
                        new_invoice_vals_list.append(new_invoice)
                else:
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
            create_invoice_vals_list += new_invoice_vals_list
            invoice_vals_list = create_invoice_vals_list
        if len(self) > len(invoice_vals_list):
            SaleOrderLine = self.env['sale.order.line']
            for invoice in invoice_vals_list:
                sequence = 1
                for line in invoice['invoice_line_ids']:
                    line[2]['sequence'] = SaleOrderLine._get_invoice_line_sequence(new=sequence,
                                                                                   old=line[2]['sequence'])
                    sequence += 1
        moves = self.env['account.move'].sudo().with_context(default_move_type='out_invoice').create(invoice_vals_list)
        if final:
            moves.sudo().filtered(lambda m: m.amount_total < 0).action_switch_invoice_into_refund_credit_note()
        for move in moves:
            move.message_post_with_view('mail.message_origin_link',
                                        values={'self': move, 'origin': move.line_ids.mapped('sale_line_ids.order_id')},
                                        subtype_id=self.env.ref('mail.mt_note').id
                                        )
        return moves
