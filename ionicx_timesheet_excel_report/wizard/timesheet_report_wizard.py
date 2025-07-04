# -*- coding: utf-8 -*-
import base64
import os
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta
from io import BytesIO
import xlsxwriter
from odoo import fields, models, api, _
from odoo.tools import config
from xlsxwriter.utility import xl_rowcol_to_cell
import calendar
from odoo.exceptions import UserError, ValidationError

class TimesheetReportWizard(models.TransientModel):
	_name = 'timesheet.report.wizard'
	_description = 'Timesheet Report Wizard'

	type = fields.Selection([('employee','Employee'),('project','Project')],default='employee',string='Type')
	start_date = fields.Date('From Date')
	end_date = fields.Date('To Date')
	employee_ids = fields.Many2many('hr.employee', string="Employees")
	project_ids = fields.Many2many('project.project', string="Project")
	file = fields.Binary('File')

	@api.constrains('end_date')
	def _check_end_date(self):
		for record in self:
			if self.end_date < self.start_date:
				raise ValidationError('The end date cannot be earlier than the start date !')

	def print_xlsx_report(self):
		file_name = _('Timesheet Report.xlsx')
		fp = BytesIO()

		workbook = xlsxwriter.Workbook(os.path.join(config['data_dir'], 'Timesheet Report'))
		header_text_format = workbook.add_format({'font_size': 12, 'align':'center','bold':True,'valign':'vcenter','bg_color':'#d0cece'})
		header_text_format_2 = workbook.add_format({'font_size': 13, 'align':'center','bold':True,'valign':'vcenter','bg_color':'#ff0000'})
		header_text_format_3 = workbook.add_format({'font_size': 13, 'align':'center','bold':True,'valign':'vcenter'})
		value_format = workbook.add_format({'font_size': 10, 'align':'left','valign':'vcenter'})
		number_value_format = workbook.add_format({'font_size': 10, 'align':'right', 'valign':'vcenter','num_format': '#,###0.00'})
		number_value_format_2 = workbook.add_format({'font_size': 12, 'align':'right', 'valign':'vcenter','bold':True,'num_format': '#,###0.00'})
		
		worksheet = workbook.add_worksheet('Timesheet Report')

		worksheet.set_column('A:A', 24)
		worksheet.set_column('B:E', 22)

		# set rows height
		worksheet.set_row(0,30)
		num_days = (self.end_date - self.start_date).days
		date_list = []
		for day in range(num_days + 1):
			current_date = self.start_date + timedelta(days=day)
			date_list.append(current_date)

		work_day_count = 0 
		day_count = (self.end_date - self.start_date).days + 1
		for single_date in [d for d in (self.start_date + timedelta(n) for n in range(day_count)) if
										d <= self.end_date]:
			if single_date.weekday() < 5:
				work_day_count += 1

		if self.type == 'employee':
			row = 0
			worksheet.write(row,0,'Employee Name',header_text_format)
			worksheet.write(row,1,'Public Holiday',header_text_format)
			worksheet.write(row,2,'Work From Home',header_text_format)
			worksheet.write(row,3,'Leave Day',header_text_format)
			worksheet.write(row,4,'Active Working Day',header_text_format)
			col = 5
			for date in date_list:
				worksheet.set_column(xl_rowcol_to_cell(row, col)+':'+xl_rowcol_to_cell(row, col), 13)
				worksheet.write(row,col,date.strftime('%a') + '\n' + date.strftime('%b %d') ,header_text_format)
				col+=1
			worksheet.set_column(xl_rowcol_to_cell(row, col)+':'+xl_rowcol_to_cell(row, col), 22)
			worksheet.set_column(xl_rowcol_to_cell(row, col+2)+':'+xl_rowcol_to_cell(row, col+1), 30)
			worksheet.set_column(xl_rowcol_to_cell(row, col+2)+':'+xl_rowcol_to_cell(row, col+4), 22)
			worksheet.write(row,col,'Total working Hours',header_text_format)
			worksheet.write(row,col+1,'Total Actual Work Hours',header_text_format)

			worksheet.write(row,col+2,'Combine Extra/Missing Hours',header_text_format)
			worksheet.write(row,col+3,'Extra Hours',header_text_format)
			worksheet.write(row,col+4,'Missing Hours',header_text_format)
			row+=1

			all_employee_ids = []
			if self.employee_ids:
				for employee in self.employee_ids:
					all_employee_ids.append(employee)
			else:
				employee_id = self.env['hr.employee'].search([('user_id', '!=', 2),('user_id.partner_id.user_id', '=', False)])
				for employee in employee_id:
					all_employee_ids.append(employee)


			public_holiday_ids = self.env['resource.calendar.leaves'].search([('company_id', '=', self.env.company.id),('date_from', '>=',self.start_date),('date_to', '<=',self.end_date), ('resource_id', '=', False)])
			for employee in all_employee_ids:

				if not employee:
					return

				leave_domain = [
					('employee_id', '=', employee.id),
					('request_date_from', '<=', self.end_date),
					('request_date_to', '>=', self.start_date),
					('request_unit_half', '=', False),
					('state', '!=', 'refuse'),
				]

				hald_day_leave_domain = [
					('employee_id', '=', employee.id),
					('request_date_from', '<=', self.end_date),
					('request_date_to', '>=', self.start_date),
					('request_unit_half', '=', True),
					('state', '!=', 'refuse'),
				]

				leave_ids = self.env['hr.leave'].search(leave_domain)
				half_day_leave_ids = self.env['hr.leave'].search(hald_day_leave_domain)
				
				total_leave_days = 0
				total_wfh_days = 0
				
				total_full_leave_days = 0
				total_full_wfh_days = 0
				for leave in leave_ids:
					leave_start = max(leave.request_date_from, self.start_date)
					leave_end = min(leave.request_date_to, self.end_date)
					
					leave_duration = leave_end - leave_start + timedelta(days=1)
					
					current_date = leave_start
					while current_date <= leave_end:
						if current_date.weekday() < 5: 
							if leave.is_work_from_home_leave:
								total_full_wfh_days += 1
							else:
								total_full_leave_days += 1
						current_date += timedelta(days=1)

				total_half_day_leave_days = 0
				total_half_day_wfh_days = 0
				for leave in half_day_leave_ids:
					leave_start = max(leave.request_date_from, self.start_date)
					leave_end = min(leave.request_date_to, self.end_date)
					
					leave_duration = leave_end - leave_start + timedelta(days=1)
					
					current_date = leave_start
					while current_date <= leave_end:
						if current_date.weekday() < 5: 
							if leave.is_work_from_home_leave:
								total_half_day_wfh_days += 1 / 2
							else:
								total_half_day_leave_days += 1 / 2
						current_date += timedelta(days=1)

				total_leave_days = total_full_leave_days + total_half_day_leave_days
				total_wfh_days = total_full_wfh_days + total_half_day_wfh_days

				# leave_ids = self.env['hr.leave'].search([('employee_id','=',employee.id),('request_date_from','>=',self.start_date),('request_date_to','<=',self.end_date)])
				# total_work_from_home = sum(leave_ids.filtered(lambda x:x.is_work_from_home_leave).mapped('number_of_days_display'))
				# total_leave = sum(leave_ids.filtered(lambda x:not x.is_work_from_home_leave).mapped('number_of_days_display'))
				active_working_days = work_day_count - (total_leave_days + len(public_holiday_ids))
					
				worksheet.write(row,0,employee.name or '',value_format)
				worksheet.write(row,1,len(public_holiday_ids) or 0.0,number_value_format)
				worksheet.write(row,2,total_wfh_days or 0.0,number_value_format)
				worksheet.write(row,3,total_leave_days or 0.0,number_value_format)
				worksheet.write(row,4,active_working_days if active_working_days > 0 else 0.0,number_value_format)
				# worksheet.write(row,4,work_day_count - total_leave_days or 0.0,number_value_format)
				col = 5
				total_working_hourss = 0.0
				
				for date in date_list:
					attendance_ids = self.env['account.analytic.line'].search([('employee_id','=',employee.id),('date','>=',date),('date','<=',date), ('state','=','approve')])
					# working_hours = sum(attendance_ids.mapped('unit_amount'))

					working_hours_unformatted = sum(attendance_ids.mapped('unit_amount'))
					hours = int(working_hours_unformatted)
					minutes = int((working_hours_unformatted - hours) * 60)
					working_hours = '{:02d}:{:02d}'.format(hours, minutes)


					worksheet.write(row,col,working_hours or 0.0,number_value_format)
					total_working_hourss += working_hours_unformatted
					hours = int(total_working_hourss)
					minutes = int((total_working_hourss - hours) * 60)
					total_working_hours = '{:02d}:{:02d}'.format(hours, minutes)
					# total_working_hours+=working_hours
					col+=1

				total_public_holiday_hrs = sum([a.calendar_id.hours_per_day for a in public_holiday_ids])
				total_actual_working_hss = (work_day_count-total_leave_days)*employee.resource_calendar_id.hours_per_day or (work_day_count-total_leave_days)*8
				total_actual_working_hss = total_actual_working_hss - total_public_holiday_hrs
				
				hours = int(total_actual_working_hss)
				minutes = int((total_actual_working_hss - hours) * 60)
				total_actual_working_hs = '{:02d}:{:02d}'.format(hours, minutes)

				total_missing_hourss = (total_working_hourss) - total_actual_working_hss if total_actual_working_hss > 0 else 0.0
				# total_missing_hourss = (total_working_hourss) - total_actual_working_hss
				hours = int(total_missing_hourss)
				minutes = int((total_missing_hourss - hours) * 60)
				total_missing_hours = '{:02d}:{:02d}'.format(hours, minutes)

				worksheet.write(row,col,(total_working_hours),number_value_format)
				worksheet.write(row,col+1,total_actual_working_hs if total_actual_working_hss > 0 else 0.0,number_value_format)

				worksheet.write(row,col+2,total_missing_hours ,number_value_format)
				worksheet.write(row,col+3, total_missing_hours if total_missing_hourss > 0 else 0, number_value_format)
				worksheet.write(row,col+4, total_missing_hours if total_missing_hourss < 0 else 0, number_value_format)

				row+=1
		else:
			worksheet.set_column('E:E', 25)
			worksheet.set_column('F:F', 25)
			row = 0
			worksheet.write(row,0,'Project Name',header_text_format)
			worksheet.write(row,1,'Employee Name',header_text_format)
			worksheet.write(row,2,'Public Holiday',header_text_format)
			worksheet.write(row,3,'Work From Home',header_text_format)
			worksheet.write(row,4,'Leave Day',header_text_format)
			worksheet.write(row,5,'Active Working Day',header_text_format)
			col = 6
			for date in date_list:
				worksheet.set_column(xl_rowcol_to_cell(row, col)+':'+xl_rowcol_to_cell(row, col), 13)
				worksheet.write(row,col,date.strftime('%a') + '\n' + date.strftime('%b %d') ,header_text_format)
				col+=1
			worksheet.set_column(xl_rowcol_to_cell(row, col)+':'+xl_rowcol_to_cell(row, col), 22)
			worksheet.set_column(xl_rowcol_to_cell(row, col+1)+':'+xl_rowcol_to_cell(row, col+1), 32)
			worksheet.write(row,col,'Total working',header_text_format)
			worksheet.write(row,col+1,'Total Hrs Spent On Project',header_text_format)
			row+=1

			# analytic_ids = self.env['account.analytic.line'].search([('date','>=',self.start_date),('date','<=',self.end_date)])
			# project_ids = analytic_ids.mapped('project_id')
			public_holiday_ids = self.env['resource.calendar.leaves'].search([('company_id', '=', self.env.company.id),('date_from', '>=',self.start_date),('date_to', '<=',self.end_date), ('resource_id', '=', False)])

			all_project_ids = []
			if self.project_ids:
				analytic_ids = self.env['account.analytic.line'].search([('date','>=',self.start_date),('date','<=',self.end_date), ('project_id', 'in', self.project_ids.ids), ('state','=','approve')])
				project_ids = analytic_ids.mapped('project_id')
				for project in project_ids:
					all_project_ids.append(project)
			else:
				analytic_ids = self.env['account.analytic.line'].search([('date','>=',self.start_date),('date','<=',self.end_date), ('state','=','approve')])
				project_ids = analytic_ids.mapped('project_id')
				for project in project_ids:
					all_project_ids.append(project)


			for project in all_project_ids:
				worksheet.write(row,0,project.name or '',header_text_format_3)
				row+=1
				cols = 0
				meta_analytic_ids = analytic_ids.search([('project_id','=',project.id),('date','>=',self.start_date),('date','<=',self.end_date), ('state','=','approve')])
				employee_ids = meta_analytic_ids.mapped('employee_id')
				for employee in employee_ids:

					if not employee:
						return

					leave_domain = [
						('employee_id', '=', employee.id),
						('request_date_from', '<=', self.end_date),
						('request_date_to', '>=', self.start_date),
						('request_unit_half', '=', False),
						('state', '!=', 'refuse'),
					]

					hald_day_leave_domain = [
						('employee_id', '=', employee.id),
						('request_date_from', '<=', self.end_date),
						('request_date_to', '>=', self.start_date),
						('request_unit_half', '=', True),
						('state', '!=', 'refuse'),
					]
					leave_ids = self.env['hr.leave'].search(leave_domain)
					half_day_leave_ids = self.env['hr.leave'].search(hald_day_leave_domain)
					
					total_leave_days = 0
					total_wfh_days = 0
					
					total_full_leave_days = 0
					total_full_wfh_days = 0
					for leave in leave_ids:
						leave_start = max(leave.request_date_from, self.start_date)
						leave_end = min(leave.request_date_to, self.end_date)
						
						leave_duration = leave_end - leave_start + timedelta(days=1)
						
						current_date = leave_start
						while current_date <= leave_end:
							if current_date.weekday() < 5: 
								if leave.is_work_from_home_leave:
									total_full_wfh_days += 1
								else:
									total_full_leave_days += 1
							current_date += timedelta(days=1)

					total_half_day_leave_days = 0
					total_half_day_wfh_days = 0
					for leave in half_day_leave_ids:
						leave_start = max(leave.request_date_from, self.start_date)
						leave_end = min(leave.request_date_to, self.end_date)
						
						leave_duration = leave_end - leave_start + timedelta(days=1)
						
						current_date = leave_start
						while current_date <= leave_end:
							if current_date.weekday() < 5: 
								if leave.is_work_from_home_leave:
									total_half_day_wfh_days += 1 / 2
								else:
									total_half_day_leave_days += 1 / 2
							current_date += timedelta(days=1)

					total_leave_days = total_full_leave_days + total_half_day_leave_days
					total_wfh_days = total_full_wfh_days + total_half_day_wfh_days

					active_working_days = work_day_count - (total_leave_days + len(public_holiday_ids))
					
					worksheet.write(row,1,employee.name or '',value_format)
					worksheet.write(row,2,len(public_holiday_ids) or 0.0,number_value_format)
					worksheet.write(row,3,total_wfh_days or 0.0,number_value_format)
					worksheet.write(row,4,total_leave_days or 0.0,number_value_format)
					worksheet.write(row,5,active_working_days if active_working_days > 0 else 0.0,number_value_format)
					# worksheet.write(row,5,work_day_count - total_leave_days or 0.0,number_value_format)
					
					col = 6
					total_working_hourss = 0.0
				
					for date in date_list:
						attendance_ids = meta_analytic_ids.search([('project_id','=',project.id),('employee_id','=',employee.id),('date','>=',date),('date','<=',date), ('state','=','approve')])
						# working_hours = sum(attendance_ids.mapped('unit_amount'))

						working_hours_unformatted = sum(attendance_ids.mapped('unit_amount'))
						hours = int(working_hours_unformatted)
						minutes = int((working_hours_unformatted - hours) * 60)
						working_hours = '{:02d}:{:02d}'.format(hours, minutes)

						worksheet.write(row,col,working_hours or 0.0,number_value_format)
						total_working_hourss+=working_hours_unformatted
						hours = int(total_working_hourss)
						minutes = int((total_working_hourss - hours) * 60)
						total_working_hours = '{:02d}:{:02d}'.format(hours, minutes)
						col+=1
					total_missing_hours = (work_day_count*employee.resource_calendar_id.hours_per_day or work_day_count*8) - total_working_hourss
					worksheet.write(row,col,total_working_hours,number_value_format)
					row+=1
					cols = col
				total_project_times = sum(meta_analytic_ids.mapped('unit_amount'))
				hours = int(total_project_times)
				minutes = int((total_project_times - hours) * 60)
				total_project_time = '{:02d}:{:02d}'.format(hours, minutes)
				worksheet.write(row-1,col+1,total_project_time or 0.0,number_value_format_2)
				row+=1

		workbook.close()	
		file_download = base64.b64encode(fp.getvalue())
		fp.close()
		data_file = open(config['data_dir'] + "/Timesheet Report", "rb")
		out = data_file.read()
		data_file.close()
		self.file = base64.b64encode(out)
		
		return {
			'name': 'Timesheet Report',
			'type': 'ir.actions.act_url',
			'url': '/web/content/%s/%d/file/%s?download=false' % (self._name, self.id, 'Timesheet Report'),
		}