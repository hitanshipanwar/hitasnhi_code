from odoo import fields, models, api

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.onchange('partner_id')
    def onchange_partner_id(self):
        res = super(SaleOrder, self).onchange_partner_id()
        if self.partner_id:
            self.rep_template_id = self.partner_id.rep_template_id and self.partner_id.rep_template_id.id or False
        return res

    rep_template_id = fields.Many2one('report.company', 'Templates to Print')
    order_sent = fields.Selection([('yes', 'Yes'), ('no', 'No')], default="no", string="Order Complete?", copy=False)

    def rount_code(self):
        lable = []
        for sol in self.order_line:
            if sol.route_id:
                if sol.route_id.short_name:
                    if sol.route_id.short_name not in lable:
                        lable.append(sol.route_id.short_name)
        return ",".join(lable)
    
    def action_quotation_sent(self):
        res = super(SaleOrder, self).action_quotation_sent()
        self.write({'order_sent': 'yes'})
        return res

    def _prepare_invoice(self):
        res = super(SaleOrder, self)._prepare_invoice()
        res['rep_template_id'] = self.rep_template_id and self.rep_template_id.id or False
        return res

    @api.model
    def create(self, vals):
        result = super(SaleOrder, self).create(vals)
        if result.partner_id and result.partner_id.rep_template_id:
            result.rep_template_id = result.partner_id.rep_template_id
        return result

    def action_quotation_send(self):
        ''' Opens a wizard to compose an email, with relevant mail template loaded by default '''
        self.ensure_one()
        template_id = self._find_mail_template()
        lang = self.env.context.get('lang')
        template = self.env['mail.template'].browse(template_id)
        # Todo [Dhaval]: add custom email from
        if self.partner_id and self.partner_id.rep_template_id and self.partner_id.rep_template_id.email_from_sale:
            template.email_from = self.partner_id.rep_template_id.email_from_sale
        else:
            template.email_from = self.user_id.email_formatted or self.env.user.email_formatted

        if template.lang:
            lang = template._render_lang(self.ids)[self.id]
        ctx = {
            'default_model': 'sale.order',
            'default_res_id': self.ids[0],
            'default_use_template': bool(template_id),
            'default_template_id': template_id,
            'default_composition_mode': 'comment',
            'mark_so_as_sent': True,
            'custom_layout': "mail.mail_notification_paynow",
            'proforma': self.env.context.get('proforma', False),
            'force_email': True,
            'model_description': self.with_context(lang=lang).type_name,
        }
        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(False, 'form')],
            'view_id': False,
            'target': 'new',
            'context': ctx,
        }

