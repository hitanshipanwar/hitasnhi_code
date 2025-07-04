from werkzeug import urls
from werkzeug.exceptions import NotFound, Forbidden

from odoo import http, _
from odoo.http import request
from odoo.osv import expression
from odoo.tools import consteq, plaintext2html
from odoo.addons.mail.controllers import mail
from odoo.addons.portal.controllers.portal import CustomerPortal
from odoo.exceptions import AccessError, MissingError, UserError
from odoo.addons.portal.controllers.mail import PortalChatter


def _check_special_access(res_model, res_id, token='', _hash='', pid=False):
	record = request.env[res_model].browse(res_id).sudo()
	if token:  # Token Case: token is the global one of the document
		token_field = request.env[res_model]._mail_post_token_field
		return (token and record and consteq(record[token_field], token))
	elif _hash and pid:  # Signed Token Case: hash implies token is signed by partner pid
		return consteq(_hash, record._sign_token(pid))
	else:
		raise Forbidden()

class PortalChatterCustomer(PortalChatter):

	@http.route('/mail/chatter_fetch', type='json', auth='public', website=True)
	def portal_message_fetch(self, res_model, res_id, domain=False, limit=10, offset=0, **kw):
		if not domain:
			domain = []
		# Only search into website_message_ids, so apply the same domain to perform only one search
		# extract domain from the 'website_message_ids' field
		model = request.env[res_model]
		field = model._fields['website_message_ids']
		record = request.env[res_model].browse(res_id).sudo()
		field_domain = field.get_domain_list(model)
		partners = []
		for mail in record.website_message_ids:
			if record.partner_id in mail.partner_ids:
				partners.append(record.partner_id.id)

		domain = expression.AND([domain, field_domain, [('res_id', '=', res_id), '|',('author_id','=',record.partner_id.id),('partner_ids', 'in', partners)]])
		# Check access
		Message = request.env['mail.message']
		if kw.get('token'):
			access_as_sudo = _check_special_access(res_model, res_id, token=kw.get('token'))
			if not access_as_sudo:  # if token is not correct, raise Forbidden
				raise Forbidden()
			# Non-employee see only messages with not internal subtype (aka, no internal logs)
			if not request.env['res.users'].has_group('base.group_user'):
				domain = expression.AND([Message._get_search_domain_share(), domain])
			Message = request.env['mail.message'].sudo()
		return {
			'messages': Message.search(domain, limit=limit, offset=offset).portal_message_format(),
			'message_count': Message.search_count(domain)
		}
