from odoo import api, fields, models, _
import base64

class ApproveQuotation(models.TransientModel):
	_name = 'approve.purchase.request.wizard'

	digital_signature = fields.Binary(string="Signature", required=True)

	def approve_purchase_request(self):

		record_id = self.env['purchase.request'].sudo().search([('id','=',self._context.get('active_id'))])
		
		for record in record_id:
			record.activity_feedback(['kitchen_purchase_request.mail_activity_data_department_manager_approval'], user_id=record.assigned_to.id)
			record.state = 'approved'
			msg = "Purchase Request Is Approved"
			
			record.manager_signature = self.digital_signature
			record.sudo().message_post(body="Your purchase Request Is Approved By Manager")
			record.sudo().message_post(body=msg)

			# purchase_user_group = self.env.ref('purchase.group_purchase_user', raise_if_not_found=False)

			# if purchase_user_group:
			# 	for user in purchase_user_group.users:
			# 		record.activity_schedule('kitchen_purchase_request.mail_activity_data_purchase_user_approval', user_id=user.id)
			

			purchase_department = self.env.ref('kitchen_purchase_request.purchase_department_PD')
			
			employee_ids = self.env['hr.employee'].sudo().search([('department_id','=',purchase_department.id)])
			for employee in employee_ids:
				for user in employee.user_id:
					record.activity_schedule('kitchen_purchase_request.mail_activity_data_purchase_user_approval', user_id=user.id)


class ApprovePurchaseQuotation(models.TransientModel):
	_name = 'approve.rfq.wizard'

	digital_signature = fields.Binary(string="Signature", required=True)

	def approve_rfq_quotation(self):
		record_id = self.env['purchase.order'].sudo().search([('id','=',self._context.get('active_id'))])
		

		for record in record_id:
			record.button_confirm()
			if record.purchase_request_id:
				record.purchase_request_id.sudo().message_post(body="Your Request is Accepted and Items Are Purchased.")
				record.purchase_request_id.state =  'done'
			record.activity_feedback(['kitchen_purchase_request.mail_activity_data_purchase_department_manager_approval'], user_id=record_id.manager_id.user_id.id)

			msg = "Quotation Is Confirmed"

			record.manager_signature = self.digital_signature
			record.manager_name = self.env.user.partner_id.name
			record.manager_signed_on = fields.Datetime.now()
			record.sudo().message_post(body="Quotation is Confirmed")

			base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
			base_url += record_id.get_portal_url()
			email_from = self.env['ir.mail_server'].sudo().search([],limit=1)
			mail_values_user_check = {
				'subject': msg,
				'email_to':record.user_id.partner_id.email,
				'email_from':email_from.smtp_user,
				'body_html': '''<div> Dear %s , <br/>
									  %s <br/>
									  Reference %s <br/>
								</div>'''%(record.user_id.partner_id.name,msg,base_url)

				}
			create_and_send_email = self.env['mail.mail'].sudo().create(mail_values_user_check).sudo().send()

			# Pass Attachment And Sale Order Ref To Delivery order
			for picking in record.picking_ids:
				picking.tag_job_sale_ref = record.sale_order_ref_id.id
				picking.remarks = record.remarks
				picking.attachment_ids = record.multi_attachments.ids