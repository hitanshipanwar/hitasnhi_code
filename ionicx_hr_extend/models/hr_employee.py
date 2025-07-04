# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.http import content_disposition, Controller, request, route
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, date, time, timedelta

class HrEmployee(models.Model):
	_inherit = 'hr.employee'

	visa_attachment_id = fields.Many2many('ir.attachment', 'ir_attachment_visa_ref', 'visa_id', 'attachment_id', string="Visa Attchment")
	employee_complaint_ids = fields.One2many('hr.employee.complaint', 'employee_id', string="Employee Service Request")
	passport_expire = fields.Date('Passport Expire Date', groups="hr.group_hr_user", tracking=True)
	passport_attachment_id = fields.Many2many('ir.attachment', 'ir_attachment_passport_ref', 'passport_id', 'attachment_id', string="Passport Attchment")
	emirates_id = fields.Char(string="Emirates ID")
	emirates_expire = fields.Date('Emirates Expire Date', groups="hr.group_hr_user", tracking=True)
	emirates_attachment_id = fields.Many2many('ir.attachment', 'ir_attachment_emirates_ref', 'emirates_id', 'attachment_id', string="Emirates Attchment")
	insurance_id = fields.Char(string="Insurance ID")
	insurance_expire = fields.Date('Insurance Expire Date', groups="hr.group_hr_user", tracking=True)
	insurance_attachment_id = fields.Many2many('ir.attachment', 'ir_attachment_insurance_ref', 'insurance_id', 'attachment_id', string="Insurance Attchment")
	pcc_status = fields.Selection([('done', 'Done'), ('not_done', 'Not Done')], string="Police Clearance Certificate (PCC)")

	
	def send_expiration_reminder(self, employee, document_type, document_field, reminder_template, department_template):
	    # today_date = date(2023, 11, 12)
	    today_date = fields.Date.today()
	    hr_managers = self.env['hr.employee'].search([('user_id.groups_id', 'in', self.env.ref('hr.group_hr_manager').id)])

	    employees = [manager for manager in hr_managers if manager != employee]
	    from_date = fields.Date.from_string(getattr(employee, document_field))

	    if from_date:
	        starting_date = from_date - timedelta(days=60)
	        date_list = [starting_date + timedelta(days=i * 10) for i in range((from_date - starting_date).days // 10 + 1)]

	        if today_date in date_list:

	            if today_date.weekday() in [5, 6]:
	                days_until_monday = (7 - today_date.weekday()) % 7
	                next_working_day = today_date + timedelta(days=days_until_monday)
	                today_date = next_working_day
	            else:
	                today_date = today_date

	            cr_today_date = fields.Date.today()
	            if today_date == cr_today_date:
		            for user in employees:
		                mail_template = self.env.ref(department_template)
		                mail_template.sudo().send_mail(employee.id, force_send=True, email_values={'email_to': user.user_id.login})

		            if employee:
		                mail_template = self.env.ref(reminder_template)
		                mail_template.sudo().send_mail(employee.id, force_send=True, email_values={'email_to': employee.work_email})

	def check_id_expiration(self):
	    all_employees = self.env['hr.employee'].search([])

	    for employee in all_employees:
	        self.send_expiration_reminder(employee, "Visa", "visa_expire", 'ionicx_hr_extend.reminder_visa_expire_to_candidate', 'ionicx_hr_extend.reminder_visa_expire_to_department')
	        self.send_expiration_reminder(employee, "Passport", "passport_expire", 'ionicx_hr_extend.reminder_passport_expire_to_candidate', 'ionicx_hr_extend.reminder_passport_expire_to_department')
	        self.send_expiration_reminder(employee, "Emirates", "emirates_expire", 'ionicx_hr_extend.reminder_emirates_expire_to_candidate', 'ionicx_hr_extend.reminder_emirates_expire_to_department')
	        self.send_expiration_reminder(employee, "Insurance", "insurance_expire", 'ionicx_hr_extend.reminder_insurance_expire_to_candidate', 'ionicx_hr_extend.reminder_insurance_expire_to_department')


class HrEmployeePublic(models.Model):
	_inherit = 'hr.employee.public'

	employee_complaint_ids = fields.One2many('hr.employee.complaint', 'employee_id', string="Employee Service Request")
	visa_attachment_id = fields.Many2many('ir.attachment', 'ir_attachment_visa_ref', 'visa_id', 'attachment_id', string="Visa Attchment")
	passport_expire = fields.Date('Passport Expire Date', groups="hr.group_hr_user", tracking=True)
	passport_attachment_id = fields.Many2many('ir.attachment', 'ir_attachment_passport_ref', 'passport_id', 'attachment_id', string="Passport Attchment")
	emirates_id = fields.Char(string="Emirates ID")
	emirates_expire = fields.Date('Emirates Expire Date', groups="hr.group_hr_user", tracking=True)
	emirates_attachment_id = fields.Many2many('ir.attachment', 'ir_attachment_emirates_ref', 'emirates_id', 'attachment_id', string="Emirates Attchment")
	insurance_id = fields.Char(string="Insurance ID")
	insurance_expire = fields.Date('Insurance Expire Date', groups="hr.group_hr_user", tracking=True)
	insurance_attachment_id = fields.Many2many('ir.attachment', 'ir_attachment_insurance_ref', 'insurance_id', 'attachment_id', string="Insurance Attchment")
	pcc_status = fields.Selection([('done', 'Done'), ('not_done', 'Not Done')], string="Police Clearance Certificate (PCC)")
 

class HrComplaintType(models.Model):
	_name = 'hr.employee.complaint'
	_inherit = ['mail.thread', 'mail.activity.mixin', 'utm.mixin']
	_description = 'Service Request'

	@api.model
	def _check_is_user(self):
		is_user = False
		if self.env.user.has_group("hr_attendance.group_hr_attendance_kiosk") and not self.env.user.has_group("hr.group_hr_manager"):
			is_user = True
		return is_user

	active = fields.Boolean(string="Active", default=True)
	name = fields.Char(string="Request Name", size=200)
	is_current_login_user = fields.Boolean(string="Is User")
	employee_id = fields.Many2one('hr.employee', string="Employee", default=lambda self: self.env.user.employee_id.id, readonly=True)
	company_id = fields.Many2one('res.company', string="Company Id", related="employee_id.company_id")
	is_user = fields.Boolean(string="Is User", default=_check_is_user)
	complaint_type = fields.Many2one('hr.complaint.type', string="Request Type", required=True)
	approver_department = fields.Selection(
		selection=[
		('hr_department', 'HR Department'), 
		('team_department', 'IT Department'), 
		('ticketing_department', 'Ticketing Department'), 
		('recruitment_department', 'Recruitment Department'), 
		('finance_department', 'Finance Department')], 
		related="complaint_type.approver_department", string="Approved By", readonly=True)
	req_approver_id = fields.Many2one('res.users', string="Approver", readonly=True)
	date = fields.Datetime(string="Date", default=datetime.now())
	is_resolved_date = fields.Boolean(string="Is Resolved Date", compute="_compute_is_solved_date")
	resolved_date = fields.Datetime(string="Resolved Date", readonly=True)
	hours_spent = fields.Char(string="Hours Spent", compute="_compute_hours_spent")
	to_be_resolved_date = fields.Datetime(string="Resolved At", compute="_compute_to_be_resolved")
	is_request_deadline = fields.Boolean(string="Request Deadline", compute="_compute_is_request_deadline")
	issue = fields.Char(string="Description")
	has_effect_on_work_efficiency = fields.Boolean(string="Has Effect on Work Efficiency")
	has_financial_effect = fields.Boolean(string="Has Financial Effect")
	add_attachment_ids = fields.Many2many('ir.attachment','ir_attachment_service_ref','service_req_id','attachment_id', string="Add Attchment")
	state = fields.Selection(
		selection=[
			('cancel', "Cancel"),
			('draft', "Draft"),
			('send_request', "Service Request Sent"),
			('approve', "Approved"),
			('in_process', "In Process"),
			('pending', "Pending"),
			('resolved', "Resolved"),
			('rejected', "Rejected"),
		],
		string="Status",
		readonly=True, copy=False, index=True,
		default='draft',
		tracking=True)
	last_comment_date = fields.Datetime(string="Last comment Date")
	last_comment_by = fields.Many2one('res.users', string="Last Comment By")
	approver_department_label = fields.Char("Approved By (Label)", compute="_compute_approver_department_label")
	delay_req_reason = fields.Char(string="Req. Delay Reason")
	job_position = fields.Char(string="Job Position")
	work_ex = fields.Char(string="Work Experiance")

	@api.depends('approver_department')
	def _compute_approver_department_label(self):
		for record in self:
			if record.approver_department:
				department_labels = {
					'hr_department': 'HR Department',
					'team_department': 'IT Department',
					'ticketing_department': 'Ticketing Department',
					'recruitment_department': 'Recruitment Department',
					'finance_department': 'Finance Department'
				}
				record.approver_department_label = department_labels.get(record.approver_department, '')
			else:
				record.approver_department_label = ''

	@api.depends('resolved_date', 'date')
	def _compute_hours_spent(self):
		for record in self:
			if record.resolved_date and record.date:
				# resolved_date = datetime.strptime(record.resolved_date, '%Y-%m-%d %H:%M:%S')
				# date = datetime.strptime(record.date, '%Y-%m-%d %H:%M:%S')
				duration = record.resolved_date - record.date
				hours_spent = duration.total_seconds() / 3600

				if hours_spent >= 24:
					days = int(hours_spent / 24)
					hours = int(hours_spent % 24)
					if hours > 0:
						record.hours_spent = f'{days} days {hours} hrs'
					else:
						record.hours_spent = f'{days} days'
				else:
					record.hours_spent = f'{int(hours_spent)} hrs'
			else:
				record.hours_spent = '0 hrs'


	def check_service_requests(self):
		# Get the day of the week (0 = Monday, 6 = Sunday)
		day_no = datetime.today().weekday()
		
		# Get the current date
		current_date = datetime.now().date()
		
		# Calculate the start date of the current month
		start_date = datetime(current_date.year, current_date.month, 1).date()
		
		# Calculate the number of days in the current month
		day_count = (current_date - start_date).days + 1

		if day_no < 5:  # Assuming Monday to Friday are working days
			# Get all service requests
			all_requests = self.search([])

			for request in all_requests:
				if not request.resolved_date:
					# Get all users
					all_users = self.env['res.users'].search([])

					# Convert the 'to_be_resolved_date' to a string in 'YYYY-MM-DD' format
					res_date = request.to_be_resolved_date.date().strftime('%Y-%m-%d')
					
					# Get the current date as a string in 'YYYY-MM-DD' format
					today_date = datetime.now().strftime('%Y-%m-%d')
					
					date_list = []
					one_day = timedelta(days=1)
					current_date = datetime.strptime(res_date, '%Y-%m-%d')
					
					while current_date <= datetime.strptime(today_date, '%Y-%m-%d'):
						date_list.append(current_date)
						current_date += one_day

					for date in date_list:
						for group, department in [
							('ionicx_hr_extend.hr_department', 'hr_department'),
							('ionicx_hr_extend.it_department', 'team_department'),
							('ionicx_hr_extend.ticketing_department', 'ticketing_department'),
							('ionicx_hr_extend.recruitment_department', 'recruitment_department'),
							('ionicx_hr_extend.finance_department', 'finance_department')
						]:
							if request.approver_department == department and res_date == date.strftime('%Y-%m-%d'):
								# Get users belonging to the specific department group
								department_users = [user for user in all_users if user.has_group(group)]
								for approver in department_users:
									mail_template = self.env.ref('ionicx_hr_extend.service_request_email_template')
									mail_template.sudo().send_mail(request.id, force_send=True, email_values={'email_to': approver.email})



	def _compute_to_be_resolved(self):
		for rec in self:
			if rec.date:
				rec.to_be_resolved_date = rec.date + timedelta(hours=24)
			else:
				rec.to_be_resolved_date = False

	def _compute_is_request_deadline(self):
		for record in self:
			if record.resolved_date:
				if record.resolved_date < record.to_be_resolved_date:
					record.is_request_deadline = True
				else:
					record.is_request_deadline = False
			else:
					record.is_request_deadline = False


	def _fix_attachment_ownership(self):
		for record in self:
			record.add_attachment_ids.write({'res_model': record._name, 'res_id': record.id})
			return self

	@api.model_create_multi
	def create(self, vals_list):
		return super().create(vals_list)._fix_attachment_ownership()


	def _compute_is_solved_date(self):
		if self.env.user.has_group('ionicx_hr_extend.complaint_master_manager'):
			self.is_resolved_date = True
		else:
			self.is_resolved_date = False

	def action_send_request(self):
		for record in self:
			if self.env.user == record.employee_id.user_id:
				record.is_current_login_user = True
			all_user = self.env['res.users'].search([])
			if self.approver_department == 'hr_department':
				hr_approver = [user for user in all_user if user.has_group('ionicx_hr_extend.hr_department')]
				for approver in hr_approver:
					self.activity_schedule('ionicx_hr_extend.mail_activity_complaint_upload', user_id=approver.id)
			elif self.approver_department == 'team_department':
				hr_approver = [user for user in all_user if user.has_group('ionicx_hr_extend.it_department')]
				for approver in hr_approver:
					self.activity_schedule('ionicx_hr_extend.mail_activity_complaint_upload', user_id=approver.id)
			elif self.approver_department == 'ticketing_department':
				hr_approver = [user for user in all_user if user.has_group('ionicx_hr_extend.ticketing_department')]
				for approver in hr_approver:
					self.activity_schedule('ionicx_hr_extend.mail_activity_complaint_upload', user_id=approver.id)
			elif self.approver_department == 'finance_department':
				hr_approver = [user for user in all_user if user.has_group('ionicx_hr_extend.finance_department')]
				for approver in hr_approver:
					self.activity_schedule('ionicx_hr_extend.mail_activity_complaint_upload', user_id=approver.id)
			elif self.approver_department == 'recruitment_department':
				hr_approver = [user for user in all_user if user.has_group('ionicx_hr_extend.recruitment_department')]
				for approver in hr_approver:
					self.activity_schedule('ionicx_hr_extend.mail_activity_complaint_upload', user_id=approver.id)
			else:
				raise UserError(_('Kindly select the Approver !'))
			record.state = 'send_request'

	def _get_service_request_model_view(self):
		res_model = "hr.employee.complaint"
		view = "ionicx_hr_extend.view_hr_employee_complaint_form_approval"
		view_id = self.env.ref(view).id
		return res_model, view_id

	def action_cancel(self):
		for rec in self:
			rec.state = 'cancel'
			rec.req_approver_id = self.env.user.id
			rec.last_comment_date = datetime.now()
			rec.last_comment_by = self.env.user

	
	def activity_update(self):
		# Get analytic line 
		def get_analytic_line(self,record):
			line = self.env[str(record.res_model)].search([('id','=',int(record.res_id))])
			return line
		analytic_ids = self.search([])
		activity_ids = self.env['mail.activity'].search([('res_id','in',analytic_ids.ids),('res_model','=',self._name)])
		for record in activity_ids:
			if record.res_model and record.res_id:
				analytic_line = get_analytic_line(self,record)
				if analytic_line.state == 'resolved':
					record.unlink()
				if analytic_line.state == 'pending':
					record.unlink()
				if analytic_line.state == 'rejected':
					record.unlink()
				if analytic_line.state == 'approve':
					record.unlink()

	def action_approve(self):
		for rec in self:
			rec.resolved_date = datetime.now()
			rec.req_approver_id = self.env.user.id
			rec.state = 'approve'
			rec.last_comment_date = datetime.now()
			rec.last_comment_by = self.env.user
			rec.activity_update()
			res_model, view_id = rec._get_service_request_model_view()
			return {
				"name": _("Service Request"),
				"res_model": res_model,
				"view_mode": "form",
				"view_id": view_id,
				"res_id": rec.id,
				"type": "ir.actions.act_window",
			}

	def action_inprocess(self):
		for rec in self:
			rec.state = 'in_process'

	def action_resolve(self):
		for rec in self:
			rec.resolved_date = datetime.now()
			rec.req_approver_id = self.env.user.id
			rec.state = 'resolved'
			rec.last_comment_date = datetime.now()
			rec.last_comment_by = self.env.user
			rec.activity_update()
			res_model, view_id = rec._get_service_request_model_view()
			return {
				"name": _("Service Request"),
				"res_model": res_model,
				"view_mode": "form",
				"view_id": view_id,
				"res_id": rec.id,
				"type": "ir.actions.act_window",
			}

	def action_pending(self):
		for rec in self:
			rec.state = 'pending'
			rec.req_approver_id = self.env.user.id
			rec.last_comment_date = datetime.now()
			rec.last_comment_by = self.env.user
			rec.activity_update()
			res_model, view_id = rec._get_service_request_model_view()
			return {
				"name": _("Service Request"),
				"res_model": res_model,
				"view_mode": "form",
				"view_id": view_id,
				"res_id": rec.id,
				"type": "ir.actions.act_window",
			}


	def action_rejected(self):
		for rec in self:
			rec.state = 'rejected'
			rec.req_approver_id = self.env.user.id
			rec.last_comment_date = datetime.now()
			rec.last_comment_by = self.env.user
			rec.activity_update()
			res_model, view_id = rec._get_service_request_model_view()
			return {
				"name": _("Service Request"),
				"res_model": res_model,
				"view_mode": "form",
				"view_id": view_id,
				"res_id": rec.id,
				"type": "ir.actions.act_window",
			}
	 

	def action_draft(self):
		for rec in self:
			rec.req_approver_id = self.env.user.id
			rec.last_comment_date = datetime.now()
			rec.last_comment_by = self.env.user
			rec.state = 'draft'

class HrComplaintType(models.Model):
	_name = 'hr.complaint.type'
	_description = 'hr.complaint.type'

	name = fields.Char(string="Name")
	approver_department = fields.Selection(selection=[('hr_department', 'HR Department'), ('team_department', 'IT Department'), ('ticketing_department', 'Ticketing Department'), ('finance_department', 'Finance Department'), ('recruitment_department', 'Recruitment Department')], default="hr_department", string="Approved By")


class ServiceRequestWizard(models.TransientModel):
	_name = 'service.request.wizard'
	_description = 'Service Request Wizard'

	employee_ids = fields.Many2many('hr.employee', 'rel_service_req', 'request_id', 'employee_id', string="Employee")
	from_date = fields.Datetime(string="Form Date", required=True)
	to_date = fields.Datetime(string="To Date", required=True)

	def print_pdf_report(self):
		domain = [
			('employee_id', 'in', self.employee_ids.ids),
			('date', '>=', self.from_date),
			('date', '<=', self.to_date),
		]

		date_domain = [
			('date', '>=', self.from_date),
			('date', '<=', self.to_date),
		]
		if self.employee_ids:
			name = self.env['hr.employee.complaint'].search(domain)
		else:
			name = self.env['hr.employee.complaint'].search(date_domain)

		return self.env.ref('ionicx_hr_extend.action_service_request_report').report_action(name)

