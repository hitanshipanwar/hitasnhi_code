from odoo import api, models, fields


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'
    
    next_timeout = fields.Float(string="Session Timeout (Hours)", config_parameter='next_timeout', default=98)
    timeout_msg = fields.Char(string="Timeout Message", config_parameter='timeout_msg', default="Your Odoo session expired. The current page is about to be refreshed.")
    