from odoo import models, fields, api,_
# from odoo.addons.client_bista_odoo_bill_com_connector.models.connection import BillComService


class RegisterPaymentAuth(models.TransientModel):
    """
    This wizard is used to authenticate register payment
    """
    _name = 'register.payment.auth'

    auth_username = fields.Char(string='Username')
    auth_password = fields.Char(string='Password')

    def action_default_wizard(self):
        active_ids = self._context.get('active_ids', [])
        context = self._context
        allowed_company_ids = context.get('allowed_company_ids', False)
        company_id_brw = self.env['res.company'].sudo().browse(allowed_company_ids[0])
        bill_com_config_obj = self.env['bill.com.config'].sudo().get_bill_com_config(company_id_brw.sudo().id)
        if bill_com_config_obj:
            bill_com_user_name = self.auth_username
            bill_com_password = self.auth_password
            bill_com_orgid = bill_com_config_obj.bill_com_orgid
            bill_com_devkey = bill_com_config_obj.bill_com_devkey
            bill_com_login_url = bill_com_config_obj.bill_com_login_url
            bill_com_service_obj = BillComService(bill_com_user_name, bill_com_password, bill_com_orgid,
                                                  bill_com_devkey, bill_com_login_url)
        return {
                'name': _('Register Payment'),
                'res_model': 'account.payment.register',
                'view_mode': 'form',
                'context': {
                    'active_model': 'account.move',
                    'active_ids': active_ids,
                },
                'target': 'new',
                'type': 'ir.actions.act_window',
            }

