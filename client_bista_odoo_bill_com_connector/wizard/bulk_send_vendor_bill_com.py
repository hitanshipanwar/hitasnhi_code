# -*- encoding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
# from odoo.addons.client_bista_odoo_bill_com_connector.models.connection import BillComService


class BulkVendorSendBillCom(models.TransientModel):
    """
    This wizard is used send the Invoices to the Bill.com in Bulk.
    """
    _name = 'bulk.vendor.send.bill.com'
    _description = 'Bulk Vendor Send to Bill.com'

    company_ids = fields.Many2many('res.company', 'bulk_vendor_send_company_rel', 'wizard_id', 'company_id',
                                   string='Companies', copy=False)
    show_company_ids = fields.Boolean('Show Company field')

    @api.model
    def default_get(self, default_fields):
        res = super(BulkVendorSendBillCom, self).default_get(default_fields)
        search_bill_com_config = self.env['bill.com.config'].search([])
        if len(search_bill_com_config) > 1:
            res.update({'show_company_ids': True})
        return res

    def bulk_vendor_send_bill_com_btn(self):
        context = self._context
        active_ids = context.get('active_ids')
        res_partner_brw = self.env['res.partner'].sudo().browse(active_ids)
        cr = self._cr
        company_ids = self.company_ids
        if company_ids:
            cr.execute("select distinct(bill_com_config_id) from bill_com_config_company_rel where company_id in %s",
                       (tuple(company_ids.ids),))
        else:
             cr.execute("select id from bill_com_config")   
        bill_config_ids = list(filter(None, map(lambda x: x[0], cr.fetchall())))
        if bill_config_ids:
            bill_com_config_obj = self.env['bill.com.config']
            bill_com_config_brw_ids = bill_com_config_obj.sudo().browse(bill_config_ids)
            # This is required to check credentials of Bill.com are correct or not before pushing into Bill.com.
            for each_bill_config in bill_com_config_brw_ids:
                bill_com_user_name = each_bill_config.bill_com_user_name
                bill_com_password = each_bill_config.bill_com_password
                bill_com_orgid = each_bill_config.bill_com_orgid
                bill_com_devkey = each_bill_config.bill_com_devkey
                bill_com_login_url = each_bill_config.bill_com_login_url
                # bill_com_service_obj = BillComService(bill_com_user_name, bill_com_password, bill_com_orgid,
                #                                       bill_com_devkey, bill_com_login_url, config_id=each_bill_config)
            res_partner_brw.send_vendor_to_bill_com(bill_com_config_brw_ids)