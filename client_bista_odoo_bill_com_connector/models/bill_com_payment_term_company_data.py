# -*- encoding: utf-8 -*-
##############################################################################
#
# Bista Solutions Pvt. Ltd
# Copyright (C) 2020 (http://www.bistasolutions.com)
#
##############################################################################

from odoo import models, fields, api


class BillComPaymentTermCompanyData(models.Model):
    _name = 'bill.com.payment.term.company.data'
    _description = 'Bill.com Payment Term IDS'
    _order = 'company_id asc'

    payment_term_id = fields.Many2one('account.payment.term', string='Payment Term')
    bill_com_payment_term_id = fields.Char('Bill.com ID', copy=False)
    company_id = fields.Many2one('res.company', string='Company')