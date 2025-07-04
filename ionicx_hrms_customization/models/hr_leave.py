from odoo import models, fields, api
from datetime import datetime, date, timedelta
from odoo.exceptions import ValidationError
from datetime import datetime
from dateutil.relativedelta import relativedelta


class HrLeave(models.Model):
	_inherit = 'hr.leave'

	is_payable = fields.Boolean(string="Is payable")

	def _check_sick_leave_limit(self, vals):
		print("===================", vals)
		# if not 'manager_id' in vals:
		if not ('manager_id' in vals or 'first_approver_id' in vals or 'second_approver_id' in vals):
			print("================================")
			"""Helper function to check if the user has already applied for a sick leave in the current month."""
			leave_type_id = vals.get('holiday_status_id', self.holiday_status_id.id)
			leave_type = self.env['hr.leave.type'].browse(leave_type_id)
			print(">>>>>>>>>>>>>>>>>>>>>>>", leave_type)
			if leave_type:
				if leave_type.name.lower() in  ['sick time off', 'sick leave', 'sick']:
					employee_id = vals.get('employee_id', self.employee_id.id)
					date_from = vals.get('date_from', self.date_from)
					date_from = fields.Datetime.from_string(date_from)
					# Calculate start and end of the current month
					# start_of_month = date_from.replace(day=1)
					# end_of_month = (start_of_month + relativedelta(months=1)) - relativedelta(days=1)
					# Calculate start and end of the current Year
					start_of_year = date_from.replace(month=1, day=1)
					end_of_year = date_from.replace(month=12, day=31)
					# Check for existing sick leaves within the year
					existing_sick_leaves = self.env['hr.leave'].search([
						('employee_id', '=', employee_id),
						('holiday_status_id', '=', leave_type_id),
						('date_from', '>=', start_of_year),
						('date_to', '<=', end_of_year),
						('state', 'not in', ['cancel', 'refuse']),
						('id', '!=', self.id)  # Exclude the current record when editing
					])
					if len(existing_sick_leaves) > 12:
						raise ValidationError('You can only apply for up to 12 sick leaves in a year. Please select another leave type.')

	@api.model
	def create(self, vals):
		"""Override create method to validate sick leave limit."""
		self._check_sick_leave_limit(vals)
		return super(HrLeave, self).create(vals)

	def write(self, vals):
		"""Override write method to validate sick leave limit."""
		self._check_sick_leave_limit(vals)
		if 'employee_id' in vals and isinstance(vals['employee_id'], int):
			vals['employee_id'] = [vals['employee_id']]
		return super(HrLeave, self).write(vals)