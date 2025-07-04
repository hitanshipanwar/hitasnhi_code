import logging
import os
from os import utime
from os.path import getmtime
from time import time

from odoo import http, models

_logger = logging.getLogger(__name__)

class ResUsers(models.Model):
    _inherit = "res.users"

    def check_timeout(self):
        if not http.request:
            return
        timeout = False
        next_timeout = float(self.env['ir.config_parameter'].sudo().get_param('next_timeout'))
        if next_timeout == 0:
            next_timeout = 24
        session = http.request.session
        path = http.root.session_store.get_session_filename(session.sid)
        session_store = http.root.session_store
        for fname in os.listdir(session_store.path):
            path = os.path.join(session_store.path, fname)
            try:
                timeout = getmtime(path) < time() - 60*60*next_timeout
            except OSError:
                timeout = True
        if "/longpolling/im_status" != http.request.httprequest.path:
            try:
                utime(path, None)
            except OSError:
                _logger.exception(
                    "Exception updating session file access/modified times.",
                )
        if timeout:
            session.logout(keep_db=True)
