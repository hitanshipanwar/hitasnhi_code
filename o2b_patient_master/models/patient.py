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

class AccountMove(models.Model):
	_name = 'patient.patient'
	_description = 'Patient Master'
	_inherit = ['mail.thread.main.attachment', 'mail.activity.mixin']

	name = fields.Char(index=True, default_export_compatible=True)
	child_ids = fields.One2many('patient.patient', 'parent_id', string='Patient')
	# child_ids = fields.One2many('patient.patient', 'parent_id', string='Patient', domain=[('active', '=', True)])
	parent_id = fields.Many2one('patient.patient', string='Patient', index=True)
	street = fields.Char()
	street2 = fields.Char()
	zip = fields.Char(change_default=True)
	city = fields.Char()
	state_id = fields.Many2one("res.country.state", string='State', ondelete='restrict', domain="[('country_id', '=?', country_id)]")
	country_id = fields.Many2one('res.country', string='Country', ondelete='restrict')
	country_code = fields.Char(related='country_id.code', string="Country Code")
	phone = fields.Char(unaccent=False)
	mobile = fields.Char(unaccent=False)
	email = fields.Char()
	vat = fields.Char(string='SSN', index=True, help="The Tax Identification Number. Values here will be validated based on the country format. You can use '/' to indicate that the patient is not subject to tax.")
	category_id = fields.Many2many('patient.category', column1='patient_id',
									column2='category_id', string='Tags')
	comment = fields.Html(string='Notes')
	color = fields.Integer(string='Color Index', default=0)
	image = fields.Binary()

	show_data = fields.Boolean(string="Show Data")
	hide_data = fields.Boolean(string="Hide Data", default=True)
	to_unmask_data = fields.Boolean(
		string="Un-Mask Data",
		compute='_compute_to_unmask_data',
	)

	def _compute_to_unmask_data(self):
		current_user = self.env.user
		self.to_unmask_data = current_user.to_unmask_data
	
	def action_view_data(self):
		for rec in self:
			rec.show_data = True
			rec.hide_data = False

	def action_hide_data(self):
		for rec in self:
			rec.hide_data = True
			rec.show_data = False

	def action_view_appointments(self):
		pass

	def action_view_prescriptions(self):
		pass

	def action_view_vaccines(self):
		pass

	def action_view_admissions(self):
		pass

	def action_view_lab_test(self):
		pass

	def action_view_invoice(self):
		pass

class PatientCategory(models.Model):
	_name = 'patient.category'
	_description = 'Patient Tags'
	
	name = fields.Char(string='Tag Name', required=True, translate=True)