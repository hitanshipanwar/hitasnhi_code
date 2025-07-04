from odoo import fields, models


class IrAttachment(models.Model):
    _inherit = 'ir.attachment'

    is_sent_on_bill_com = fields.Boolean(string="Sent on Bill.com?", default=False, copy=False)
    bill_com_document_upload_id = fields.Char(string="Bill.com Upload ID?", copy=False)

    # def _attachment_format(self, legacy=False):
    def _attachment_format(self):
        res_list = super(IrAttachment, self)._attachment_format()
        for index, result in enumerate(res_list):
            attachment = self.browse(result['id'])
            res_list[index]['is_sent_on_bill_com'] = attachment.is_sent_on_bill_com
            if attachment.res_model == 'account.move' and attachment.res_id:
                related_account_move = self.env['account.move'].browse(attachment.res_id)
                res_list[index]['account_move_bill_id'] = related_account_move.bill_com_bill_id
        return res_list