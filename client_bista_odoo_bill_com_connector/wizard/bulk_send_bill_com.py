from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class BulkSendBillCom(models.TransientModel):
    """
    This wizard is used send the Invoices to the Bill.com in Bulk.
    """
    _name = 'bulk.send.bill.com'
    _description = 'Bulk Send to Bill.com'

    # @api.model
    # def get_view(self, view_id=None, view_type='form', **options):
    #     print("####################################")
    #     res = super().get_view(view_id, view_type, **options)
    #     context = self._context
    #     active_ids = context.get('active_ids', [])
    #     active_model = context.get('active_model', '')
    #     if active_ids and active_model == 'account.move':
    #         active_ids_brw = self.env[active_model].sudo().browse(active_ids)
    #         selected_wrong_records = self.env[active_model].sudo().search(
    #             [('id', 'in', active_ids), '|', '|', '|', ('move_type', '!=', 'in_invoice'), ('state', '!=', 'posted'),
    #              ('bill_com_bill_id', '!=', False), ('payment_state', '!=', 'not_paid')])
    #         print("===================== selected_wrong_records", selected_wrong_records)
    #         if selected_wrong_records:
    #             raise ValidationError('Please select only Posted, Not Paid and not sent to Bill.com Vendor invoices.')
    #         vendor_dict = {}
    #         for each_inv in active_ids_brw:
    #             company_id = each_inv.company_id
    #             company_name = company_id.name
    #             non_bill_com_vendor_ids = self.env[active_model].sudo().search(
    #                 [('id', '=', each_inv.id), ('partner_id.bill_com_vendor_data.company_id', 'in', company_id.ids)])
    #             if not non_bill_com_vendor_ids:
    #                 partner_id = each_inv.partner_id
    #                 if partner_id.id not in vendor_dict:
    #                     vendor_dict[partner_id.id] = {'vendor_name': partner_id.name,
    #                                                   'not_found_company_names': company_name}
    #                 else:
    #                     existing_not_found_company_names = vendor_dict.get(partner_id.id, {}).get(
    #                         'not_found_company_names', '')
    #                     if company_name not in existing_not_found_company_names:
    #                         vendor_dict[partner_id.id].update(
    #                             {'not_found_company_names': existing_not_found_company_names + ',%s' % (company_name)})
    #         final_message = ''
    #         for key, value in vendor_dict.items():
    #             vendor_name = value.get('vendor_name', '')
    #             not_found_company_names = value.get('not_found_company_names', '')
    #             final_message += '%s - %s \n' % (vendor_name, not_found_company_names)
    #         if final_message:
    #             raise ValidationError(
    #                 'Following Vendors not found in bill.com ! If a new Vendor is created, please ensure it is pushed to Bill.com.\n%s' % (
    #                     final_message))
    #     return res

    @api.model
    def default_get(self, fields):
        res = super().default_get(fields)
        context = self._context
        active_ids = context.get('active_ids', [])
        active_model = context.get('active_model', '')
        active_ids_brw = self.env[active_model].sudo().browse(active_ids)
        if active_ids and active_model == 'account.move':
            selected_wrong_records = self.env[active_model].sudo().search(
                [('id', 'in', active_ids), '|', '|', '|', ('move_type', '!=', 'in_invoice'),
                 ('state', '!=', 'posted'), ('bill_com_bill_id', '!=', False),
                 ('payment_state', '!=', 'not_paid')])
            if selected_wrong_records:
                raise ValidationError(
                    'Please select only Posted, Not Paid, and not sent to Bill.com Vendor invoices.')

            vendor_dict = {}
            for each_inv in active_ids_brw:
                company_id = each_inv.company_id
                company_name = company_id.name
                non_bill_com_vendor_ids = self.env[active_model].sudo().search(
                    [('id', '=', each_inv.id), ('partner_id.bill_com_vendor_data.company_id', 'in', company_id.ids)])
                if not non_bill_com_vendor_ids:
                    partner_id = each_inv.partner_id
                    if partner_id.id not in vendor_dict:
                        vendor_dict[partner_id.id] = {'vendor_name': partner_id.name,
                                                      'not_found_company_names': company_name}
                    else:
                        existing_not_found_company_names = vendor_dict.get(partner_id.id, {}).get(
                            'not_found_company_names', '')
                        if company_name not in existing_not_found_company_names:
                            vendor_dict[partner_id.id].update(
                                {'not_found_company_names': existing_not_found_company_names + ',%s' % (company_name)})
            final_message = ''
            for key, value in vendor_dict.items():
                vendor_name = value.get('vendor_name', '')
                not_found_company_names = value.get('not_found_company_names', '')
                final_message += '%s - %s \n' % (vendor_name, not_found_company_names)
            if final_message:
                raise ValidationError(
                    'Following Vendors not found in bill.com ! If a new Vendor is created, please ensure it is pushed to Bill.com.\n%s' % (
                        final_message))
        return res

    def bulk_send_bill_com_btn(self):
        context = self._context
        active_ids = context.get('active_ids', [])
        failed_invoices = []
        for invoice in self.env['account.move'].sudo().browse(active_ids):
            try:
                invoice.check_line_description()
                invoice.send_to_bill_com()
            except Exception as e:
                failed_invoices.append((invoice.name, str(e)))
        if failed_invoices:
            error_message = "\n".join([f"{name}: {error}" for name, error in failed_invoices])
            raise ValidationError(f"Some invoices failed to send:\n{error_message}")



    # def bulk_send_bill_com_btn(self):
    #     context = self._context
    #     active_ids = context.get('active_ids')
    #     invoice_brw = self.env['account.move'].sudo().browse(active_ids)
    #     invoice_brw.check_line_description()
    #     invoice_brw.send_to_bill_com()