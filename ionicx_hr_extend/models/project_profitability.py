# -*- coding: utf-8 -*-

import os
import base64
import calendar
import xlsxwriter
from io import BytesIO
from odoo.tools import config
from odoo import api, fields, models, _
from datetime import datetime, date, timedelta
from xlsxwriter.utility import xl_rowcol_to_cell
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError, ValidationError

class ProjectProfitability(models.TransientModel):
	_name = 'project.profitability'
	_description = ' Project Profitability'

	project_ids = fields.Many2many('project.project', 'project_profitability_rel', 'project_id', 'profitability_id', string="Project")
	file = fields.Binary('File')

	def print_pdf_report(self):
		domain = [
			('id', 'in', self.project_ids.ids),
		]
		if self.project_ids:
			name = self.env['project.project'].search(domain)
		else:
			name = self.env['project.project'].search([])

		return self.env.ref('ionicx_hr_extend.action_project_profitability_report').report_action(name)

	def print_xlsx_report(self):
		file_name = _('Project Profitability Report.xlsx')
		# Creates a BytesIO object to store the Excel file in memory.
		fp = BytesIO()

		workbook = xlsxwriter.Workbook(fp)
		date_format = workbook.add_format({'num_format': 'mm/dd/yyyy'})
		header_text_format = workbook.add_format({'font_size': 12, 'align':'center','bold':True,'valign':'vcenter','bg_color':'#d0cece'})
		value_format = workbook.add_format({'font_size': 13, 'align':'left','valign':'vcenter'})
		value_format_1 = workbook.add_format({'font_size': 13, 'align':'right','valign':'vcenter'})
		number_value_format = workbook.add_format({'font_size': 13, 'align':'right', 'valign':'vcenter','num_format': '#,###0.00'})

		worksheet = workbook.add_worksheet('Project Profitability Report')
		worksheet.set_column('A:A', 30)
		worksheet.set_column('B:B', 32)
		worksheet.set_column('C:F', 20)
		worksheet.set_column('G:G', 22)

		row = 0

		worksheet.write(row,0,'Project Name',header_text_format)
		worksheet.write(row,1,'Planned Date',header_text_format)
		worksheet.write(row,2,'Deadline',header_text_format)
		worksheet.write(row,3,'% Work Complete',header_text_format)
		worksheet.write(row,4,'Planned Cost',header_text_format)
		worksheet.write(row,5,'Actual Cost',header_text_format)
		worksheet.write(row,6,'Planned Revenue',header_text_format)

		row+=1

		all_projects = []
		if self.project_ids:
			for project in self.project_ids:
				all_projects.append(project)
		else:
			project_id = self.env['project.project'].search([])
			for project in project_id:
				all_projects.append(project)

		for project in all_projects:
			worksheet.write(row,0,project.name or '',value_format)
			worksheet.write(row,1,project.date_start or 0.0,date_format)
			worksheet.write(row,2,project.date or 0.0, date_format)
			worksheet.write(row,3,str(project.progress)+'%' or 0.0, number_value_format)
			worksheet.write(row,4,project.gross_margin or 0.0,number_value_format)
			worksheet.write(row,5,project.time_cost or 0.0,number_value_format)
			worksheet.write(row,6,project.gross_margin - project.time_cost or 0.0,number_value_format)
			row+=1

		workbook.close()

		#  Encodes the Excel file content into base64 for download.
		file_download = base64.b64encode(fp.getvalue())
		# Closes the BytesIO object.
		fp.close()

		#  Stores the base64-encoded file content in the file attribute of the instance.
		self.file = file_download

		# Returns an action dictionary to trigger the download in the Odoo interface.
		return {
			'name': file_name,
			'type': 'ir.actions.act_url',
			'url': '/web/content/%s/%d/file/%s?download=false' % (self._name, self.id, file_name),
		}
		#  Specifies the action type (ir.actions.act_url).
		#  Constructs the URL for downloading the file using Odoo's web content endpoint.


class ProjectProfitability(models.Model):
	_inherit = 'project.project'

	
	total_hrs_spent = fields.Float(string="Total Hrs Spent On Project", compute="_compute_total_project_hrs")
	per_hrs_charges = fields.Monetary(string="Project Hourly Rate")
	project_fix_amt_charges = fields.Monetary(string="Project Fixed Costing")
	project_revenue = fields.Float(string="Project Fixed Revenue")
	project_hourly_revenue = fields.Float(string="Project Hourly Rate Revenue")
	direct_cost = fields.Monetary(string="Direct Cost/Expenses", compute="_compute_total_project_hrs")
	time_cost = fields.Monetary(string="Time Cost", compute="_compute_total_project_hrs")
	currency_id = fields.Many2one(string="Currency", related='company_id.currency_id', readonly=True)
	expenses_ids = fields.One2many('project.expenses', 'project_id', string="Expenses")
	gross_margin = fields.Monetary(string="Gross Margin", compute="_compute_total_project_hrs")
	work_rate = fields.Selection(
		selection=[
		('hrs_basis', 'Hourly Basis Rate'),
		('fixed_amt', 'Fixed Amount'),
		], string="Project Rate", default="fixed_amt")
	work_rate_client_side = fields.Selection(
		selection=[
		('hrs_basis', 'Hourly Basis Rate'),
		('fixed_amt', 'Fixed Amount'),
		], string="Project Rate", default="fixed_amt")
	payment_status = fields.Selection(
		selection=[
		('paid', 'Fully Paid'),
		('partial_paid', 'Partial Paid'),
		('unpaid', 'Unpaid'),
		], string="Payment Status",)
	payment_amount = fields.Monetary(string="Amount Paid")
	total_expenses = fields.Monetary(string="Total", compute="_compute_total_expenses")


	@api.depends("expenses_ids.amount")
	def _compute_total_expenses(self):
		for record in self:
			record.total_expenses = sum(record.expenses_ids.mapped("amount"))


	@api.model
	def default_get(self, fields_list):
		res = super(ProjectProfitability, self).default_get(fields_list)
		vals = [(0, 0, {'project_id': self.id}),]
		res.update({'expenses_ids': vals})
		return res


	def _compute_total_project_hrs(self):
		for record in self:
			project_timesheet = self.env['account.analytic.line'].search([('project_id', '=', record.id)])
			employees = project_timesheet.mapped('employee_id')
			total_cost = 0
			for rec in employees:
				emp_timesheet = self.env['account.analytic.line'].search([('project_id', '=', record.id), ('employee_id', '=', rec.id)])
				total_hrs = sum(emp_timesheet.mapped('unit_amount'))
				emp_cost = total_hrs * rec.hourly_cost
				total_cost += emp_cost

			working_hours = sum(record.timesheet_ids.mapped('unit_amount'))
			expenses = sum(record.expenses_ids.mapped('amount'))
			record.total_hrs_spent = working_hours
			record.direct_cost = expenses
			record.time_cost = total_cost
			# if record.work_rate == 'hrs_basis':
			# 	record.time_cost = record.total_hrs_spent*record.per_hrs_charges
			# else:
			# 	record.time_cost = record.project_fix_amt_charges
			if record.work_rate_client_side == 'hrs_basis':
				record.gross_margin = record.project_hourly_revenue * record.total_hrs_spent - record.direct_cost 
			else:
				record.gross_margin = record.project_revenue - record.direct_cost 



class ProjectExpenses(models.Model):
	_name = 'project.expenses'
	_description = 'Project Expense'

	name = fields.Char(string="Description")
	amount = fields.Monetary(string="Amount")
	date = fields.Datetime(string="Date", default=date.today())
	currency_id = fields.Many2one(string="Currency", related='project_id.company_id.currency_id', readonly=True)
	project_id = fields.Many2one('project.project')
