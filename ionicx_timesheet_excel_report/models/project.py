# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from datetime import datetime, date, timedelta
import base64
import os
from dateutil.relativedelta import relativedelta
from io import BytesIO
import xlsxwriter
from odoo.tools import config
from xlsxwriter.utility import xl_rowcol_to_cell
import calendar
import logging

_logger = logging.getLogger(__name__)

class HrProjectTask(models.Model):
	_inherit = 'project.project'

	progress = fields.Float('Progress', group_operator='avg', readonly=True, compute='_compute_progress')
	file = fields.Binary('File')
	email_send_to = fields.Many2many('res.users','project_id', 'users_id','rel_project_users', string="Estimation Email Send To")
	timesheet_app_ids = fields.Many2many(
		'res.users',
		'rel_timesheet_project_users',
		'project_id',
		'user_id',
		string="Timesheet Exceeded Mail"
	)


	def check_project_and_task_hours(self):
		"""Check if timesheet hours exceed allocated hours for projects and tasks."""
		projects = self.search([])
		mail_template = self.env.ref('ionicx_timesheet_excel_report.mail_template_project_exceed')
		for project in projects:
			total_project_hours = sum(project.timesheet_ids.mapped('unit_amount'))
			if project.allocated_hours and total_project_hours > project.allocated_hours:
				if mail_template:
					ctx = {}
					for approver in project.timesheet_app_ids:
						missing_dic = {
							'total_hours':total_project_hours,
							'allocated_hours':project.allocated_hours,
							'user':approver.name,
							'object':project,
							'project_name':project.name
						} 
						ctx['missing_datas'] = missing_dic
						mail_template.with_context(ctx).sudo().send_mail(project.id, force_send=True, email_values={
						'email_to': approver.login})
						_logger.info(f"Reminder email sent for project: {project.name}")

			for task in project.task_ids:
				total_task_hours = sum(task.timesheet_ids.mapped('unit_amount'))
				if task.planned_hours and total_task_hours > task.planned_hours:
					if mail_template:
						ctx = {}
						for approver in task.project_id.timesheet_app_ids:
							missing_dic = {
								'total_hours':total_task_hours,
								'allocated_hours':task.planned_hours,
								'user':approver.name,
								'object':task,
								'project_name':task.name
							} 
							ctx['missing_datas'] = missing_dic
							mail_template.with_context(ctx).sudo().send_mail(project.id, force_send=True, email_values={
							'email_to': approver.login})
							_logger.info(f"Reminder email sent for task: {task.name}")


	@api.depends('allocated_hours')
	def _compute_progress(self):
		for rec in self:
			if rec.allocated_hours:
				# approved_timesheets = rec.timesheet_ids.search([('state', '=', 'approve')])
				# total_approved_hours = sum(approved_timesheets.mapped('unit_amount'))
				working_hours = sum(rec.timesheet_ids.mapped('unit_amount'))
				progress_percentage = working_hours * 100 / rec.allocated_hours
				rec.progress = round(progress_percentage, 2)
			else:
				rec.progress = 0

	def check_project_timesheet(self):
		project_ids = self.search([])
		day_no = datetime.today().weekday()
		if day_no < 5:
			for project in project_ids:
				missing_datas = []
				ctx = {}
				project_task_id = self.env['project.task'].search([])
				project_wise_task = project_task_id.search([('project_id', '=', project.id)])

				for task in project_wise_task:
					missing_dic = {
						'project_name' : project.name,
						'project_manager' : project.user_id.name,
						'project_date_start' : project.date_start,
						'project_date' : project.date,
						'project_allocated_hrs' : project.allocated_hours,
						'project_total_hrs_spent' : project.total_hrs_spent,
						'project_progress' : project.progress,
						'task_name' :  task.name,
						'planned_date' : task.planned_date,
						'task_deadline' : task.date_deadline,
						'estimated_time' : task.planned_hours,
						# 'estimated_time' : task.estimated_time,
						'acctual_hrs' : task.effective_hours,
						'progress' : task.progress,
					}
					missing_datas.append(missing_dic)
				ctx['missing_datas'] = missing_datas
				# Send Email Alert
				users_list = []
				users_list.append(project.user_id)
				for user in project.email_send_to:
					users_list.append(user)
				for user_login in users_list:
					mail_template = self.env.ref('ionicx_timesheet_excel_report.update_project_email_template')
					mail_template.with_context(ctx).sudo().send_mail(self.user_id.id, force_send=True, email_values={
						'email_to': user_login.login})


	def print_xlsx_report(self):
		file_name = f"{self.name}.xlsx"
		fp = BytesIO()

		workbook = xlsxwriter.Workbook(fp)
		date_format = workbook.add_format({'num_format': 'mm/dd/yyyy'})
		header_text_format = workbook.add_format({'font_size': 12, 'align':'center','bold':True,'valign':'vcenter','bg_color':'#d0cece'})
		value_format = workbook.add_format({'font_size': 13, 'align':'left','valign':'vcenter'})
		value_format_1 = workbook.add_format({'font_size': 13, 'align':'right','valign':'vcenter', 'num_format': '0.00'})
		number_value_format = workbook.add_format({'font_size': 13, 'align':'right', 'valign':'vcenter','num_format': '#,###0.00'})

		worksheet = workbook.add_worksheet('Timesheet Report')
		worksheet.set_column('A:A', 30)
		worksheet.set_column('B:B', 32)
		worksheet.set_column('C:F', 20)
		worksheet.set_column('G:G', 22)

		row = 0

		worksheet.write(row,0,'Project Name',header_text_format)
		worksheet.write(row,1,'Customer',header_text_format)
		worksheet.write(row,2,'Planned Date',header_text_format)
		worksheet.write(row,3,'Deadline',header_text_format)
		worksheet.write(row,4,'Allocated Hours',header_text_format)
		worksheet.write(row,5,'Actual Efforts',header_text_format)
		worksheet.write(row,6,'% Of work Completed',header_text_format)

		row+=1

		worksheet.write(row,0,self.name or '',value_format)
		worksheet.write(row,1,self.partner_id.name or '',value_format)
		worksheet.write(row,2,self.date_start or '',date_format)
		worksheet.write(row,3,self.date or '',date_format)
		worksheet.write(row,4,self.allocated_hours or 0.00 ,number_value_format)
		worksheet.write(row,5,self.total_hrs_spent or 0.00 ,number_value_format)
		worksheet.write(row,6,str(self.progress) + '%',value_format_1)

		project_task_id = self.env['project.task'].search([])
		project_wise_task = project_task_id.search([('project_id', '=', self.name)])

		row+=2

		worksheet.write(row,1,'Task Name',header_text_format)
		worksheet.write(row,2,'Planned Date',header_text_format)
		worksheet.write(row,3,'Deadline',header_text_format)
		worksheet.write(row,4,'Estimated Hours',header_text_format)
		worksheet.write(row,5,'Actual Efforts',header_text_format)
		worksheet.write(row,6,'% Of work Completed',header_text_format)

		row+=1
		for task in project_wise_task:

			worksheet.write(row,1,task.name or '',value_format)
			worksheet.write(row,2,task.planned_date or '', date_format)
			worksheet.write(row,3,task.date_deadline or '', date_format)
			worksheet.write(row,4,task.planned_hours or 0.0,number_value_format)
			# worksheet.write(row,4,task.estimated_time or 0.0,number_value_format)
			worksheet.write(row,5,task.effective_hours or 0.0,number_value_format)
			worksheet.write(row, 6, str(task.progress) + '%', value_format_1)
			row+=1

		workbook.close()

		file_download = base64.b64encode(fp.getvalue())
		fp.close()

		self.file = file_download

		return {
			'name': file_name,
			'type': 'ir.actions.act_url',
			'url': '/web/content/%s/%d/file/%s?download=false' % (self._name, self.id, file_name),
		}
