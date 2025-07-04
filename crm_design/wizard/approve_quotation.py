from odoo import api, fields, models, _
import base64

class ApproveQuotation(models.TransientModel):
	_name = 'approve.quotation.wizard'

	digital_signature = fields.Binary(string="Signature", required=True)

	def approve_quotation_invoice(self):
		if self._context.get('active_model') == 'account.move':
			record_id = self.env['account.move'].sudo().search([('id','=',self._context.get('current_id'))])
			base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
			base_url += record_id.get_portal_url()
			quotation_approval_group_id = self.env.ref('crm_design.group_manager_quotation').id
			quotation_manager_ids = self.env['res.users'].search([('groups_id','=',quotation_approval_group_id)])
			
			for rec in record_id:
				msg = 'Invoice Is Approved'
				manager_name = self.env.user.partner_id.name
				rec.state = 'approved'
				for manager in quotation_manager_ids:
					approval_id = self.env.ref('crm_design.mail_activity_data_approval')
					approval_id.sudo().name = "Approval"
					rec.activity_feedback(['crm_design.mail_activity_data_approval'], user_id=manager.id)
				msg = "Invoice Is Approved By %s" % (manager_name)

				rec.manager_signature = self.digital_signature
				rec.manager_name = manager_name
				rec.manager_signed_on = fields.Datetime.now()

				email_from = self.env['ir.mail_server'].sudo().search([],limit=1)
				mail_values_user_check = {
					'subject': msg,
					'email_to':rec.invoice_user_id.partner_id.email,
					'email_from':email_from.smtp_user,
					'body_html': '''<div> Dear %s ,<br/>
										  %s <br/>
										  Reference %s
									</div>'''%(rec.invoice_user_id.partner_id.name,msg,base_url)
					}
				create_and_send_email = self.env['mail.mail'].sudo().create(mail_values_user_check).sudo().send()
			
		if self._context.get('active_model') == 'sale.order':
			record_id = self.env['sale.order'].sudo().search([('id','=',self._context.get('current_id'))])
			quotation_approval_group_id = self.env.ref('crm_design.group_manager_quotation').id
			quotation_manager_ids = self.env['res.users'].search([('groups_id','=',quotation_approval_group_id)])
			
			for record in record_id:
				msg =''
				manager_name = self.env.user.partner_id.name
				for manager in quotation_manager_ids:
					approval_id = self.env.ref('crm_design.mail_activity_data_approval')
					approval_id.sudo().name = "Approval"
					record.activity_feedback(['crm_design.mail_activity_data_approval'], user_id=manager.id)

				if record.state == 'final_approve_pending':
					record.is_quotation_approved = True
					record.state = 'final_approved'
					for design in record.attachment_ids:
						design.is_approved = True
					msg = "Quaotation %s Is Approved By %s" % (record.name,manager_name)

				else:
					record.is_quotation_approved = True
					record.state = 'approved'
					for design in record.attachment_ids:
						design.is_approved = True
					msg = "Design Is Approved"

				# record.manager_info_ids.manager_signature = self.digital_signature
				# record.manager_info_ids.manager_name = manager_name
				# record.manager_info_ids.manager_signed_on = fields.Datetime.now()
				record.sudo().message_post(body="Quotation is Approved")

				data=[]
				for info in record_id.manager_info_ids:
					info.is_approved = False
				data.append((0,0, {
					'manager_signature':self.digital_signature,
					'manager_name' : manager_name,
					'manager_signed_on': fields.Datetime.now(),
					'state': 'approved',
					'is_approved': True
					}))
				record.write({'manager_info_ids':data})

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

		# if self._context.get('active_model') == 'purchase.order':
		# 	record_id = self.env['purchase.order'].sudo().search([('id','=',self._context.get('active_id'))])
			
		# 	record_id.button_confirm()

		# 	for record in record_id:
		# 		record.activity_feedback(['crm_design.mail_activity_data_approval'], user_id=record.manager_id.user_id.id)

		# 		record.state = 'approved'
		# 		msg = "Quotation Is Approved"

		# 		record.manager_signature = self.digital_signature
		# 		record.manager_name = self.env.user.partner_id.name
		# 		record.manager_signed_on = fields.Datetime.now()
		# 		record.sudo().message_post(body="Quotation is Approved")

		# 		base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
		# 		base_url += record_id.get_portal_url()
		# 		email_from = self.env['ir.mail_server'].sudo().search([],limit=1)
		# 		mail_values_user_check = {
		# 			'subject': msg,
		# 			'email_to':record.user_id.partner_id.email,
		# 			'email_from':email_from.smtp_user,
		# 			'body_html': '''<div> Dear %s , <br/>
		# 								  %s <br/>
		# 								  Reference %s <br/>
		# 							</div>'''%(record.user_id.partner_id.name,msg,base_url)

		# 			}
		# 		create_and_send_email = self.env['mail.mail'].sudo().create(mail_values_user_check).sudo().send()
