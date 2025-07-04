from odoo import api, fields, models, _

class RejectPurchaseRequest(models.TransientModel):
	_name = 'reject.purchase.request.wizard'

	note = fields.Text("Rejection Note")
	digital_signature = fields.Binary(string="Signature", required=True)

	def reject_purchase_request(self):
		if self._context.get('active_model') == 'purchase.request':
			record_id = self.env['purchase.request'].sudo().search([('id','=',self._context.get('active_id'))])

			record_id.sudo().message_post(body=self.note)
			record_id.sudo().message_post(body="Your Request Is Rejected")
			for rec in record_id:
				rec.state = 'rejected'
				rec.manager_signature = self.digital_signature
				rec.activity_feedback(['kitchen_purchase_request.mail_activity_data_department_manager_approval'], user_id=rec.assigned_to.id)
				
class RejectRFQQuotation(models.TransientModel):
	_name = 'reject.rfq.wizard'

	note = fields.Html("Rejection Note", help="Add a note about this Quotation")
	digital_signature = fields.Binary(string="Signature", required=True)


	def reject_rfq_quotation(self):
		record_id = self.env['purchase.order'].sudo().search([('id','=',self._context.get('active_id'))])
		record_id.sudo().message_post(body=self.note)
		record_id.activity_feedback(['kitchen_purchase_request.mail_activity_data_purchase_department_manager_approval'], user_id=record_id.manager_id.user_id.id)
		record_id.manager_signature = self.digital_signature
		record_id.manager_name = self.env.user.partner_id.name
		record_id.manager_signed_on = fields.Datetime.now()
		record_id.state = 'draft'

		base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
		base_url += record_id.get_portal_url()
		email_from = self.env['ir.mail_server'].sudo().search([],limit=1)
		msg = "Quotation %s Is Rejected By %s" % (record_id.name,self.env.user.partner_id.name)
		mail_values_user_check = {
			'subject': msg,
			'email_to':record_id.user_id.partner_id.email,
			'email_from':email_from.smtp_user,
			'body_html': '''<div> Dear, %s %s <br/>Reference %s
							</div>'''%(record_id.user_id.partner_id.name,msg,base_url)

			}
		create_and_send_email = self.env['mail.mail'].sudo().create(mail_values_user_check).sudo().send()

