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

class HrProjectTask(models.Model):
	_inherit = 'project.task'

	# estimated_time = fields.Float(string="Estimated Hours")
	planned_date = fields.Date(string="Planned Date", default=date.today())
	is_user = fields.Boolean(string="Is User", default=True, compute='_compute_user_group')
	# planned_hours = fields.Float("Initially Planned Hours", tracking=True, related="estimated_time")
	file = fields.Binary('File')

	@api.depends('effective_hours', 'subtask_effective_hours', 'planned_hours')
	def _compute_progress_hours(self):
		res = super(HrProjectTask, self)._compute_progress_hours()
		for task in self:
			if (task.planned_hours > 0.0):
				task_total_hours = task.effective_hours + task.subtask_effective_hours
				task.overtime = max(task_total_hours - task.planned_hours, 0)
				# if task_total_hours > task.planned_hours:
				#     task.progress = 100
				# else:
				task.progress = round(100.0 * task_total_hours / task.planned_hours, 2)
			else:
				task.progress = 0.0
				task.overtime = 0
		return res


	def _compute_user_group(self):
		user_name = self.env.user
		if user_name.has_group('project.group_project_user') and not user_name.has_group('project.group_project_manager'):
			self.is_user = True
		else:
			self.is_user = False


	def print_xlsx_report(self):
		file_name = f"{self.project_id.name}.xlsx"
		fp = BytesIO()

		workbook = xlsxwriter.Workbook(fp)
		date_format = workbook.add_format({'num_format': 'mm/dd/yyyy'})
		header_text_format = workbook.add_format({'font_size': 12, 'align':'center','bold':True,'valign':'vcenter','bg_color':'#d0cece'})
		value_format = workbook.add_format({'font_size': 13, 'align':'left','valign':'vcenter'})
		value_format_1 = workbook.add_format({'font_size': 13, 'align':'right','valign':'vcenter'})
		number_value_format = workbook.add_format({'font_size': 13, 'align':'right', 'valign':'vcenter','num_format': '#,###0.00'})

		worksheet = workbook.add_worksheet('Timesheet Report')
		worksheet.set_column('A:A', 30)
		worksheet.set_column('B:B', 32)
		worksheet.set_column('C:F', 20)
		worksheet.set_column('G:G', 22)

		row = 0

		worksheet.write(row,0,'Project Name',header_text_format)
		worksheet.write(row,1,'Task Name',header_text_format)
		worksheet.write(row,2,'Planned Date',header_text_format)
		worksheet.write(row,3,'Task Deadline',header_text_format)
		worksheet.write(row,4,'Estimated Hrs',header_text_format)
		worksheet.write(row,5,'Actual Efforts',header_text_format)
		worksheet.write(row,6,'% Of work Completed',header_text_format)

		row+=1

		worksheet.write(row,0,self.project_id.name or '',value_format)

		project_task_id = self.env['project.task'].search([])
		project_wise_task = project_task_id.search([('project_id', '=', self.project_id.id)])

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
