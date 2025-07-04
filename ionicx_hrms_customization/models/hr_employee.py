from odoo import models, fields, api
from datetime import datetime, date,timedelta


class HrEmployee(models.Model):
	_inherit = 'hr.employee'

	send_timesheet_date = fields.Date(string="Send Timesheet Date")

	# CRON FUNCTION THAT CHECK EMAPLOYEES TIMESHEET
	# @api.model
	def check_employee_timesheet(self):
		day_no = datetime.today().weekday()
		current_date = datetime.now().date()
		start_date = datetime(current_date.year, current_date.month, 1).date()
		day_count = (current_date - start_date).days + 1
		if day_no < 5:
			employees = self.search([])
			for employee in employees:
				total_effort = 0
				check_timesheet = True
				if not employee.user_id.has_group('hr_timesheet.group_timesheet_manager'):
					if employee.send_timesheet_date and employee.send_timesheet_date == date.today():
						check_timesheet = False
					if employee.user_id and employee.work_email and check_timesheet:
						# Check Employee Timesheet
						emp_timesheet = self.env['account.analytic.line'].sudo().search([('employee_id','=',employee.id),('date','=',date.today())])
						if emp_timesheet:
							total_effort = sum(emp_timesheet.mapped('unit_amount'))
						if total_effort < 8:
							miss_eff_data = 0
							ctx = {}
							db = self.env.cr.dbname
							base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
							action_id = self.env.ref('hr_timesheet.act_hr_timesheet_line').id
							menu_id = self.env.ref('hr_timesheet.timesheet_menu_root').id
							ctx['action_url'] = "{}/web?db={}#action={}&model=account.analytic.line&view_type=list&menu_id={}".format(
								base_url, db, action_id, menu_id)
							ctx['total_effort'] = '%.2f'%total_effort
							miss_eff_data = 7.60 - total_effort if (total_effort - int(total_effort) !=0 ) else (8 - total_effort)
							ctx['missing_effort'] = '%.2f'%miss_eff_data
							# Data Preparation
							missing_datas = []
							for single_date in [d for d in (start_date + timedelta(n) for n in range(day_count)) if
												d <= current_date]:
								if single_date.weekday() < 5:
									missing_total_effort = 0
									missing_emp_timesheet = self.env['account.analytic.line'].sudo().search(
										[('employee_id', '=', employee.id), ('date', '=', single_date)])
									if missing_emp_timesheet:
										missing_total_effort = sum(missing_emp_timesheet.mapped('unit_amount'))
									if missing_total_effort < 8:
										missing_efforts = 8 - missing_total_effort
										missing_dic = {
											'date' : str(single_date) + ' / ' + str(single_date.strftime("%A")),
											'total_effort' :  '{0:02.0f}:{1:02.0f}'.format(*divmod(missing_total_effort * 60, 60)),
											'missing_effort' : '{0:02.0f}:{1:02.0f}'.format(*divmod(missing_efforts * 60, 60)),
										}
										missing_datas.append(missing_dic)
							ctx['missing_datas'] = missing_datas
							# Send Email Alert
							mail_template = self.env.ref('ionicx_hrms_customization.update_email_template')
							employee.sudo().write({
								'send_timesheet_date': date.today()
								})
							self.env.cr.commit()
							mail_template.with_context(ctx).sudo().send_mail(employee.id, force_send=True, email_values={
								'email_to': employee.work_email})

class EmployeePublic(models.Model):
	_inherit = 'hr.employee.public'

	send_timesheet_date = fields.Date(string="Send Timesheet Date")