# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
# from .connection import BillComService
import json
import requests
from odoo.exceptions import UserError, ValidationError


class ResPartner(models.Model):
    _inherit = 'res.partner'

    bill_com_vendor_id = fields.Char('Bill.com Vendor ID', copy=False)
    bank_ids = fields.One2many('res.partner.bank', 'partner_id', "Bank Accounts", context={'active_test': False})
    bill_com_vendor_data = fields.One2many('bill.com.vendor.company.data', 'partner_id',string='Vendor Data')


    def get_bill_com_vendor_id(self, partner_id, company_id=False, company_ids=[]):
        cr = self._cr
        if partner_id and company_id:
            cr.execute("select bill_com_vendor_id from bill_com_vendor_company_data where partner_id=%s and company_id = %s" %(partner_id.id, company_id.id))
            bill_com_vendor_id = list(filter(None, map(lambda x: x[0], cr.fetchall())))
            if bill_com_vendor_id:
                return bill_com_vendor_id[0]
        elif partner_id and company_ids:
            cr.execute("select bill_com_vendor_id from bill_com_vendor_company_data where partner_id=%s and company_id in %s",(partner_id.id, tuple(company_ids),))
            bill_com_vendor_id = list(filter(None, map(lambda x: x[0], cr.fetchall())))
            if bill_com_vendor_id:
                return bill_com_vendor_id[0]
            return False

    def get_odoo_vendor_id(self, bill_com_vendor_id):
        if bill_com_vendor_id:
            cr = self._cr
            cr.execute("select partner_id from bill_com_vendor_company_data where bill_com_vendor_id='%s'" %(bill_com_vendor_id))
            partner_id = list(filter(None, map(lambda x: x[0], cr.fetchall())))
            if partner_id:
                return partner_id
            return False

    def auto_update_vendor_data_wizard(self, bill_com_company_ids):
        update_company_data_obj = self.env['update.company.data']
        vals_wiz = update_company_data_obj.sudo().create({'partner_id': self.id,
                                                          'street': self.street,
                                                          'street2': self.street2,
                                                          'zip_code': self.zip,
                                                          'city': self.city,
                                                          'state_id': self.state_id.id,
                                                          'country_id': self.country_id.id,
                                                          'phone': self.phone,
                                                          'company_ids': bill_com_company_ids,
                                                          'supplier_currency_id': self.property_purchase_currency_id.id,
                                                          'email': self.email,
                                                          })
        vals_wiz.send_vendor_info()

    def update_company_data(self):
        # if self.is_lock:
        #     pass
        # else:
        return {
            'name': _('Update on Bill.Com'),
            'res_model': 'update.company.data',
            'view_mode': 'form',
            'context': {
                'active_model': 'res.partner',
                'active_ids': self.ids,
                'default_partner_id': self.id
            },
            'target': 'new',
            'type': 'ir.actions.act_window',
        }


    def action_bulk_vendor_send_bill_com_btn(self):
        context = self._context
        active_ids = context.get('active_ids')
        return {
            'name': _('Send to Bill.com'),
            'res_model': 'bulk.vendor.send.bill.com',
            'view_mode': 'form',
            'context': {
                'active_model': 'res.partner',
                'active_ids': active_ids,
                # 'default_partner_id': self.id
            },
            'target': 'new',
            'type': 'ir.actions.act_window',
        }

    def send_vendor_to_bill_com(self, bill_config_ids):
        print("====================send_vendor_to_bill_com=")
        bill_com_vendor_company_data_obj = self.env['bill.com.vendor.company.data']
        partner_obj = self.env['res.partner']
        for each_bill_config in bill_config_ids:
            if each_bill_config.state == 'expired':
                raise ValidationError('Can not Send Vendors To Bill.com as your subscription expired.')
            else:
                final_data, odoo_vendor_data = [], {}
                for each_vendor in self:
                    name = each_vendor.name
                    data = {"obj": {"entity": "Vendor"}}
                    data["obj"].update({"isActive": "1", "name": name, "payBy": "0"})
                    company_type = each_vendor.company_type
                    bill_com_company_type = '0'
                    if company_type == 'company':
                        bill_com_company_type = '1'
                    elif company_type == 'person':
                        bill_com_company_type = '2'
                    data["obj"].update({"accountType": bill_com_company_type})    
                    street = each_vendor.street
                    data["obj"].update({"address1": street or ''})
                    street2 = each_vendor.street2
                    data["obj"].update({"address2": street2 or ''})
                    city = each_vendor.city
                    data["obj"].update({"addressCity": city or ''})
                    state_id = each_vendor.state_id
                    if state_id:
                        data["obj"].update({"addressState": state_id.code})
                    else:
                        data["obj"].update({"addressState": ''})
                    addresszip = each_vendor.zip
                    data["obj"].update({"addressZip": addresszip or ''})
                    country_id = each_vendor.country_id
                    if country_id:
                        data["obj"].update({"addressCountry": country_id.name})
                    else:
                        data["obj"].update({"addressCountry": ''})
                    email = each_vendor.email
                    data["obj"].update({"email": email or ''})
                    phone = each_vendor.phone
                    data["obj"].update({"phone": phone or ''})
                    currency_id = each_vendor.property_purchase_currency_id.name
                    if currency_id:
                        data["obj"].update({"billCurrency": currency_id})
                    final_data.append(data)
                if final_data:
                    final_dict = {"bulk": final_data}
                    print(">>>>>>>>>>>>>>>>>>>>>. final_dict", final_dict)
                    print(">>>>>>>>>>>>>>>>>>>>>. ids", self.ids)
                    # final_dict = json.dumps(final_dict)
                    bill_com_user_name = each_bill_config.bill_com_user_name
                    bill_com_password = each_bill_config.bill_com_password
                    bill_com_orgid = each_bill_config.bill_com_orgid
                    bill_com_devkey = each_bill_config.bill_com_devkey
                    bill_com_login_url = each_bill_config.bill_com_login_url
                    bill_com_vendor_bulk_create_url = each_bill_config.bill_com_vendor_bulk_create_url
                    if bill_com_vendor_bulk_create_url:
                        # bill_com_service_obj = BillComService(bill_com_user_name, bill_com_password, bill_com_orgid, bill_com_devkey, bill_com_login_url)
                        # bill_com_vendor_data = bill_com_service_obj.create_bulk_vendor_api(bill_com_vendor_bulk_create_url, final_dict, self.ids)
                        params = {
                            'bill_com_user_name': bill_com_user_name,
                            'bill_com_password': bill_com_password,
                            'bill_com_orgid': bill_com_orgid,
                            'bill_com_devkey': bill_com_devkey,
                            'bill_com_login_url': bill_com_login_url,
                            'bill_com_vendor_bulk_create_url': bill_com_vendor_bulk_create_url,
                            'data': final_dict,
                            'ids': self.ids,
                        }
                        print(">>>>>>>>>>>>>>>>>> params", params)
                        url = self.env['ir.config_parameter'].sudo().get_param('client_subscription.host_db_url')
                        if not url:
                            raise UserError("Please Configure Sevice DB URL in General settings.")

                        response = requests.post(
                            f"{url}/create_bulk_vendor_api",
                            json=params,
                            headers={'Content-Type': 'application/json'},
                            verify=False
                        )
                        print(">>>>>>>>>>>>>>>>>>>>>>>>> response", response)
                        if response.status_code == 200:
                            result = response.json()
                            print("=================== result", result)
                            if result.get('result') and result['result'].get('status') == 'success':
                                bill_com_vendor_data = result['result'].get('data')
                                print("--------------------bill_com_vendor_data", bill_com_vendor_data)
                                if bill_com_vendor_data:
                                    for odoo_vendor_id,vendor_data in bill_com_vendor_data.items():
                                        print("=======================", odoo_vendor_id)
                                        print("=======================", vendor_data)
                                        partner_id = partner_obj.browse(int(odoo_vendor_id))
                                        print("========================", partner_id)
                                        response_data = vendor_data.get('response_data', {})
                                        bill_com_vendor_id = response_data.get('id')
                                        company_ids = each_bill_config.company_ids
                                        for each_company_rec in company_ids:
                                            bill_com_vendor_company_data_obj.sudo().create({'partner_id': partner_id.id,
                                                                                            'company_id': each_company_rec.id,
                                                                                    'bill_com_vendor_id': bill_com_vendor_id})