# -*- coding: utf-8 -*-

from odoo import fields, models, tools, api


class ActivityReport(models.Model):
    """ Sale Order Analysis """

    _name = "sale.activity.report"
    _auto = False
    _description = "Sale Activity Analysis"
    _rec_name = 'id'

    date = fields.Datetime('Completion Date', readonly=True)
    order_create_date = fields.Datetime('Creation Date', readonly=True)
    author_id = fields.Many2one('res.partner', 'Assigned To', readonly=True)
    user_id = fields.Many2one('res.users', 'Salesperson', readonly=True)
    team_id = fields.Many2one('crm.team', 'Sales Team', readonly=True)
    order_id = fields.Many2one('sale.order', "Opportunity", readonly=True)
    body = fields.Html('Activity Description', readonly=True)
    subtype_id = fields.Many2one('mail.message.subtype', 'Subtype', readonly=True)
    mail_activity_type_id = fields.Many2one('mail.activity.type', 'Activity Type', readonly=True)
    warehouse_id = fields.Many2one('stock.warehouse', 'Warehouse', readonly=True)
    company_id = fields.Many2one('res.company', 'Company', readonly=True)
    picking_policy = fields.Selection([
        ('direct', 'As soon as possible'),
        ('one', 'When all products are ready')],
        string='Shipping Policy', required=True, readonly=True, default='direct',
        states={'draft': [('readonly', False)], 'sent': [('readonly', False)]}
        ,help="If you deliver all products at once, the delivery order will be scheduled based on the greatest "
        "product lead time. Otherwise, it will be based on the shortest.")
    partner_id = fields.Many2one('res.partner', 'Customer', readonly=True)
    pricelist_id = fields.Many2one('product.pricelist', 'Pricelist', readonly=True)
    payment_term_id = fields.Many2one('account.payment.term', 'Payment Terms', readonly=True)
    state = fields.Selection([
        ('draft', 'Quotation'),
        ('sent', 'Quotation Sent'),
        ('sale', 'Sales Order'),
        ('done', 'Locked'),
        ('cancel', 'Cancelled'),
        ], string='Status')

    subject = fields.Char("Subject")
    body = fields.Html("Notes")

    def _select(self):
                # o.partner_id,
        return """
            SELECT
                m.id,
                o.state,
                o.partner_id,
                o.pricelist_id,
                o.payment_term_id,
                m.subtype_id,
                m.mail_activity_type_id,
                m.author_id,
                m.date,
                m.body,
                o.id as order_id,
                o.user_id,
                o.team_id,
                o.warehouse_id,
                o.company_id,
                o.picking_policy,
                o.create_date as order_create_date,
                m.subject
        """

    def _from(self):
        return """
            FROM mail_message m
        """
            # LEFT JOIN res_partner r ON r.id = m.res_id

    def _join(self):
        return """
            JOIN sale_order AS o ON o.id = m.res_id 
            JOIN res_partner AS r ON r.id = m.res_id
        """
           
    def _where(self):
        disccusion_subtype = self.env.ref('mail.mt_note')
        return """
            WHERE
                m.model IN ('sale.order','res.partner') 
                AND (m.mail_activity_type_id IS NOT NULL OR m.subtype_id = %s)
        """ % (disccusion_subtype.id,)

    def my_query(self):
        disccusion_subtype = self.env.ref('mail.mt_note')
        return """    
            SELECT 
                m.id,
                m.subtype_id,
                m.mail_activity_type_id,
                m.author_id,
                m.date,
                m.body,
                m.subject,
                o.company_id
            FROM mail_message AS m
            JOIN sale_order AS o ON m.res_id = o.id
            WHERE
                m.model = 'sale.order' AND (m.mail_activity_type_id IS NOT NULL OR m.subtype_id = %s)
            
            UNION ALL 
            SELECT 
                m.id,
                m.subtype_id,
                m.mail_activity_type_id,
                m.author_id,
                m.date,
                m.body,
                m.subject,
                p.company_id
            FROM mail_message AS m
            JOIN res_partner AS p ON m.res_id = p.id
            WHERE
                m.model = 'res.partner' AND (m.mail_activity_type_id IS NOT NULL OR m.subtype_id = %s)
        """ % (disccusion_subtype.id,disccusion_subtype.id)
    

    # def init(self):
    #     tools.drop_view_if_exists(self._cr, self._table)
    #     self._cr.execute("""
    #         CREATE OR REPLACE VIEW %s AS (
    #             %s
    #             %s
    #             %s
    #             %s
    #         )
    #     """ % (self._table, self._select(), self._from(), self._join(), self._where())
    #     )
    
    def init(self):
        tools.drop_view_if_exists(self._cr, self._table)
        self._cr.execute("""
            CREATE OR REPLACE VIEW %s AS (
                %s
            )
        """ % (self._table,self.my_query())
        )