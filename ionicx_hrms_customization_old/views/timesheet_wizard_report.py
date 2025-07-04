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

class TimesheetReportWizard(models.TransientModel):
	_name = 'timesheet.report.wizard'
	_description = 'Timesheet Report Wizard'

	type = fields.Selection([('employee','Employee'),('project','Project')],default='employee',string='Type')
	start_date = fields.Date('From Date')
	end_date = fields.Date('To Date')
	file = fields.Binary('File')

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
		worksheet.set_column('B:D', 22)

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
			worksheet.write(row,1,'Work From Home',header_text_format)
			worksheet.write(row,2,'Leave Day',header_text_format)
			worksheet.write(row,3,'Active Working Day',header_text_format)
			col = 4
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

			employee_ids = self.env['hr.employee'].search([])
			
			for employee in employee_ids:

				if not employee:
					return

				leave_domain = [
					('employee_id', '=', employee.id),
					('request_date_from', '<=', self.end_date),
					('request_date_to', '>=', self.start_date)
				]
				leave_ids = self.env['hr.leave'].search(leave_domain)
				
				total_leave_days = 0
				total_wfh_days = 0
				
				for leave in leave_ids:
					if leave.is_work_from_home_leave == False:
						leave_start = max(leave.request_date_from, self.start_date)
						leave_end = min(leave.request_date_to, self.end_date)
						
						leave_duration = leave_end - leave_start + timedelta(days=1)
						total_leave_days += leave_duration.days
					else:
						leave_start = max(leave.request_date_from, self.start_date)
						leave_end = min(leave.request_date_to, self.end_date)
						
						leave_duration = leave_end - leave_start + timedelta(days=1)
						total_wfh_days += leave_duration.days

				leave_ids = self.env['hr.leave'].search([('employee_id','=',employee.id),('request_date_from','>=',self.start_date),('request_date_to','<=',self.end_date)])
				total_work_from_home = sum(leave_ids.filtered(lambda x:x.is_work_from_home_leave).mapped('number_of_days_display'))
				total_leave = sum(leave_ids.filtered(lambda x:not x.is_work_from_home_leave).mapped('number_of_days_display'))
					
				worksheet.write(row,0,employee.name or '',value_format)
				worksheet.write(row,1,total_wfh_days or 0.0,number_value_format)
				# worksheet.write(row,1,total_work_from_home or 0.0,number_value_format)
				worksheet.write(row,2,total_leave_days or 0.0,number_value_format)
				# worksheet.write(row,2,total_leave or 0.0,number_value_format)
				worksheet.write(row,3,work_day_count - total_leave_days or 0.0,number_value_format)
				# worksheet.write(row,3,work_day_count - total_leave or 0.0,number_value_format)
				col = 4
				total_working_hours = 0.0
				
				for date in date_list:
					attendance_ids = self.env['account.analytic.line'].search([('employee_id','=',employee.id),('date','>=',date),('date','<=',date)])
					working_hours = sum(attendance_ids.mapped('unit_amount'))
					worksheet.write(row,col,working_hours or 0.0,number_value_format)
					total_working_hours+=working_hours
					col+=1

				# total_actual_working_hs = (work_day_count-total_leave)*employee.resource_calendar_id.hours_per_day or (work_day_count-total_leave)*8
				# total_actual_working_hs = (work_day_count)*employee.resource_calendar_id.hours_per_day or (work_day_count-total_leave)*8
				# total_missing_hours = (total_working_hours - total_leave*8) - total_actual_working_hs
				total_actual_working_hs = (work_day_count-total_leave_days)*employee.resource_calendar_id.hours_per_day or (work_day_count-total_leave_days)*8
				total_missing_hours = (total_working_hours) - total_actual_working_hs

				worksheet.write(row,col,(total_working_hours),number_value_format)
				worksheet.write(row,col+1,(work_day_count - total_leave_days)*employee.resource_calendar_id.hours_per_day or (work_day_count-total_leave_days)*8,number_value_format)
				# worksheet.write(row,col+1,(work_day_count-total_leave)*employee.resource_calendar_id.hours_per_day or (work_day_count-total_leave)*8,number_value_format)

				worksheet.write(row,col+2,total_missing_hours ,number_value_format)
				worksheet.write(row,col+3, total_missing_hours if total_missing_hours > 0 else 0, number_value_format)
				worksheet.write(row,col+4, total_missing_hours if total_missing_hours < 0 else 0, number_value_format)

				row+=1
		else:
			worksheet.set_column('E:E', 25)
			row = 0
			worksheet.write(row,0,'Project Name',header_text_format)
			worksheet.write(row,1,'Employee Name',header_text_format)
			worksheet.write(row,2,'Work From Home',header_text_format)
			worksheet.write(row,3,'Leave Day',header_text_format)
			worksheet.write(row,4,'Active Working Day',header_text_format)
			col = 5
			for date in date_list:
				worksheet.set_column(xl_rowcol_to_cell(row, col)+':'+xl_rowcol_to_cell(row, col), 13)
				worksheet.write(row,col,date.strftime('%a') + '\n' + date.strftime('%b %d') ,header_text_format)
				col+=1
			worksheet.set_column(xl_rowcol_to_cell(row, col)+':'+xl_rowcol_to_cell(row, col), 22)
			worksheet.set_column(xl_rowcol_to_cell(row, col+1)+':'+xl_rowcol_to_cell(row, col+1), 32)
			# worksheet.set_column(xl_rowcol_to_cell(row, col+2)+':'+xl_rowcol_to_cell(row, col+2), 22)
			# worksheet.set_column(xl_rowcol_to_cell(row, col+3)+':'+xl_rowcol_to_cell(row, col+3), 32)
			worksheet.write(row,col,'Total working',header_text_format)
			# worksheet.write(row,col+1,'Total Hours',header_text_format)
			# worksheet.write(row,col+2,'Total Missing',header_text_format)
			worksheet.write(row,col+1,'Total Hrs Spent On Project',header_text_format)
			row+=1

			# analytic_ids = self.env['account.analytic.line'].search([])
			analytic_ids = self.env['account.analytic.line'].search([('date','>=',self.start_date),('date','<=',self.end_date)])
			project_ids = analytic_ids.mapped('project_id')
			
			for project in project_ids:
				worksheet.write(row,0,project.name or '',header_text_format_3)
				row+=1
				cols = 0
				meta_analytic_ids = analytic_ids.search([('project_id','=',project.id),('date','>=',self.start_date),('date','<=',self.end_date)])
				employee_ids = meta_analytic_ids.mapped('employee_id')
				for employee in employee_ids:

					if not employee:
						return

					leave_domain = [
						('employee_id', '=', employee.id),
						('request_date_from', '<=', self.end_date),
						('request_date_to', '>=', self.start_date)
					]
					
					leave_ids = self.env['hr.leave'].search(leave_domain)
					
					total_leave_days = 0
					total_wfh_days = 0
					
					for leave in leave_ids:
						if leave.is_work_from_home_leave == False:
							leave_start = max(leave.request_date_from, self.start_date)
							leave_end = min(leave.request_date_to, self.end_date)
							
							leave_duration = leave_end - leave_start + timedelta(days=1)
							total_leave_days += leave_duration.days
						else:
							leave_start = max(leave.request_date_from, self.start_date)
							leave_end = min(leave.request_date_to, self.end_date)
							
							leave_duration = leave_end - leave_start + timedelta(days=1)
							total_wfh_days += leave_duration.days

					# leave_ids = self.env['hr.leave'].search([('employee_id','=',employee.id),('request_date_from','>=',self.start_date),('request_date_to','<=',self.end_date)])
					# total_work_from_home = sum(leave_ids.filtered(lambda x:x.is_work_from_home_leave).mapped('number_of_days_display'))
					# total_leave = sum(leave_ids.filtered(lambda x:not x.is_work_from_home_leave).mapped('number_of_days_display'))
					
					worksheet.write(row,1,employee.name or '',value_format)
					worksheet.write(row,2,total_wfh_days or 0.0,number_value_format)
					# worksheet.write(row,2,total_work_from_home or 0.0,number_value_format)
					worksheet.write(row,3,total_leave_days or 0.0,number_value_format)
					# worksheet.write(row,3,total_leave or 0.0,number_value_format)
					worksheet.write(row,4,work_day_count - total_leave_days or 0.0,number_value_format)
					
					col = 5
					total_working_hours = 0.0
				
					for date in date_list:
						attendance_ids = meta_analytic_ids.search([('project_id','=',project.id),('employee_id','=',employee.id),('date','>=',date),('date','<=',date)])
						working_hours = sum(attendance_ids.mapped('unit_amount'))
						worksheet.write(row,col,working_hours or 0.0,number_value_format)
						total_working_hours+=working_hours
						col+=1
					total_missing_hours = (work_day_count*employee.resource_calendar_id.hours_per_day or work_day_count*8) - total_working_hours
					worksheet.write(row,col,total_working_hours,number_value_format)
					# worksheet.write(row,col+1,work_day_count*employee.resource_calendar_id.hours_per_day or work_day_count*8,number_value_format)
					# worksheet.write(row,col+2,total_missing_hours if total_missing_hours > 0 else 0,number_value_format)
					row+=1
					cols = col
				total_project_time = sum(meta_analytic_ids.mapped('unit_amount'))
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