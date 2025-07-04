from odoo import models
from odoo.http import request


class IrHttp(models.AbstractModel):
    _inherit = 'ir.http'

    @classmethod
    def _authenticate(cls, endpoint):
        auth_method = endpoint.routing["auth"]
        if auth_method == "user" and request and request.env and request.env.user:
            request.env.user.check_timeout()
        return super(IrHttp, cls)._authenticate(endpoint=endpoint)
