from odoo import api, fields, models, _


class MailFollowers(models.Model):
    _inherit = "mail.followers"

    @api.model_create_multi
    def create(self, vals_list):
        created_followers = super(MailFollowers, self).create(vals_list)
        for rec in created_followers:
            if rec.res_model and rec.res_id:
                current_record = self.env[rec.res_model].sudo().browse(rec.res_id)
                current_record.sudo()._message_log(body="%s has been added as a follower on this record." % str(rec.partner_id.name))
        return created_followers


    def unlink(self):
        for follower in self:
            current_record = self.env[follower.res_model].sudo().browse(follower.res_id)
            current_record._message_log(body="%s has been removed as a follower from this record." % str(follower.partner_id.name))
        return super(MailFollowers, self).unlink()