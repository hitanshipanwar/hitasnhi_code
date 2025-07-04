from datetime import date, datetime
from odoo import api, models, fields
from odoo.tools.misc import clean_context


class MailActivityInherit(models.Model):
	_inherit = "mail.activity"

	@api.model
	def _default_mail_activity_type_id(self):
		ActivityType = self.env["mail.activity.type"]
		activity_type_todo = self.env.ref('mail.mail_activity_data_todo', raise_if_not_found=False)
		activity_data_call = self.env.ref('mail.mail_activity_data_call', raise_if_not_found=False)

		default_vals = self.default_get(['res_model_id', 'res_model'])
		if not default_vals.get('res_model_id'):
			return ActivityType
		current_model_id = default_vals['res_model_id']
		current_model = self.env["ir.model"].sudo().browse(current_model_id)

		# Set Default Activity Type as CALL only for "Contact" and "Lead/Opportunity" Other models set default as 'To DO'
		if default_vals.get('res_model') in ['res.partner', 'crm.lead']:
			if activity_data_call and activity_data_call.active and \
					(activity_data_call.res_model == current_model.model or not activity_data_call.res_model):
				return activity_data_call

		if activity_type_todo and activity_type_todo.active and \
				(activity_type_todo.res_model == current_model.model or not activity_type_todo.res_model):
			return activity_type_todo
		activity_type_model = ActivityType.search([('res_model', '=', current_model.model)], limit=1)
		if activity_type_model:
			return activity_type_model
		activity_type_generic = ActivityType.search([('res_model', '=', False)], limit=1)
		return activity_type_generic

	partner_activity_history_id = fields.Many2one('partner.activity.history', string="Partner Activity History")

	activity_type_id = fields.Many2one(
		'mail.activity.type', string='Activity Type',
		domain="['|', ('res_model', '=', False), ('res_model', '=', res_model)]", ondelete='restrict',
		default=_default_mail_activity_type_id)

	def action_feedback(self, feedback=False, attachment_ids=None):
		self = self.with_context(clean_context(self.env.context))
		messages, next_activities = self.with_context(feedback=True)._action_done(feedback=feedback,
																				  attachment_ids=attachment_ids)
		return messages.ids and messages.ids[0] or False

	def action_done(self):
		if self.partner_activity_history_id:
			self.partner_activity_history_id.date_completed = date.today()
		return super(MailActivityInherit, self).action_done()

	def _action_done(self, feedback=False, attachment_ids=None):
		if self.partner_activity_history_id:
			self.partner_activity_history_id.feedback = feedback
			if feedback:
				self.partner_activity_history_id.note = feedback
			self.partner_activity_history_id.date_completed = date.today()
		return super(MailActivityInherit, self)._action_done(feedback=feedback, attachment_ids=attachment_ids)

	def unlink(self):
		# This is for remove history on customer when activity Cancel
		for activity in self:
			if self._context.get('is_delete'):
				model_id = self.env['ir.model']._get('res.partner').id
				if activity.res_model_id.id == model_id:
					partner_activity_history_id = self.env['partner.activity.history'].search(
						[('activity_id', '=', activity.id)])
					if partner_activity_history_id:
						partner_activity_history_id.unlink()
		#     if not self._context.get('feedback'):
		#         model_id = self.env['ir.model']._get('res.partner').id
		#         if activity.res_model_id.id == model_id:
		#             partner_activity_history_id = self.env['partner.activity.history'].search(
		#                 [('activity_id', '=', activity.id)])
		#             if partner_activity_history_id:
		#                 partner_activity_history_id.unlink()
		return super(MailActivityInherit, self).unlink()

	@api.model
	def create(self, values):
		res = super(MailActivityInherit, self).create(values)

		if self._context.get('default_res_model') == 'res.partner' and self._context.get('default_res_id'):
			model = self._context.get('default_res_model')
			res_id = self._context.get('default_res_id')
			partner_id = self.env[model].browse(res_id)
			model_id = self.env['ir.model']._get(model).id

			activity_type_list = []
			complaint_or_error = self.env.ref('crm_history_module.mail_activity_type_demo_complaint_with_template')
			review_or_feedback = self.env.ref('crm_history_module.mail_activity_type_demo_review_with_template')
			attempted_contact = self.env.ref('crm_history_module.mail_activity_type_demo_attempt_contact_with_template')
			call = self.env.ref('mail.mail_activity_data_call')
			mail = self.env.ref('mail.mail_activity_data_email')
			meeting = self.env.ref('mail.mail_activity_data_meeting')

			if complaint_or_error:
				activity_type_list.append(complaint_or_error.id)
			if review_or_feedback:
				activity_type_list.append(review_or_feedback.id)
			if attempted_contact:
				activity_type_list.append(attempted_contact.id)
			if call:
				activity_type_list.append(call.id)
			if mail:
				activity_type_list.append(mail.id)
			if meeting:
				activity_type_list.append(meeting.id)

			if partner_id and res.activity_type_id.id in activity_type_list:
				activity_history_dict = {
					'res_model_id': model_id,
					'activity_type_id': res.activity_type_id.id,
					'summary': res.summary,
					'date_deadline': res.date_deadline,
					'note': res.note,
					'activity_id': res.id,
					'partner_id': partner_id.id
				}
				
				partner_activity_history_id = self.env['partner.activity.history'].with_context(is_import=False).create(activity_history_dict)
				res.partner_activity_history_id = partner_activity_history_id.id
				def add_data_on_parent(parent):
					parent.partner_activity_his_ids = [(4,partner_activity_history_id.id)]
					if parent.parent_id:
						if parent.parent_id.company_type == 'person':
							return add_data_on_parent(parent.parent_id)
						else:
							parent.parent_id.partner_activity_his_ids = [(4,partner_activity_history_id.id)]

 


				if partner_id and partner_activity_history_id:
					partner_id.partner_activity_his_ids = [(4, partner_activity_history_id.id)]
					if partner_id.parent_id:
						if partner_id.parent_id.company_type == 'person':
							add_data_on_parent(partner_id.parent_id)
						else:
							partner_id.parent_id.partner_activity_his_ids = [(4,partner_activity_history_id.id)]
				
		return res

	def write(self, values):
		model = self._context.get('default_res_model')
		res_id = self._context.get('default_res_id')

		if model == 'res.partner':
			partner_id = self.env[model].browse(res_id)

			if partner_id:
				activity_his_id = partner_id.partner_activity_his_ids.filtered(lambda r: r.activity_id.id == self.id)

				history = {}
				if 'activity_type_id' in values:
					history['activity_type_id'] = values.get('activity_type_id')

				if 'date_deadline' in values:
					history['date_deadline'] = values.get('date_deadline')

				if 'summary' in values:
					history['summary'] = values.get('summary')

				if 'note' in values:
					history['note'] = values.get('note')

				if 'user_id' in values:
					history['user_id'] = values.get('user_id')

				if history:
					activity_his_id.write(history)

		return super(MailActivityInherit, self).write(values)

class ResPartner(models.Model):
	_inherit = "res.partner"

	partner_activity_his_ids = fields.Many2many('partner.activity.history',
												'res_partner_partner_activity_history_rel', 'partner_id',
												'partner_activity_history_id', string="CRM History Page")

	old_partner_activity_his_ids = fields.Many2many('old.partner.activity.history',
												'old_res_partner_partner_activity_history_rel', 'old_partner_id',
												'old_partner_activity_history_id', string="OLD History Page")

	from_date = fields.Datetime(string="From Date", default=fields.datetime.now())


	# def action_get_crm_history(self):
	# 	print("self._contextffffffffffff",self._context)
	# 	for data in self:
	# 		model_id=self.env['ir.model'].search([('model', '=', 'res.partner')])
	# 		print("CCCCCCCCCCCCCCCCC",model_id)
	# 		print(data.id,"XXXXXXXXXXXXX",data.from_date)
	# 		activity_data=self.env['mail.activity'].search([('res_id', '=', data.id),('res_model_id','=',model_id.id)])
	# 		print("=================vbbb",activity_data)
	# 		for jk in activity_data:
	# 			print("Cvvvvvvvvvvvvvvv",jk.note)

	def action_get_crm_history(self):
		self.ensure_one()
		# self.partner_activity_his_ids.unlink()
		# history.unlink() for history in self.partner_activity_his_ids.filtered(lambda a : a.is_import == False)
		datas = self.partner_activity_his_ids.filtered(lambda a :not a.is_import)
		print('DATASSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSS',datas)
		
		datas.unlink()
		model = self._context.get('default_res_model')
		model_id = self.env['ir.model']._get(model).id
		for rec in self:
			current_activity = self.env['mail.activity'].search([('res_id', '=', rec.id),('res_model', '=', 'res.partner')])
			print('////////////current_activity.res_id/////////////////////////////////////',current_activity.res_id, type(current_activity.res_id))
			print('QQQQQQQQQQQQQQQQQQQQQQQQQQQ',current_activity)
			old_activity = self.env['mail.message'].search([('date','>=','01/07/2022'),('res_id', '=', rec.id),('model','=', 'res.partner')])
			# old_activity = self.env['mail.message'].search([('date','>=','01/01/2022'),('res_id', '=', rec.id),('model','=', 'res.partner')])
			print('!!!old_activity!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!',old_activity)
			activities_list = []
			activities_list = current_activity.ids + old_activity.ids
			print('listttttttttttttttttttttttttttttttt',activities_list)
			activities = []
			# self.partner_activity_his_ids = []
			if old_activity:
				for activity in old_activity:
					if activity.date >= rec.from_date:
						print('##############################',activity)
						activities.append((0,0, {
							'date_deadline': activity.date,
							'summary': activity.description or '',
							'note': activity.subtype_id.name,
							'date_completed': activity.date,
							'partner_id': activity.res_id,
							'mail_message_id': activity.id,
							'user_id': activity.create_uid.id,
							'is_import': False,
							}))
						print('---------------------------------',activity)
						print('---------------------------------',activity.body)
						print('---------------------------------',activity)
				print('***activity_data***********************************',activities)
				# rec.partner_activity_his_ids.with_context(is_import=False) = activities
				rec.with_context(is_import=False).partner_activity_his_ids = activities
			else:
				rec.partner_activity_his_ids = []

			activities = []
			if current_activity:
				for activity in current_activity:
					activities.append((0,0, {
						'date_deadline': activity.date_deadline,
						'summary': activity.summary or '',
						'note': activity.note,
						'date_completed': activity.create_date,
						# 'partner_id': activity.res_name,
						'partner_id': activity.res_id,
						'mail_message_id': activity.id,
						'user_id': activity.user_id.id,
						'is_import': False,						}))
					print('---------------------------------',activity)
					# print('---------------------------------',activity.body)
					# print('---------------------------------',activity)
				print('***activity_data***********************************',activities)
				rec.with_context(is_import=False).partner_activity_his_ids = activities
			else:
				rec.partner_activity_his_ids = []



	# def _compute_partner_activity_history(self):
	# 	# if self._context.get('default_res_model') == 'res.partner' and self._context.get('default_res_id'):
	# 	model = self._context.get('default_res_model')
	# 		# res_id = self._context.get('default_res_id')
	# 		# partner_id = self.env[model].browse(res_id)
	# 	model_id = self.env['ir.model']._get(model).id
	# 	# res = super(ResPartner, self)
	# 	print('!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!\n\n\n\n\n')
	# 	# self.old_partner_activity_his_ids = []
	# 	for rec in self:
	# 		activity_data = self.env['mail.message'].search([('date','>=','01/07/2022'),('res_id', '=', rec.id),('model','=', 'res.partner')])
	# 		# activity_data = self.env['mail.message'].search([('date','>=','01/07/2022')], limit= 5)
	# 		print('-----------------------------@@@@@@@@@@@@@@@@@@@@@@@@@@@',activity_data)
	# 		activites = [] 
	# 		# data=[]
	# 		# data.append((0,0, {
	# 		# 	'manager_signature':self.digital_signature,
	# 		# 	'manager_name' : manager_name,
	# 		# 	'manager_signed_on': fields.Datetime.now(),
	# 		# 	'state': 'rejected',
	# 		# 	}))
	# 		# activites = {} 
	# 		print('---------------------------------------------------------------------------------------',activity_data)
	# 		for activity in activity_data:
	# 			activites.append((0,0, {
	# 				'date_deadline': activity.date,
	# 				'summary': activity.subject,
	# 				'note': activity.subtype_id.name,
	# 				'date_completed': activity.date,
	# 				# 'date_completed': activity.__last_update,
	# 				'partner_id': activity.author_id.id,
	# 				# 'partner_id': activity.record_name,
	# 				'mail_message_id': activity.id,
	# 				'user_id': activity.create_uid.id,
	# 				}))
	# 			# rec.write({'old_partner_activity_his_ids':activites})
	# 			# activites.append(activity.id)
	# 			# rec.old_partner_activity_his_ids = [(0,0,{
	# 					# 'res_model_id': model_id,
	# 					# 'activity_type_id': activity.message_type,
	# 					# 'summary': activity.summary,
	# 					# 'date_deadline': activity.date,
	# 					# 'note': activity.subtype_id.id,
	# 					# 'activity_id': activity.id,
	# 					# 'partner_id': partner_id.id
	# 				# })]
	# 		print('------------------------------',activites)
	# 		rec.old_partner_activity_his_ids = activites
	# 			# rec.old_partner_activity_his_ids = [(4, x, None) for x in activites]
	# 				# rec.old_partner_activity_his_ids = [(4,activity.id)]

	# 				# activites. ({(6,0,)})
	# 				# activites.append((0,0,{
	# 				#     'date_completed': activity.date
	# 				#     }))
	# 				# activites.append((4,activity.id))
	# 			# print('*****************************************',activites)
	# 				# rec.old_partner_activity_his_ids = activites
	# 			# print('==============================================',activity.date)
	# 			# print('==============================================',activity)
	# 			# print('==============================================',activity.id)
	# 			# rec.write({'old_partner_activity_his_ids':  activites})


	# def _inverse_activity_history(self):
	# 	print('Hitanshiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiii')
	# 	model = self._context.get('default_res_model')
	# 	model_id = self.env['ir.model']._get(model).id

	# 	for rec in self:
	# 		# activity_data = self.env['mail.message'].search([('date','>=','01/07/2022'),('id', '=', rec.old_partner_activity_his_ids.id),('model','=', 'res.partner')])
	# 		activity_data = self.env['mail.message'].search([('date','>=','01/07/2022'),('res_id', '=', rec.id),('model','=', 'res.partner')])
	# 		# activity_data = self.env['mail.message'].search([('date','>=','01/07/2022')], limit= 5)
	# 		print('///////////////////////////////////////////',rec.old_partner_activity_his_ids.mail_message_id)
	# 		print('*********************************************************',activity_data)
	# 		# print('@@@@@@@@@@@@@@@@@@@@@@@@@@@@@',rec.old_partner_activity_his_ids.summary)
	# 		activites = []

	# 		for activity in activity_data:
	# 			print('-----------------------wwwwwwwww-----------------',activity)
	# 			for activites_rec in rec.old_partner_activity_his_ids:
	# 				print('--------------------ggggggggggggg---------------',activites_rec)
	# 				if activites_rec.mail_message_id.id == activity.id:
	# 					print("Summary Sunen------------------------- ", activites_rec.summary)
	# 					upd_subject = activites_rec.summary
	# 					# upd_date = activites_rec.date_completed + time.strftime.now('%H:%M:%S')
	# 					# print('======================////////////////////////////////////',upd_date)
	# 					upd_partner = activites_rec.partner_id.id
	# 					# upd_note = activites_rec.note
	# 					upd_user = activites_rec.user_id.id

	# 					print('!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!',upd_subject)
	# 					# sql = "update mail_message set subject='"+str(activites_rec.summary)+"' where model = 'res.partner' and res_id = '"+str(self.id)+"'"
	# 				# 	sql = "update mail_message set subject='"+str(activites_rec.summary)+"' where model = 'old.partner.activity.history' and res_id = '"+str(activites_rec.mail_message_id.id)+"'"
	# 				# 	print('*********************************************************',sql)
	# 				# self._cr.execute(sql)
	# 				# self._cr.commit()

	# 					sql = "update mail_message set subject='"+str(upd_subject)+"', create_uid='"+str(upd_user)+"'  where model = 'res.partner' and res_id="+str(self.id)+" and id="+str(activity.id)+";"
	# 					print('*************************************************************',sql)
	# 					self._cr.execute(sql)
	# 					self._cr.commit()

	# 					# self.env.cr.execute(" UPDATE mail_message set subject = %s where res_model = 'res.partner' and res_id = %s
	# 					# 	")% (activites_rec.summary,self.id)
	# 					# activity.sudo().write({
	# 					# 	# 'activity.subtype_id': activites_rec.note
	# 					# 	})

	# 					# print('@@@@@@@@@@@@@@@@@@@@@@@@@@@@@',activites_rec.summary)
	# 					# print('@@@@@@@@@@@@@@@@@@@@@@@@@@@@@',rec.old_partner_activity_his_ids.summary)
	# 			# activity.date = rec.old_partner_activity_his_ids.date_deadline
	# 			# activity.subject = rec.old_partner_activity_his_ids.summary
	# 			# activites.append((0,0, {
	# 			# 	'activity.date' : rec.old_partner_activity_his_ids.date_deadline,
	# 			# 	'activity.subject': rec.old_partner_activity_his_ids.summary

	# 				# 'date_deadline': activity.date,
	# 				# 'summary': activity.subject,
	# 				# 'note': activity.subtype_id.name,
	# 				# 'date_completed': activity.date,
	# 				# 'partner_id': activity.author_id.id
	# 				# }))

	# 	# print('------------------------------',activites)
	# 	# rec.old_partner_activity_his_ids = activites

	# 	# for rec in self:
	# 	# partner_activity = self.env['old.partner.activity.history'].search([('id','=', self.old_partner_activity_his_ids.id)])
	# 	# print('*****************************************************************',partner_activity)
	# 	# for p in partner_activity:
	# 	# 	rec.old_partner_activity_his_ids.summary = self.old_partner_activity_his_ids.summary


	# 	# print('-------------------------------------')
	# 	pass

	def open_record(self):
		return {
			'type': 'ir.actions.act_window', 
			'res_model': 'res.partner', 
			'name': 'Record name', 
			'view_type': 'form', 
			'view_mode': 'form', 
			'res_id': self.id, 
			'target': 'current', 
		}

class PartnerActivityHistory(models.Model):
	_name = "partner.activity.history"
	_description = "Partner Activity History"
	_order = 'date_deadline ASC'
	_rec_name = 'summary'

	@api.model
	def _default_activity_type_id(self):
		activity_type_call = self.env.ref('mail.mail_activity_data_call', raise_if_not_found=False)
		return activity_type_call.id

	partner_id = fields.Many2one('res.partner', string='Contact')
	activity_type_id = fields.Many2one(
		'mail.activity.type', string='Activity Type',
		domain="['|', ('res_model', '=', False), ('res_model', '=', res_model)]", ondelete='restrict',
		default=_default_activity_type_id)

	res_model_id = fields.Many2one('ir.model', 'Document Model', index=True, ondelete='cascade')
	res_model = fields.Char('Related Document Model', index=True, related='res_model_id.model', compute_sudo=True,
							store=True, readonly=True)
	date_deadline = fields.Date('Due Date', index=True, required=True, default=fields.Date.context_today)
	date_completed = fields.Date('Completed Date')
	summary = fields.Char('Summary')
	note = fields.Html('Note', sanitize_style=True)
	user_id = fields.Many2one('res.users', 'Assigned to', default=lambda self: self.env.user, index=True,
							  required=True)
	activity_id = fields.Many2one('mail.activity', string='Activity')
	feedback = fields.Char(string="Feedback")
	is_import = fields.Boolean(string='Is imported')
	mail_message_id = fields.Many2one('mail.message', string='Mail Message ID')


	@api.model
	def create(self, vals):
		res = super(PartnerActivityHistory, self).create(vals)
		if self._context.get('is_import') is None:
			print("ssssssssssssssssssssssssssssssssssss ", self._context.get('is_import'))
			res.is_import = True
			if res.partner_id:
				res.partner_id.partner_activity_his_ids = [(4, res.id)]   
				# res.partner_id.old_partner_activity_his_ids = [(4, res.id)]   
		else:
			res.is_import = False
			print('...................11111.............................',res.is_import)
		return res


class OldPartnerActivityHistory(models.Model):
	_name = "old.partner.activity.history"
	_description = "Partner Activity History"
	_order = 'date_deadline ASC'
	_rec_name = 'summary'

	@api.model
	def _default_activity_type_id(self):
		activity_type_call = self.env.ref('mail.mail_activity_data_call', raise_if_not_found=False)
		return activity_type_call.id

	partner_id = fields.Many2one('res.partner', string='Contact')
	activity_type_id = fields.Many2one(
		'mail.activity.type', string='Activity Type',
		domain="['|', ('res_model', '=', False), ('res_model', '=', res_model)]", ondelete='restrict',
		default=_default_activity_type_id)

	res_model_id = fields.Many2one('ir.model', 'Document Model', index=True, ondelete='cascade')
	res_model = fields.Char('Related Document Model', index=True, related='res_model_id.model', compute_sudo=True,
							store=True, readonly=True)
	date_deadline = fields.Date('Due Date', index=True, required=True, default=fields.Date.context_today)
	date_completed = fields.Date('Completed Date')
	summary = fields.Char('Summary')
	note = fields.Html('Note', sanitize_style=True)
	user_id = fields.Many2one('res.users', 'Assigned to', default=lambda self: self.env.user, index=True,
							  required=True)
	activity_id = fields.Many2one('mail.activity', string='Activity')
	feedback = fields.Char(string="Feedback")
	is_import = fields.Boolean(string='Is imported')
	mail_message_id = fields.Many2one('mail.message', string='Mail Message ID')