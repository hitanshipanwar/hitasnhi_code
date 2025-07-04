# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.http import content_disposition, Controller, request, route
from datetime import datetime, date, time, timedelta
from odoo.exceptions import UserError, ValidationError, AccessError
from lxml import etree

class AccountAnalyticLine(models.Model):
	_name = 'account.analytic.line'
	_inherit = ['account.analytic.line', 'mail.thread', 'mail.activity.mixin']

	# task_id = fields.Many2one(
	# 	'project.task',
	# 	'Task',
	# 	index='btree_not_null',
	# 	compute='_compute_task_id',
	# 	store=True,
	# 	readonly=False,
	# 	domain="[('company_id', '=', company_id), ('project_id.allow_timesheets', '=', True), ('project_id', '=', project_id), ('planned_date', '>=', from_date), ('planned_date', '<=', to_date)]"
	# )

	# from_date = fields.Date(string="Form Date")
	# to_date = fields.Date(string="To Date", default=date.today())
	estimated_time = fields.Float(string="Allocated Hours", compute="_compute_allocated_date_hrs")
	effective_hours = fields.Float(string="Total Hours Spent", compute="_compute_allocated_date_hrs")
	planned_date = fields.Date(string="Planned Date", compute="_compute_allocated_date_hrs")
	date_deadline = fields.Date(string="Date Deadline", compute="_compute_allocated_date_hrs")
	state = fields.Selection(
		selection=[
			('draft', 'Draft'),
			('approve', 'Approved'),
			('refuse', 'Refused'),
			('re_submit', 'Re-submitted')
		],
		string='Status',
		default='draft',
	)
	is_weekend = fields.Boolean(string="Is weekday")
	partner_id = fields.Many2one('res.partner', string="Client")
	client_name = fields.Char(string="Client Name")

	@api.depends('project_id', 'task_id')
	def _compute_allocated_date_hrs(self):
		for rec in self:
			if rec.project_id and rec.task_id:
				rec.estimated_time = rec.task_id.planned_hours
				rec.effective_hours = sum(rec.task_id.timesheet_ids.mapped('unit_amount'))
				rec.planned_date = rec.task_id.planned_date
				rec.date_deadline = rec.task_id.date_deadline
			else:
				rec.estimated_time = rec.project_id.allocated_hours
				rec.effective_hours = sum(rec.project_id.timesheet_ids.mapped('unit_amount'))
				rec.planned_date = rec.project_id.date_start
				rec.date_deadline = rec.project_id.date

	def action_approve(self):
		project_ids = self.env['project.project'].sudo().search([('user_id', '=', self.env.uid)])
		can_access_project = project_ids.mapped('name')
		
		for rec in self.filtered(lambda r: r.project_id.user_id.id == self.env.uid):
			rec.write({'state': 'approve'})
			rec.activity_update()
			self._approve_compensatory_leave(rec.employee_id)

		if not self.filtered(lambda r: r.project_id.user_id.id == self.env.uid):
			raise ValidationError(_("As you're not the project manager for the following projects, you're unable to approve their timesheets:\n\n %s") % (can_access_project))
			# raise ValidationError(_("As you're not the project manager for project '%s' you're unable to approve its timesheet. \n\nKindly approve the timesheets for projects :- \n\n %s \n\nFor which you are the project manager.") % (rec.project_id.name, can_access_project))

	def activity_update(self):
		analytic_lines = self.filtered(lambda r: r.state == 'approve')
		activity_ids = self.env['mail.activity'].search([('res_id', 'in', analytic_lines.ids), ('res_model', '=', self._name)])
		activity_ids.unlink()


	def action_re_submit(self):
		self.state = 're_submit'
		# self.activity_update()

	def action_set_as_draft(self):
		self.state = 'draft'
					
	def action_refuse(self):
		self.state = 'refuse'

	def approve_timesheet(self):
		# analytic_ids = self.env['account.analytic.line'].sudo().search([('date','=',date.today())])
		analytic_ids = self.env['account.analytic.line'].sudo().search([])
		project_ids = analytic_ids.sudo().mapped('project_id')
		for project in project_ids:
			timesheet_rec = analytic_ids.sudo().search([('project_id', '=', project.id)]) 
			# timesheet_rec = analytic_ids.sudo().search([('project_id', '=', project.id), ('date','=',date.today())]) 
			for rec in timesheet_rec:
				# if rec.state == 'draft':
				if rec.state not in ['approve', 'refuse']: 
					rec.sudo().activity_schedule('ionicx_hr_extend.mail_activity_timesheet_upload', user_id=project.user_id.id)


	def _approve_compensatory_leave(self, employee):
		"""
		Approve compensatory leave allocations for the given employee if applicable.
		"""
		# Fetch compensatory leave allocations in the draft state for the employee
		leave_allocations = self.env['hr.leave.allocation'].sudo().search([
			('employee_id', '=', employee.id),
			('state', '=', 'confirm'),
			('holiday_status_id.is_compensatory_leave', '=', True)
		])
		for leave in leave_allocations:
			leave.action_validate()  # Automatically approve the leave allocation
			print(f"Compensatory leave approved for {employee.name} on {leave.date_from}.")

	# @api.model
	# def create(self, vals):
	# 	print("================== crfeate calling")
	# 	record = super(AccountAnalyticLine, self).create(vals)
	# 	self._check_for_compensatory_leave(record)
	# 	return record

	@api.model
	def create(self, vals):
		# Get the timesheet date from the valuesi
		if 'name' in vals and vals['name'] == 'Time Off (1/1)':
			print("Skipping specific timesheet validation for:", vals['name'])
			pass
		else:
			timesheet_date = vals.get('date')
			if not timesheet_date:
				raise ValidationError("The timesheet date is required.")

			# Convert the date to a datetime object
			# timesheet_date = fields.Date.from_string(timesheet_date)
			# today = fields.Date.today()
			# now = datetime.now()
			timesheet_date_obj = fields.Date.from_string(timesheet_date)
			current_datetime = datetime.now()

			# Calculate the time difference
			timesheet_datetime = datetime.combine(timesheet_date_obj, datetime.min.time())
			time_difference = current_datetime - timesheet_datetime

			# Check if the time difference exceeds 48 hours

			# Check the ResConfigSettings for the "past_timesheet" setting
			config = self.env['res.config.settings'].sudo().get_values()
			past_timesheet_enabled = config.get('past_timesheet', False)
			# Validation logic
			if time_difference.total_seconds() > 48 * 3600:
			# if timesheet_date < today:
				# Allow creating past timesheets only if setting is enabled and current time is before 12 PM
				# if past_timesheet_enabled and now.hour >= 12:
				if past_timesheet_enabled:
					raise ValidationError(
						"Creating past timesheets is not allowed , Please Update Timesheet on Daily Basis."
					)

			# Create the record
			record = super(AccountAnalyticLine, self).create(vals)
			self._check_for_compensatory_leave(record)
			return record

	def _check_for_compensatory_leave(self, record):
		# Check if the date is a weekend
		date = fields.Date.from_string(record.date)
		if date.weekday() in (5, 6) and record.unit_amount >= 8:
			record.is_weekend = True
			self._allocate_compensatory_leave(record.employee_id, record.date)
		
		# Check if the date is a public holiday
		public_holidays = self.env['resource.calendar.leaves'].search([
			('date_from', '<=', record.date),
			('date_to', '>=', record.date)
		])
		if public_holidays and record.unit_amount >= 8:
			record.is_weekend = True
			self._allocate_compensatory_leave(record.employee_id, record.date)

	def _allocate_compensatory_leave(self, employee, date):
		leave_type = self.env['hr.leave.type'].search([('is_compensatory_leave', '=', True)], limit=1)
		if not leave_type:
			raise ValidationError("Leave type 'Compensatory Leave' not found. Please create it first.")
		
		date_from = date.replace(month=1, day=1)
		date_to = date.replace(month=12, day=31)


		res = self.env['hr.leave.allocation'].sudo().create({
			'name': 'Compensatory Leave for {}'.format(date),
			'employee_id': employee.id,
			'employee_ids': [(6, 0, [employee.id])],
			'employee_company_id': employee.company_id.id,
			'holiday_status_id': leave_type.id,
			'date_from': date_from,
			'date_to': date_to,
			'state': 'confirm'
		})
		return res


class HrLeaveType(models.Model):
	_inherit = 'hr.leave.type'

	is_compensatory_leave = fields.Boolean(string="Is Compensatory Leave")