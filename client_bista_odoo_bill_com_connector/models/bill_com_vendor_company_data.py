# -*- encoding: utf-8 -*-
##############################################################################
#
# Bista Solutions Pvt. Ltd
# Copyright (C) 2020 (http://www.bistasolutions.com)
#
##############################################################################

from odoo import models, fields, api


class BillComVendorCompanyData(models.Model):
    _name = 'bill.com.vendor.company.data'
    _description = 'Bill.com Vendor IDS'
    _order = 'company_id asc'

    partner_id = fields.Many2one('res.partner', string='Partner')
    bill_com_vendor_id = fields.Char('Vendor ID')
    company_id = fields.Many2one('res.company', string='Company')
