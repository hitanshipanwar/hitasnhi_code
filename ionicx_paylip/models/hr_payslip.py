# -*- coding: utf-8 -*-

from odoo import _, api, fields, models, tools
from odoo.exceptions import AccessError

from io import BytesIO
from PyPDF2 import PdfFileWriter, PdfFileReader

class ResUsers(models.Model):
	_inherit = 'res.users'

	is_payslip_admin = fields.Boolean('Is Payslip Admin')
	
class HrEmployee(models.Model):
	_inherit = 'hr.employee'

	password = fields.Boolean("Set Password")
	password_name = fields.Char("Password")

class HrEmployeePublic(models.Model):
	_inherit = 'hr.employee.public'

	password = fields.Boolean("Set Password")
	password_name = fields.Char("Password")

class MyWeb(models.Model):
	_name = 'payslip.payslip'
	_description = 'Payslip'

	name = fields.Char(string="Name")
	employee_id = fields.Many2one('res.users', string="Employee")
	hr_employee = fields.Many2one('hr.employee', string="Employee", related="employee_id.employee_id")
	months = fields.Selection(selection=([('jan', 'January'),('feb', 'February'),
							('mar', 'March'),('april', 'April'),
							('may', 'May'),('june', 'June'),
							('july', 'July'),('aug', 'August'),
							('sep', 'September'),('oct', 'October'),
							('nov', 'November'),('dec', 'December'),]), string="Month")
	year = fields.Char(string="Year", limit=4)
	designation = fields.Char(string="Designation")
	emp_id = fields.Char(string="Employee ID")
	department = fields.Char(string="Department")
	basic_salary = fields.Float(string="Basic Salary")
	hra = fields.Float(string="HRA")
	conveyance = fields.Float(string="Conveyance")
	medical = fields.Float(string="Medical")
	special_allowance = fields.Float(string="Special Allowancne")
	earning_epf = fields.Float(string="Employer Contribution to Provident Fund")
	others = fields.Float(string="Others")
	total_earning = fields.Float(string="Total Earnings")
	# total_earning = fields.Float(string="Total Earnings", compute="_compute_total_pays")
	deduct_employer_pf = fields.Float(string="Employer Contribution to Provident Fund")
	deduct_employee_pf = fields.Float(string="Employee Contribution to Provident Fund")
	esi = fields.Float(string="ESI")
	professional_tax = fields.Float(string="Professional Tax")
	tds = fields.Float(string="TDS")
	advance = fields.Float(string="Advance")
	leave_deduct = fields.Float(string="Leave Deductions")
	deduct_total = fields.Float(string="Deductions Total")
	# deduct_total = fields.Float(string="Deductions Total", compute="_compute_total_pays")
	net_pay = fields.Float(string="Net Pay")
	# net_pay = fields.Float(string="Net Pay", compute="_compute_total_pays")
	password = fields.Boolean("Set Password", related="hr_employee.password")
	password_name = fields.Char("Password", related="hr_employee.password_name")
	company_id = fields.Many2one('res.company','Company', related="hr_employee.company_id")

	# def _compute_total_pays(self):
	# 	print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
	# 	self.total_earning = self.basic_salary + self.hra + self.conveyance + self.medical + self.special_allowance + self.earning_epf + self.others
	# 	self.deduct_total = self.deduct_employer_pf + self.deduct_employee_pf + self.esi + self.professional_tax + self.tds + self.advance + self.leave_deduct
	# 	self.net_pay = self.total_earning - self.deduct_total

	def print_payslip_pdf_report(self):
		name = self.env['payslip.payslip'].search([])
		return self.env.ref('ionicx_paylip.action_payslip_report').report_action(name)

	def _get_report_base_filename(self):
		return self.name


class IrActionsReportInherit(models.Model):
	_inherit = 'ir.actions.report'

	password = fields.Boolean("Set Password?")
	password_name = fields.Char("Password")

	# Write Password on generated PDF based on configuration.
	def encrypt_pdf(self, pdf_data, password):
		pdf_buffer = BytesIO(pdf_data)
		pdf_reader = PdfFileReader(pdf_buffer)
		pdf_writer = PdfFileWriter()
		pdf_writer.appendPagesFromReader(pdf_reader)
		if password:
		# if self.password:
			pdf_writer.encrypt(user_pwd=password, owner_pwd=None, use_128bit=True)
		pdf_buffer_enc = BytesIO()
		pdf_writer.write(pdf_buffer_enc)
		pdf_buffer_enc.seek(0)
		return pdf_buffer_enc.read()


class ResCompany(models.Model):
	_inherit = 'res.company'

	signature = fields.Html(string="Signature")
	seal = fields.Html(string="Company Seal")