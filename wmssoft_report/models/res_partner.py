
from odoo import fields, models, api

class ResPartner(models.Model):
    _inherit = 'res.partner'
    
    rep_template_id = fields.Many2one('report.company', 'Templates to Print')

    @api.model
    def create(self, vals):
        result = super(ResPartner, self).create(vals)
        if result.parent_id and result.parent_id.rep_template_id:
            result.rep_template_id = result.parent_id.rep_template_id
        return result
