# -*- encoding: utf-8 -*-
from odoo import models, fields, api
# from odoo.addons.client_bista_odoo_bill_com_connector.models.connection import BillComService
import json
import requests
from odoo.exceptions import ValidationError, UserError

"""
    This wizard is used to update company data
    """


class UpdateCompanyData(models.TransientModel):
    _name = 'update.company.data'
    _description = 'Bill.com Update Vendor Data'

    company_ids = fields.Many2many('res.company')
    partner_id = fields.Many2one('res.partner', string='Partner')
    street = fields.Char('Street')
    street2 = fields.Char('Street2')
    zip_code = fields.Char('Zip')
    city = fields.Char('City')
    state_id = fields.Many2one("res.country.state", string="State")
    country_id = fields.Many2one('res.country', string="Country")
    email = fields.Char('Email')
    phone = fields.Char('Phone')
    supplier_currency_id = fields.Many2one(
        'res.currency', string="Supplier Currency", company_dependent=True,
        help="This currency will be used, instead of the default one, for purchases from the current partner")

    @api.model
    def default_get(self, fields):
        res = super(UpdateCompanyData, self).default_get(fields)
        context = self._context
        if 'default_partner_id' in context:
            default_partner_id = context.get('default_partner_id')
            res['partner_id'] = default_partner_id
            partner_id_brw = self.env['res.partner'].sudo().browse(default_partner_id)
            street = partner_id_brw.street
            street2 = partner_id_brw.street2
            zip_code = partner_id_brw.zip
            city = partner_id_brw.city
            state_id = partner_id_brw.state_id
            country_id = partner_id_brw.country_id
            email = partner_id_brw.email
            phone = partner_id_brw.phone
            company_ids = partner_id_brw.bill_com_vendor_data.company_id.ids
            supplier_currency_id = partner_id_brw.property_purchase_currency_id
            res.update({'street': street, 'street2': street2, 'city': city,
                        'state_id': state_id.id if state_id else False,
                        'zip_code': zip_code, 'country_id': country_id.id if country_id else False,
                        'phone': phone, 'email': email,'supplier_currency_id': supplier_currency_id,
                        'company_ids': [(6, 0, company_ids)]})
        return res

    def create_write_vendor_info(self, bill_com_config_obj):
        if bill_com_config_obj:
            bill_com_user_name = bill_com_config_obj.bill_com_user_name
            if bill_com_user_name:
                bill_com_password = bill_com_config_obj.bill_com_password
                bill_com_orgid = bill_com_config_obj.bill_com_orgid
                bill_com_devkey = bill_com_config_obj.bill_com_devkey
                bill_com_login_url = bill_com_config_obj.bill_com_login_url
                bill_com_vendor_create_url = bill_com_config_obj.bill_com_vendor_create_url
                bill_com_vendor_update_url = bill_com_config_obj.bill_com_vendor_update_url
                company_ids = bill_com_config_obj.company_ids.ids
                name = self.partner_id.name
                bill_com_vendor_id = self.partner_id.get_bill_com_vendor_id(self.partner_id, company_ids=company_ids)
                data = {"obj": {"entity": "Vendor"}}
                if bill_com_vendor_id:
                    data["obj"].update({"id": bill_com_vendor_id, "name": name})
                else:
                    data["obj"].update({"isActive": "1", "name": name, "payBy": "0"})
                company_type = self.partner_id.company_type
                bill_com_company_type = '0'
                if company_type == 'company':
                    bill_com_company_type = '1'
                elif company_type == 'person':
                    bill_com_company_type = '2'
                data["obj"].update({"accountType": bill_com_company_type})    
                street = self.street
                data["obj"].update({"address1": street or ''})
                street2 = self.street2
                data["obj"].update({"address2": street2 or ''})
                city = self.city
                data["obj"].update({"addressCity": city or ''})
                state_id = self.state_id
                if state_id:
                    data["obj"].update({"addressState": state_id.code})
                else:
                    data["obj"].update({"addressState": ''})
                addresszip = self.zip_code
                data["obj"].update({"addressZip": addresszip or ''})
                country_id = self.country_id
                if country_id:
                    data["obj"].update({"addressCountry": country_id.name})
                else:
                    data["obj"].update({"addressCountry": ''})
                email = self.email
                data["obj"].update({"email": email or ''})
                phone = self.phone
                data["obj"].update({"phone": phone or ''})
                currency_id = self.partner_id.property_purchase_currency_id.name
                if currency_id:
                    data["obj"].update({"billCurrency": currency_id})
                data = json.dumps(data)
                params = {
                    'bill_com_user_name': bill_com_user_name,
                    'bill_com_password': bill_com_password,
                    'bill_com_orgid': bill_com_orgid,
                    'bill_com_devkey': bill_com_devkey,
                    'bill_com_login_url': bill_com_login_url,
                    'bill_com_vendor_update_url': bill_com_vendor_update_url,
                    'bill_com_vendor_create_url': bill_com_vendor_create_url,
                    'bill_com_vendor_id': bill_com_vendor_id,
                    'data': data,
                }
                url = self.env['ir.config_parameter'].sudo().get_param('client_subscription.host_db_url')
                if not url:
                    raise UserError("Please Configure Sevice DB URL in General settings.")

                response = requests.post(
                    f"{url}/create_write_vendor_info",
                    json=params,
                    headers={'Content-Type': 'application/json'},
                    verify=False
                )
                if response.status_code == 200:
                    result = response.json()
                    if result.get('result') and result['result'].get('status') == 'success':
                        bill_com_vendor_id = result['result'].get('response')
                        return bill_com_vendor_id
               
               
    def send_vendor_info(self):
        context = self._context
        user_name = self.env['res.users'].sudo().browse(self._uid).name
        bill_com_config_obj = self.env['bill.com.config']
        bill_com_vendor_company_data_obj = self.env['bill.com.vendor.company.data']
        company_ids = self.company_ids
        partner_id = self.partner_id
        street = self.street
        street2 = self.street2
        city = self.city
        state_id = self.state_id
        zip_code = self.zip_code
        country_id = self.country_id
        phone = self.phone
        email = self.email
        currency_id = self.supplier_currency_id
        auto_update_check = context.get('auto_update', False)
        if not auto_update_check:
            partner_id.write({'street': street, 'street2': street2, 'city': city,
                              'state_id': state_id.id if state_id else False,
                              'zip': zip_code, 'country_id': country_id.id if country_id else False,
                              'phone': phone, 'email': email, 'property_purchase_currency_id': currency_id
                              })
        cr = self._cr
        cr.execute("select distinct(bill_com_config_id) from bill_com_config_company_rel where company_id in %s",
                   (tuple(company_ids.ids),))
        bill_config_ids = list(filter(None, map(lambda x: x[0], cr.fetchall())))
        if bill_config_ids:
            bill_config_data = {}
            # This is required to check credentials of Bill.com are correct or not before pushing into Bill.com.
            for each_bill_config in bill_com_config_obj.sudo().browse(bill_config_ids):
                if each_bill_config.state == 'expired':
                    raise ValidationError('Can not Send Vendor To Bill.com as your subscription expired.')
                else:
                    bill_com_user_name = each_bill_config.bill_com_user_name
                    bill_com_password = each_bill_config.bill_com_password
                    bill_com_orgid = each_bill_config.bill_com_orgid
                    bill_com_devkey = each_bill_config.bill_com_devkey
                    bill_com_login_url = each_bill_config.bill_com_login_url
                    # bill_com_service_obj = BillComService(bill_com_user_name, bill_com_password, bill_com_orgid,
                    #                                       bill_com_devkey, bill_com_login_url, config_id=each_bill_config)
                    bill_config_data[each_bill_config.id] = each_bill_config.company_ids.ids
            for each_bill_config in bill_com_config_obj.sudo().browse(bill_config_ids):
                if each_bill_config.state == 'expired':
                    raise ValidationError('Can not Send Vendor To Bill.com as your subscription expired.')
                else:
                    company_ids = each_bill_config.company_ids
                    bill_com_vendor_id = self.create_write_vendor_info(each_bill_config)
                    if bill_com_vendor_id:
                        company_ids = each_bill_config.company_ids
                        for each_company_rec in company_ids:
                            odoo_bill_com_vendor_id = partner_id.get_bill_com_vendor_id(partner_id,
                                                                                        company_id=each_company_rec)
                            if not odoo_bill_com_vendor_id:
                                bill_com_vendor_company_data_obj.sudo().create({'partner_id': partner_id.id,
                                                                                'company_id': each_company_rec.id,
                                                                                'bill_com_vendor_id': bill_com_vendor_id})
            message = ("""Update on Bill.com is done by %s""" % (user_name))
            partner_id.message_post(body=message)
