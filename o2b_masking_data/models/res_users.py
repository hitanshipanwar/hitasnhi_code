# -*- coding: utf-8 -*-
##########################################################################
# Author      : O2b Technologies Pvt. Ltd.(<www.o2btechnologies.com>)
# Copyright(c): 2016-Present O2b Technologies Pvt. Ltd.
# All Rights Reserved.
#
# This program is copyright property of the author mentioned above.
# You can`t redistribute it and/or modify it.
#
##########################################################################
from odoo import api, fields, models, _, exceptions

class ResUsers(models.Model):
	_inherit = 'res.users'

	to_unmask_data = fields.Boolean(string="Un-Mask Data", tracking=True)
# 	pin_unmask_data = fields.Char(string="Password")


# class Patient(models.Model):
# 	_inherit = 'patient.patient'

# 	show_data = fields.Boolean(string="Show Data")
# 	hide_data = fields.Boolean(string="Hide Data", default=True)
# 	to_unmask_data = fields.Boolean(
# 		string="Un-Mask Data",
# 		compute='_compute_to_unmask_data',
# 	)

# 	def _compute_to_unmask_data(self):
# 		current_user = self.env.user
# 		self.to_unmask_data = current_user.to_unmask_data
		
# 	def action_view_data(self):
# 		for rec in self:
# 			rec.show_data = True
# 			rec.hide_data = False

# 	def action_hide_data(self):
# 		for rec in self:
# 			rec.hide_data = True
# 			rec.show_data = False