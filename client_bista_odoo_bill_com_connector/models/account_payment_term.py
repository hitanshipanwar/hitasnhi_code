# -*- coding: utf-8 -*-

from odoo import models, fields, api


class AccountPaymentTerm(models.Model):
    _inherit = 'account.payment.term'

    bill_com_payment_term_ids = fields.One2many('bill.com.payment.term.company.data', 'payment_term_id',string='Bill.com Payment Term IDS')

    def get_bill_com_payment_term_id(self, payment_term_id, company_id=False):
        # cr = self._cr
        if payment_term_id and company_id:
            bill_com_payment_term_id = self.env['bill.com.payment.term.company.data'].sudo().search([('payment_term_id', '=', payment_term_id.id),('company_id', '=', company_id.id)])

            # cr.execute("select bill_com_payment_term_id from bill_com_payment_term_company_data where payment_term_id=%s and company_id = %s" %(payment_term_id.id, company_id.id))
            # bill_com_payment_term_id = list(filter(None, map(lambda x: x[0], cr.fetchall())))
            if bill_com_payment_term_id:
                return bill_com_payment_term_id[0].bill_com_payment_term_id
            return False
