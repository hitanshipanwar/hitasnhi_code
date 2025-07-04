# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from datetime import datetime, date, time

class HrAttendance(models.Model):
	_inherit = 'hr.attendance'


	is_user = fields.Boolean(string="Is User", compute="_get_default_is_user")

	def _get_default_is_user(self):
		if self.env.user.has_group('hr_attendance.group_hr_attendance') and not self.env.user.has_group('hr_attendance.group_hr_attendance_manager'):
			self.is_user = True
		else:
			self.is_user = False