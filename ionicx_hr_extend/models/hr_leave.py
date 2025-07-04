# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.http import content_disposition, Controller, request, route
from datetime import datetime, date, time
from odoo.addons.base.models.res_partner import _tz_get
from odoo.addons.resource.models.resource import float_to_time, HOURS_PER_DAY
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tools import float_compare, format_date
from odoo.tools.float_utils import float_round
from odoo.tools.misc import format_date
from odoo.tools.translate import _
from odoo.osv import expression


class HRLeave(models.Model):
	_inherit = 'hr.leave'

	is_overlape_leave = fields.Boolean(string="Is Overlap Leave")

	# @api.depends('date_from', 'date_to', 'employee_id')
	# def _check_overlape_leave(self):
	# 	print("=========================================")
	# 	# if self.env.context.get('leave_skip_date_check', False):
	# 	# 	return

	# 	all_employees = self.employee_id | self.employee_ids
	# 	all_leaves = self.search([
	# 		('date_from', '<', max(self.mapped('date_to'))),
	# 		('date_to', '>', min(self.mapped('date_from'))),
	# 		('employee_id', 'in', all_employees.ids),
	# 		('id', 'not in', self.ids),
	# 		('state', 'not in', ['cancel', 'refuse']),
	# 	])
	# 	print("=====================================", all_leaves)
	# 	if all_leaves:
	# 		for leave in all_leaves:
	# 			leave.is_overlape_leave = True

	

	@api.constrains('date_from', 'date_to', 'employee_id')
	def _check_date(self):
		if self.env.context.get('leave_skip_date_check', False):
			return

		ov_all_employees = self.employee_id | self.employee_ids
		ov_all_leaves = self.search([
			('date_from', '<', max(self.mapped('date_to'))),
			('date_to', '>', min(self.mapped('date_from'))),
			('employee_id', 'in', ov_all_employees.ids),
			('id', 'not in', self.ids),
			('state', 'not in', ['cancel', 'refuse']),
		])
		if ov_all_leaves:
			for leave in ov_all_leaves:
				leave.is_overlape_leave = True


		all_employees = self.employee_id | self.employee_ids
		all_leaves = self.search([
			('date_from', '<', max(self.mapped('date_to'))),
			('date_to', '>', min(self.mapped('date_from'))),
			('employee_id', 'in', all_employees.ids),
			('id', 'not in', self.ids),
			('is_overlape_leave', '=', True),
			('state', 'not in', ['cancel', 'refuse']),
		])
		for holiday in self:
			domain = [
				('date_from', '<', holiday.date_to),
				('date_to', '>', holiday.date_from),
				('id', '!=', holiday.id),
				('is_overlape_leave', '=', False),
				('state', 'not in', ['cancel', 'refuse']),
			]

			employee_ids = (holiday.employee_id | holiday.employee_ids).ids
			search_domain = domain + [('employee_id', 'in', employee_ids)]
			conflicting_holidays = all_leaves.filtered_domain(search_domain)

			if conflicting_holidays:
				conflicting_holidays_list = []
				# Do not display the name of the employee if the conflicting holidays have an employee_id.user_id equivalent to the user id
				holidays_only_have_uid = bool(holiday.employee_id)
				holiday_states = dict(conflicting_holidays.fields_get(allfields=['state'])['state']['selection'])
				for conflicting_holiday in conflicting_holidays:
					conflicting_holiday_data = {}
					conflicting_holiday_data['employee_name'] = conflicting_holiday.employee_id.name
					conflicting_holiday_data['date_from'] = format_date(self.env, min(conflicting_holiday.mapped('date_from')))
					conflicting_holiday_data['date_to'] = format_date(self.env, min(conflicting_holiday.mapped('date_to')))
					conflicting_holiday_data['state'] = holiday_states[conflicting_holiday.state]
					if conflicting_holiday.employee_id.user_id.id != self.env.uid:
						holidays_only_have_uid = False
					if conflicting_holiday_data not in conflicting_holidays_list:
						conflicting_holidays_list.append(conflicting_holiday_data)
				if not conflicting_holidays_list:
					return
				conflicting_holidays_strings = []
				if holidays_only_have_uid:
					for conflicting_holiday_data in conflicting_holidays_list:
						conflicting_holidays_string = _('From %(date_from)s To %(date_to)s - %(state)s',
														date_from=conflicting_holiday_data['date_from'],
														date_to=conflicting_holiday_data['date_to'],
														state=conflicting_holiday_data['state'])
						conflicting_holidays_strings.append(conflicting_holidays_string)
					raise ValidationError(_('You can not set two time off that overlap on the same day.\nExisting time off:\n%s') %
										  ('\n'.join(conflicting_holidays_strings)))
				for conflicting_holiday_data in conflicting_holidays_list:
					conflicting_holidays_string = _('%(employee_name)s - From %(date_from)s To %(date_to)s - %(state)s',
													employee_name=conflicting_holiday_data['employee_name'],
													date_from=conflicting_holiday_data['date_from'],
													date_to=conflicting_holiday_data['date_to'],
													state=conflicting_holiday_data['state'])
					conflicting_holidays_strings.append(conflicting_holidays_string)
				conflicting_employees = set(employee_ids) - set(conflicting_holidays.employee_id.ids)
				# Only one employee has a conflicting holiday
				if len(conflicting_employees) == len(employee_ids) - 1:
					raise ValidationError(_('You can not set two time off that overlap on the same day for the same employee.\nExisting time off:\n%s') %
										  ('\n'.join(conflicting_holidays_strings)))
				raise ValidationError(_('You can not set two time off that overlap on the same day for the same employees.\nExisting time off:\n%s') %
									  ('\n'.join(conflicting_holidays_strings)))