from odoo import _, api, exceptions, fields, models, tools, registry, SUPERUSER_ID, Command

class MailThreadInherit(models.AbstractModel):
	_inherit = "mail.thread"
	_description = "Email Thread"

	@api.returns('mail.message', lambda value: value.id)
	def message_post(self, **kwargs):
		message = super(MailThreadInherit, self).message_post(**kwargs)

		# channel_obj = self.env['mail.channel']
		notification_ids = []
		for partner in message.partner_ids:
			if partner not in message.notification_ids.res_partner_id:
				notification_ids.append((0,0,{
						'res_partner_id': partner.id,
						'notification_type': 'inbox'}))

		# message.notification_ids = notification_ids
		message.write({'notification_ids':notification_ids})
		# subtype_id = self.env.ref('mail.mt_comment').id

		# self.message_post(body=message.body, message_type='notification', subtype_id=subtype_id, author_id=self.env.user.partner_id.id, notification_ids=notification_ids)


		# message_id = self.env['mail.message'].sudo().create({
		# 	'message_type': 'notification',
		# 	'body': message.body,
		# 	'model': self._name,
		# 	'partner_ids': [message.partner_ids.ids],
		# 	'author_id': self.env.user.partner_id.id,
		# 	'notification_ids': notification_ids,
		# 	})

		# message = .message_post(partner_ids=self.partners.ids, subtype_xmlid='mail.mt_comment', message_type='notification')
		# 	for user in partner.user_ids:
		# 		ch_name = user.name+', '+self.env.user.name
		# 		ch = channel_obj.sudo().search([('name', 'ilike', str(ch_name))])
		# 		if not ch:
		# 			ch = channel_obj.sudo().search([('name', 'ilike', str(self.env.user.name+', '+user.name))])
		# 			if not ch:
		# 				ch = channel_obj.sudo().create({'name':str(ch_name)})
		# 		ch.message_post(attachment_ids=[],body=message.body,content_subtype='html',
  #                        message_type='comment',partner_ids=[],subtype_xmlid='mail.mt_comment',
  #                        email_from=self.env.user.partner_id.email,author_id=self.env.user.partner_id.id)

		return message