# -*- coding: utf-8 -*-
from odoo import api, fields, models, _




class BillComUsersCompanyData(models.Model):
    _name = 'bill.com.users.company.data'
    _description = 'Bill.com User IDS'
    _order = 'company_id asc'

    user_id = fields.Many2one('res.users', string='Users')
    bill_com_user_id = fields.Char('User ID')
    company_id = fields.Many2one('res.company', string='Company')


class Users(models.Model):
    _inherit = "res.users"

    bill_com_user_data = fields.One2many('bill.com.users.company.data', 'user_id', string='User Data')
    
    def get_bill_com_user_id(self, user_id, company_id=False, company_ids=[]):
        cr = self._cr
        if user_id and company_id:
            cr.execute("select bill_com_user_id from bill_com_users_company_data where user_id=%s and company_id = %s" %(user_id.id, company_id.id))
            bill_com_user_id = list(filter(None, map(lambda x: x[0], cr.fetchall())))
            if bill_com_user_id:
                return bill_com_user_id[0]
        elif user_id and company_ids:
            cr.execute("select bill_com_user_id from bill_com_users_company_data where user_id=%s and company_id in %s",(user_id.id, tuple(company_ids),))
            bill_com_user_id = list(filter(None, map(lambda x: x[0], cr.fetchall())))
            if bill_com_user_id:
                return bill_com_user_id[0]
            return False