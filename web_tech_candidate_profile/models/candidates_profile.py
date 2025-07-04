# -*- coding: utf-8 -*-

from odoo import api, fields, models
from datetime import datetime, date, time

class CandidateProfile(models.Model):
	_name = 'candidate.profile'
	_inherit = ['mail.thread', 'mail.activity.mixin', 'utm.mixin']
	_description = 'Candidate Profile'


	def _get_default_stage_id(self):
		return self.env["candidate.profile.stage"].search([], limit=1).id

	@api.model
	def _read_group_stage_ids(self, stages, domain, order):
		stage_ids = self.env["candidate.profile.stage"].search([])
		return stage_ids

	name = fields.Char(string="Candidate Name")
	father_name = fields.Char(string="Father's Name")
	email = fields.Char(string="Email")
	contact = fields.Char(string="Contact")
	job_description = fields.Char(string="Job Description")
	day_month = fields.Selection(selection=[
		('day', 'Days'),
		('month', 'Months')], default='day', required=True)
	employement_type = fields.Selection(selection=[
		('permanent', 'Permanent'),
		('contract', 'Contract'),
		('freelance', 'Freelancer')])
	hours = fields.Float(string="Working Hours")
	joining_date = fields.Date(string="Date of Joining")
	probationary_period = fields.Float(string="Probationary Period")
	work_ex = fields.Float(string="Work Experiance")
	current_ctc = fields.Float(string="Current CTC")
	expectation = fields.Float(string="Eexpectation")
	current_company = fields.Char(string="Current Company")
	attachment_ids = fields.Many2many('ir.attachment','ir_attachment_candidated_ref','candidate_profile_id','attachment_id', string="Add Attchments")
	description = fields.Html(string="Description")
	# state = fields.Selection(selection=[
	# 	('pending', 'Pending'),
	# 	('in_process', 'In Process'),
	# 	('on_hold', 'On Hold'),
	# 	('running', 'Runing')], string="Status")
	stage_id = fields.Many2one(
		comodel_name="candidate.profile.stage",
		string="Stage",
		group_expand="_read_group_stage_ids",
		default=_get_default_stage_id,
		tracking=True,
		ondelete="restrict",
		index=True,
		copy=False,
	)
	is_running = fields.Boolean(string="Is Running", related="stage_id.is_running")
	is_closed = fields.Boolean(string="Is Closed", related="stage_id.is_closed")
	company_id = fields.Many2one('res.company', string="Company")


	def send_email_to_candidate(self):
		for rec in self:
			if rec.email:
				mail_template = self.env.ref('web_tech_candidate_profile.candidate_email_template')
				mail_template.sudo().send_mail(rec.id, force_send=True, email_values={
					'email_to': rec.email})


class CandidateProfileStages(models.Model):
	_name = 'candidate.profile.stage'
	_description = 'Candidate Profile Stage'

	name = fields.Char(string="Name")
	is_running = fields.Boolean(string="Is Running")
	is_closed = fields.Boolean(string="Is Closed")
