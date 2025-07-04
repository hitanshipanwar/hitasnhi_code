# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class PortalShare(models.TransientModel):
	_inherit = 'portal.share'
	_description = 'Portal Sharing'


	@api.model
	def _send_public_link(self, note, partners=None):
		context = self.env.context or {}
		if partners is None:
			partners = self.partner_ids
		for partner in partners:
			if context.get('share_design_link'):
				share_link = self.resource_ref.get_base_url() + "/my/kitchen/design/%s"%(self.resource_ref.id)
			else:
				share_link = self.resource_ref.get_base_url() + self.resource_ref._get_share_url(redirect=True, pid=partner.id)
			saved_lang = self.env.lang
			self = self.with_context(lang=partner.lang)
			template = self.env.ref('portal.portal_share_template', False)
			self.resource_ref.message_post_with_view(template,
				values={'partner': partner, 'note': self.note, 'record': self.resource_ref,
				'share_link': share_link},
				subject=_("You are invited to access %s", self.resource_ref.display_name),
				subtype_id=note.id,
				email_layout_xmlid='mail.mail_notification_light',
				partner_ids=[(6, 0, partner.ids)])
			self = self.with_context(lang=saved_lang)

	@api.model
	def default_get(self, fields):
		result = super(PortalShare, self).default_get(fields)
		result['res_model'] = self._context.get('active_model', False)
		result['res_id'] = self._context.get('active_id', False)
		context = self.env.context or {}
		if result['res_model'] and result['res_id']:
			record = self.env[result['res_model']].browse(result['res_id'])
			result['share_link'] = record.get_base_url() + record._get_share_url(redirect=True)
		if context.get('share_design_link'):
			record = self.env[result['res_model']].browse(result['res_id'])
			result['share_link'] = record.get_base_url() + "/my/kitchen/design/%s"%(record.id)
		return result

	@api.depends('res_model', 'res_id')
	def _compute_share_link(self):
		context = self.env.context or {}
		for rec in self:
			res = super(PortalShare,self)._compute_share_link()
			if context.get('share_design_link'):
				if rec.res_model:
					res_model = self.env[rec.res_model]
					if isinstance(res_model, self.pool['portal.mixin']) and rec.res_id:
						record = res_model.browse(rec.res_id)
						rec.share_link = record.get_base_url() + "/my/kitchen/design/%s"%(record.id)