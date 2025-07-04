from odoo import api, fields, models

class HREmployeeInherited(models.Model):
	_inherit = 'hr.employee'
	
	section_seleection = [
	('MARKETING','MARKETING'),
	('SUPPORT','SUPPORT'),
	('AUDIT','AUDIT'),
	('ACCOUNTING & FINANCE','ACCOUNTING & FINANCE'),
	('PURCHASING','PURCHASING'),
	('HR','HR'),
	('SAFETY','SAFETY'),
	('WAREHOUSE','WAREHOUSE'),
	('MAID','MAID'),
	('LOGISTIC','LOGISTIC'),
	('DESIGNER','DESIGNER'),
	('SALES','SALES'),
	('PRODUCTION','PRODUCTION'),
	('INSTALLATION','INSTALLATION'),
	('QUALITY CONTROL','QUALITY CONTROL'),
	('PLANNING','PLANNING'),
	]

	employee_number = fields.Char("Employeee Number")
	name_surname_thai = fields.Char("Name Thai") 
	section = fields.Selection(selection=section_seleection)
	start_date = fields.Date(string="Start Date")
	social_security_number = fields.Char(string="Social Security Number")
	nickname = fields.Char(string="Nick Name")
	passport_expiration_date = fields.Date("Passport Expiration Date")
	hospital_name = fields.Char("Hospital Name")