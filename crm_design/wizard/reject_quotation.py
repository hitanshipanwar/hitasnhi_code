from odoo import api, fields, models, _
import datetime
from datetime import datetime, timedelta, time
from odoo.exceptions import AccessError, MissingError, ValidationError,UserError

class RejectQuotation(models.TransientModel):
	_name = 'reject.quotation.wizard'

	note = fields.Html("Rejection Note", help="Add a note about this Quotation")
	digital_signature = fields.Binary(string="Signature", required=True)

	def reject_quotation_invoice(self):
		if self._context.get('active_model') == 'account.move':
			record_id = self.env['account.move'].sudo().search([('id','=',self._context.get('current_id'))])
			record_id.sudo().message_post(body=self.note)
			for rec in record_id:
				rec.state = 'draft'
				msg = "Invoice Is Rejected"
				manager_name = self.env.user.partner_id.name
				quotation_approval_group_id = self.env.ref('crm_design.group_manager_quotation').id
				quotation_manager_ids = self.env['res.users'].search([('groups_id','=',quotation_approval_group_id)])
				base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
				base_url += rec.get_portal_url()
				
				for manager in quotation_manager_ids:
					approval_id = self.env.ref('crm_design.mail_activity_data_approval')
					approval_id.sudo().name = "Rejection"
					rec.activity_feedback(['crm_design.mail_activity_data_approval'], user_id=manager.id)
					msg = "Invoice Is Rejected By %s" % (manager_name)

				rec.manager_signature = self.digital_signature
				rec.manager_name = manager_name
				rec.manager_signed_on = fields.Datetime.now()

				email_from = self.env['ir.mail_server'].sudo().search([],limit=1)
				mail_values_user_check = {
					'subject': msg,
					'email_to':rec.invoice_user_id.partner_id.email,
					'email_from':email_from.smtp_user,
					'body_html': '''<div> Dear %s, <br/>
										  %s <br/>Reference %s
									</div>'''%(rec.invoice_user_id.partner_id.name,msg,base_url)

					}
				create_and_send_email = self.env['mail.mail'].sudo().create(mail_values_user_check).sudo().send()
		
		if self._context.get('active_model') == 'sale.order':
			record_id = self.env['sale.order'].sudo().search([('id','=',self._context.get('current_id'))])
			record_id.sudo().message_post(body=self.note)
			quotation_approval_group_id = self.env.ref('crm_design.group_manager_quotation').id
			quotation_manager_ids = self.env['res.users'].search([('groups_id','=',quotation_approval_group_id)])
			manager_name = self.env.user.partner_id.name
			for manager in quotation_manager_ids:
				approval_id = self.env.ref('crm_design.mail_activity_data_approval')
				approval_id.sudo().name = "Rejection"
				record_id.activity_feedback(['crm_design.mail_activity_data_approval'], user_id=manager.id)
				

			# record_id.manager_signature = self.digital_signature
			# record_id.manager_name = manager_name
			# record_id.manager_signed_on = fields.Datetime.now()

			data=[]
			data.append((0,0, {
				'manager_signature':self.digital_signature,
				'manager_name' : manager_name,
				'manager_signed_on': fields.Datetime.now(),
				'state': 'rejected',
				}))
			record_id.write({'manager_info_ids':data})
			
			if record_id.appoinment_to_visit:
				record_id.state = 'site_visited'
			else:
				record_id.state = 'draft'
				record_id.is_quotation_approved = True

			base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
			base_url += record_id.get_portal_url()
			email_from = self.env['ir.mail_server'].sudo().search([],limit=1)
			msg = "Quotation %s Is Rejected By %s" % (record_id.name,manager_name)
			mail_values_user_check = {
				'subject': msg,
				'email_to':record_id.user_id.partner_id.email,
				'email_from':email_from.smtp_user,
				'body_html': '''<div> Dear, %s %s <br/>Reference %s
								</div>'''%(record_id.user_id.partner_id.name,msg,base_url)

				}
			create_and_send_email = self.env['mail.mail'].sudo().create(mail_values_user_check).sudo().send()


		# if self._context.get('active_model') == 'purchase.order':
		# 	record_id = self.env['purchase.order'].sudo().search([('id','=',self._context.get('active_id'))])
		# 	record_id.sudo().message_post(body=self.note)
		# 	record_id.activity_feedback(['crm_design.mail_activity_data_approval'], user_id=record_id.manager_id.user_id.id)
		# 	record_id.manager_signature = self.digital_signature
		# 	record_id.manager_name = self.env.user.partner_id.name
		# 	record_id.manager_signed_on = fields.Datetime.now()
		# 	record_id.state = 'draft'

		# 	base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
		# 	base_url += record_id.get_portal_url()
		# 	email_from = self.env['ir.mail_server'].sudo().search([],limit=1)
		# 	msg = "Quotation %s Is Rejected By %s" % (record_id.name,self.env.user.partner_id.name)
		# 	mail_values_user_check = {
		# 		'subject': msg,
		# 		'email_to':record_id.user_id.partner_id.email,
		# 		'email_from':email_from.smtp_user,
		# 		'body_html': '''<div> Dear, %s %s <br/>Reference %s
		# 						</div>'''%(record_id.user_id.partner_id.name,msg,base_url)

		# 		}
		# 	create_and_send_email = self.env['mail.mail'].sudo().create(mail_values_user_check).sudo().send()

