# -*- encoding: utf-8 -*-
##############################################################################
#
# Bista Solutions Pvt. Ltd
# Copyright (C) 2020 (http://www.bistasolutions.com)
#
##############################################################################

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class BillComPaymentMethods(models.Model):
    _name = 'bill.com.payment.methods'
    _description = 'Bill.com Payment Methods'
    _rec_name = 'payment_method'

    @api.constrains('company_id', 'payment_method')
    def _check_company_id_payment_method(self):
        bill_com_payment_method_obj = self.env['bill.com.payment.methods']
        for each_method in self.sudo():
            company_id = each_method.company_id
            payment_method = each_method.payment_method
            odoo_rec_found  = bill_com_payment_method_obj.sudo().search([('id', '!=', each_method.id),('company_id', '=', company_id.id), ('payment_method', '=', payment_method)])
            if odoo_rec_found:
                raise ValidationError(_('You cannot set same payment method twice for same company.'))

    payment_method = fields.Selection([('0','Check'),
        ('2','RPPS'), ('3','PayPal'),
        ('4','Other'), ('5','InltEpmt'),
        ('6','Amex'), ('7','VCard'),
        ('11','Wallet'), ('12','CreditCard')], string="Method", copy=False)
    journal_id = fields.Many2one('account.journal',string='Journal', copy=False, help="Selected journal will be used while importing payments based on the Payment method linked")
    company_id = fields.Many2one('res.company', 'Company', copy=False, default=lambda self: self.env.company)