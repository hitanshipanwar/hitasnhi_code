from datetime import date, datetime
from odoo import api, models, fields
from odoo.tools.misc import clean_context

class Zoho_Crm_History(models.Model):
    _name = "zoho.crm.history"
    _description = "Zoho CRM History"
    # _order = 'date_deadline ASC'
    _rec_name = 'partner_id'

    partner_id = fields.Many2one('res.partner', string='Contact')
    company_id = fields.Many2one('res.company', string='Company')
    date_of_note = fields.Date('Date Of Note', index=True)
    activity_type_id = fields.Many2one('mail.activity.type', string='Activity Type', ondelete='restrict')
    date_completed = fields.Date('Completed Date')
    subject = fields.Char('Subject')
    note = fields.Html('Note', sanitize_style=True)
    user_id = fields.Many2one('res.users', 'UserUser', default=lambda self: self.env.user, index=True, required=True)

    
    
    # res_model_id = fields.Many2one('ir.model', 'Document Model', index=True, ondelete='cascade', required=True)
    # res_model = fields.Char('Related Document Model', index=True, related='res_model_id.model', compute_sudo=True,
    #                         store=True, readonly=True)
    # date_deadline = fields.Date('Due Date', index=True, required=True, default=fields.Date.context_today)
    
    # activity_id = fields.Many2one('mail.activity', string='Activity')
    # feedback = fields.Char(string="Feedback")
