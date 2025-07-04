# -*- coding: utf-8 -*-

from odoo import models, fields, api, _

class HrLeave(models.Model):
	_inherit = 'hr.leave'

	is_work_from_home_leave = fields.Boolean('Is Work From Home Leave', related="holiday_status_id.is_work_from_home_leave_type")


class HrLeaveType(models.Model):
	_inherit = 'hr.leave.type'

	is_work_from_home_leave_type = fields.Boolean('Is Work From Home Leave Type')