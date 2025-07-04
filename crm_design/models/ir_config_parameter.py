from odoo import api, models, tools, fields

IGNORED_PATH_KEY = "inactive_session_time_out_ignored_url"


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    inactive_session_time_out_delay = fields.Char(default="5")

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        ICPSudo = self.env['ir.config_parameter'].sudo()
        inactive_session_time_out_delay = ICPSudo.get_param('auth_session_timeout.inactive_session_time_out_delay')
        res.update(
            inactive_session_time_out_delay=inactive_session_time_out_delay
        )
        return res

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        ICPSudo = self.env['ir.config_parameter'].sudo()
        ICPSudo.set_param('auth_session_timeout.inactive_session_time_out_delay', self.inactive_session_time_out_delay if self.inactive_session_time_out_delay else '5')


class IrConfigParameter(models.Model):
    _inherit = "ir.config_parameter"

    @api.model
    @tools.ormcache("self.env.cr.dbname")
    def _auth_timeout_get_parameter_ignored_urls(self):
        urls = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param(
                IGNORED_PATH_KEY,
                "",
            )
        )
        return urls.split(",")

    def write(self, vals):
        res = super(IrConfigParameter, self).write(vals)
        self._auth_timeout_get_parameter_ignored_urls.clear_cache(
            self.filtered(lambda r: r.key == IGNORED_PATH_KEY),
        )
        return res
