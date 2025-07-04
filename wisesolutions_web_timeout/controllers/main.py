from odoo import http
from odoo.http import request


class SessionTimeoutController(http.Controller):
    @http.route(['/crash_manager/message'], type='json', auth="public")
    def get_attribute_notes(self):
        msg = request.env['ir.config_parameter'].sudo().get_param('timeout_msg')
        return msg
