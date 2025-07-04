# Part of Odoo. See LICENSE file for full copyright and licensing details.

from werkzeug.exceptions import NotFound

from odoo import _
from odoo import _, http
from odoo.exceptions import AccessError
from odoo.http import request, content_disposition
from odoo.addons.mail.controllers.attachment import AttachmentController
from odoo.exceptions import AccessError
from odoo.addons.mail.models.discuss.mail_guest import add_guest_to_context


class AttachementCo(AttachmentController):
    @http.route()
    @add_guest_to_context
    def mail_attachment_upload(self, ufile, thread_id, thread_model, is_pending=False, **kwargs):
        # user = request.env.user
        user = request.env[thread_model].sudo().search([('id', '=', thread_id)])
        if user:
            user.sudo().message_post(body="%s Add New Attachment." % (request.env.user.name))
        return super().mail_attachment_upload(ufile, thread_id, thread_model, is_pending, **kwargs)

    @http.route()
    @add_guest_to_context
    def mail_attachment_delete(self, attachment_id, access_token=None):
        attachment = request.env["ir.attachment"].browse(int(attachment_id))
        user = request.env[attachment.res_model].search([('id', '=', attachment.res_id)])
        if user:
            user.sudo().message_post(body="%s Delete Attachment." % (request.env.user.name))
        return super().mail_attachment_delete(attachment_id, access_token)
