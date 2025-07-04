from odoo import api, fields, models, _
import datetime
from datetime import datetime, timedelta, time
from odoo.exceptions import AccessError, MissingError, ValidationError,UserError

class AppointmentDesignAttachment(models.Model):
	_inherit = 'ir.attachment'
 
	appointment_order_ref_id = fields.Many2one('appointment.visit')
	appointment_ref_id = fields.Many2one("appointment.visit", string="Attachments")


class Appointment(models.Model):
	_name = 'appointment.visit'
	_inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin', 'utm.mixin']
	_rec_name = 'visitor_id'
	_description = "Appointment To Visit"

	# name = fields.Char(string="Title")
	appointment_date = fields.Datetime(string="Appointment Date")
	customer_id = fields.Many2one('res.partner',string="Customer")
	visitor_id = fields.Many2one('res.users',string="Visitor", domain=[('share','=',False)])
	visit_charge = fields.Float(string="Visit Charge")
	is_tax_included = fields.Boolean(string="Tax Included")
	appointment_state = fields.Selection(string="Appointment State",
		selection=[('draft','To Submit'),
		('confirm','To Approve'),
		('validate','Approved'),
		('reject','Rejected')],default='draft')
	my_order_id = fields.Integer()
	calendar_event_manager_id = fields.Integer()
	calendar_event_employee_id = fields.Integer()
	is_visitor_login = fields.Boolean(compute='_compute_is_visitor')
	appointment_invoice_id = fields.Many2one('account.move')
	is_manager_login = fields.Boolean(compute='_compute_is_manager')
	multi_attachments = fields.Many2many('ir.attachment','ir_attachment_upload_ref','sale_id','attachment_id',string="Multiple Attchment")
	multi_attachments_ids = fields.One2many("ir.attachment","appointment_ref_id", string="Attachments")
	notes = fields.Html('Notes')
	attachment_ids = fields.One2many('ir.attachment','appointment_order_ref_id', compute='_compute_appointment_design')

	def _compute_appointment_design(self):
		self.attachment_ids = False
		if self.my_order_id:
			order_id = self.env['sale.order'].browse(self.my_order_id)
			self.attachment_ids = order_id.attachment_ids.ids

	def write(self,vals):
		res = super(Appointment, self).write(vals)
		# if vals.get('multi_attachments'):
		# 	ir_attachment_obj = self.env['ir.attachment']
		# 	if not self._context.get('no_update'):
		# 		for record in self:
		# 			order_id = self.env['sale.order'].browse(record.my_order_id)
		# 			order_id.write({'multi_attachments':[(5,0,0)]})
		# 			for att in record.multi_attachments:
		# 				order_id.write({'multi_attachments':[(0,0,{
		# 					'name': att.name,
		# 					'type': 'binary',
		# 					'datas': att.datas,
		# 					'res_model': 'sale.order',
		# 					'res_id': record.my_order_id
		# 				})]})

		if vals.get('visitor_id') and self.appointment_state == "confirm":
			for record in self:
				order_id = self.env['sale.order'].browse(record.my_order_id)
				order_id.sudo().message_post(body="Visitor Changed to <strong>%s</strong>"%(record.visitor_id.name))

		if vals.get('multi_attachments_ids'):
			ir_attachment_obj = self.env['ir.attachment']
			if not self._context.get('no_update'):
				for record in self:
					order_id = self.env['sale.order'].browse(record.my_order_id)
					order_id.write({'multi_attachments_ids':[(5,0,0)]})
					for att in record.multi_attachments_ids:
						order_id.write({'multi_attachments_ids':[(0,0,{
							'name': att.name,
							'type': 'binary',
							'datas': att.datas,
							'res_model': 'sale.order',
							'res_id': record.my_order_id
						})]})

		if vals.get('notes'):
			for record in self:
				order_id = self.env['sale.order'].browse(record.my_order_id)
				order_id.write({'visiter_notes': self.notes})

		return res

	@api.onchange('visitor_id')
	def _onchage_visitor_scheduler_updated(self):
		calendar_event_employee_id = self.env['mail.activity'].sudo().search([('id','=',int(self.calendar_event_employee_id))])
		record_id = self.env['sale.order'].sudo().search([('id','=',self.my_order_id)])
		for record in self:
			if record.is_manager_login and record.calendar_event_employee_id:
				calendar_event_employee_id.write({'user_id':record.visitor_id.id})
				record_id.visitor_id = record.visitor_id.id

	@api.onchange('appointment_date')
	def _onchange_date_set_appointment_date(self):
		record_id = self.env['sale.order'].sudo().search([('id','=',self.my_order_id)])
		for record in self:
			if record.is_manager_login or record.is_visitor_login:
				record_id.appointment_date = record.appointment_date


	@api.model
	def _compute_is_manager(self):
		schedule_approval_group_id = self.env.ref('crm_design.group_manager_schedular').id
		schedule_manager_ids = self.env['res.users'].search([('groups_id','=',schedule_approval_group_id)])
		for record in self:
			if self.env.uid in schedule_manager_ids.ids:
				record.is_manager_login = True
			else:
				record.is_manager_login = False

	@api.model
	def _compute_is_visitor(self):
		for record in self:
			if self.env.uid == record.visitor_id.id:
				record.is_visitor_login = True
			else:
				record.is_visitor_login = False

	def create_appointment(self):
		self.my_order_id = self._context.get('my_order_id')
		record_id = self.env['sale.order'].search([('id','=',self._context.get('my_order_id'))])
		record_id.appointment_date = self.appointment_date
		record_id.visitor_id = self.visitor_id.id
		
		if self.is_tax_included:
			tax_id = self.env.ref('crm_design.design_tax_ids_included_price')
		else:
			tax_id = self.env.ref('crm_design.design_tax_ids')
		
		site_visit_product_id = self.env['product.product'].search([('is_site_visit_product','=',True)])
		record_id.write({'order_line':[(0, 0, {
				'product_id': site_visit_product_id.id,
				'product_uom_qty': 1,
				'price_unit': self.visit_charge,
				'tax_id':[(6,0,tax_id.ids)],
				'name': site_visit_product_id.description_sale,
			})]})

		record_id.action_confirm()
		invoice_id = self.env['account.move'].sudo().create(record_id._prepare_invoice())
		lines = record_id.order_line.filtered(lambda l: l.product_id.is_site_visit_product == True)
		invoice_line_vals = []
		for line in lines:
			invoice_line_vals.append(
						(0, 0, line._prepare_invoice_line()),
					)
		invoice_id.write({'invoice_line_ids':invoice_line_vals,
							'is_thai': record_id.is_thai})
		# invoice_id.write({'invoice_line_ids':[(0,0,{
  #           'product_id': site_visit_product_id.id,
  #           'price_unit': self.visit_charge,
		# 	})]})
		record_id.invoice_ids:invoice_id
		invoice_id.is_visit_invoice = True
		invoice_id.visitor_id = self.visitor_id.id
		invoice_id.appointment_id = self.id
		invoice_id.appointment_access_link = self.env['mail.thread']._notify_get_action_link('view', model='appointment.visit', res_id=self.id),

		record_id.visit_charge = invoice_id.amount_total_in_currency_signed		
		record_id.state = 'site_visit'
		self.appointment_invoice_id = invoice_id.id

		schedule_approval_group_id = self.env.ref('crm_design.group_manager_schedular').id
		schedule_manager_ids = self.env['res.users'].search([('groups_id','=',schedule_approval_group_id)])
		
		for manager in self.visitor_id:
			email_from = self.env['ir.mail_server'].sudo().search([],limit=1)
			base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
			base_url += self.get_portal_url()
			mail_values_user_check = {
					'subject': 'Appointment For Visit' ,
					'email_to':manager.partner_id.email,
					# 'email_cc':manager.partner_id.email,
					'email_from':email_from.smtp_user,
					'body_html': '''<div> Dear <strong> %s </strong> <br/>
									My name is %s and I am contacting you on behalf of %s.<br/>
									I appreciate if we can meet at %s to talk about Design.
									<br/><br/>
									Thank you for your consideration and your time. I am looking forward to meet you.
									<br/> Best Regards
									</div> <br/>
									<strong>Reference : </strong>%s'''
									% (self.visitor_id.name,self.env.user.name,self.env.company.name,self.appointment_date,base_url)
				}
			create_and_send_email = self.env['mail.mail'].sudo().create(mail_values_user_check).sudo().send()

		self.appointment_state = 'confirm'

		shedule_approval_group_id = self.env.ref('crm_design.group_manager_schedular').id
		manager_ids = self.env['res.users'].search([('groups_id','=',shedule_approval_group_id)])

		for manager in manager_ids:
			self.activity_schedule(
						'crm_design.mail_activity_data_approval_appointmnet',
						user_id=manager.id)
		
		calendar_event_employee = self.activity_schedule(
						'crm_design.mail_activity_data_approval_appointmnet',
						user_id=self.visitor_id.id)

		self.calendar_event_employee_id = calendar_event_employee.id

	def action_approve_appointment(self):
		record_id = self.env['sale.order'].sudo().search([('id','=',int(self.my_order_id))])

		if self.appointment_invoice_id.payment_state == 'paid':
			record_id.state = 'site_visited'
			record_id.appointment_date = self.appointment_date
			record_id.visitor_id = self.visitor_id.id
			self.appointment_state = 'validate'
		else:
			raise UserError(_('First Pay Appointment Charges'))

		for design in record_id.attachment_ids:
			if design.approve_state == 'approve':
				design.approve_state = 'pre_approved'

		base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
		base_url += record_id.get_portal_url()
		email_from = self.env['ir.mail_server'].sudo().search([],limit=1)
		mail_values_user_check = {
			'subject': "Appointment Approved By %s" % (self.visitor_id.partner_id.name),
			'email_to':record_id.user_id.partner_id.email,
			'email_from':email_from.smtp_user,
			'body_html': '''<div> Dear, %s  <br/>
							Appointment is Approved by %s <br/>
							Reference %s
							</div>'''%(record_id.user_id.partner_id.name,self.visitor_id.partner_id.name,base_url)

			}
		create_and_send_email = self.env['mail.mail'].sudo().create(mail_values_user_check).sudo().send()

		shedule_approval_group_id = self.env.ref('crm_design.group_manager_schedular').id
		manager_ids = self.env['res.users'].search([('groups_id','=',shedule_approval_group_id)])

		for manager in manager_ids:
			self.activity_feedback(['crm_design.mail_activity_data_approval_appointmnet'], user_id=manager.id)
		self.activity_feedback(['crm_design.mail_activity_data_approval_appointmnet'], user_id=self.visitor_id.id)
	
	def action_reject_appointment(self):
		record_id = self.env['sale.order'].sudo().search([('id','=',int(self.my_order_id))])
		return {
				'name': "Reject Appointment Visit",
				'type': 'ir.actions.act_window',
				'view_type': 'form',
				'view_mode': 'form',
				'res_model': 'appointment.visit.reject',
				'context': {'sale_order_id': self.my_order_id, 'appointment_id': self.id},
				'view_id': self.env.ref('crm_design.appointment_visit_reject_view_form').id,
				'target': 'new'
		}

		# return result
		
	@api.returns('mail.message', lambda value: value.id)
	def message_post(self, *, message_type='notification', **kwargs):
		self.ensure_one()
		result = super(Appointment, self).message_post(message_type=message_type, **kwargs)
		record_id = self.env['sale.order'].sudo().search([('id','=',int(self.my_order_id))])
		if record_id:
			record_id.message_post(body=result.body)
		return result

class AppointmentVisitReject(models.TransientModel):
	_name = "appointment.visit.reject"
	_description = "Appointment Visit Reject"

	notes = fields.Html('Notes', requered=True)

	def action_appointment_visit_reject(self):
		if self._context.get('sale_order_id'):
			record_id = self.env['sale.order'].sudo().search([('id','=',self._context.get('sale_order_id'))])
			record_id.message_post(body="Visitor Rejected Appointment")

			visit_id =  self.env['appointment.visit'].sudo().search([('id','=',self._context.get('active_id'))])
			visit_id.message_post(body=self.notes)

			visit_id.appointment_state = 'reject'
			
			self.env['account.move'].browse(visit_id.appointment_invoice_id.id).unlink()

			visit_id.activity_schedule('crm_design.mail_activity_data_approval_appointmnet',
						user_id=record_id.user_id.id)

			shedule_approval_group_id = self.env.ref('crm_design.group_manager_schedular').id
			manager_ids = self.env['res.users'].search([('groups_id','=',shedule_approval_group_id)])

		for manager in manager_ids:
			visit_id.activity_feedback(['crm_design.mail_activity_data_approval_appointmnet'], user_id=manager.id)
		visit_id.activity_feedback(['crm_design.mail_activity_data_approval_appointmnet'], user_id=visit_id.visitor_id.id)
		
