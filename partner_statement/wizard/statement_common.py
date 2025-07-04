# -*- coding: utf-8 -*-
##############################################################################
#                                                                            #
# Part of WMSSOFT. (Website: www.wmssoft.com.au).                            #
# See LICENSE file for full copyright and licensing details.                 #
#                                                                            #
##############################################################################

import datetime

from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _

import logging
_logger = logging.getLogger(__name__)

import base64


class StatementCommon(models.AbstractModel):

    _name = "statement.common.wizard"
    _description = "Statement Reports Common Wizard"

    
    @api.model
    def default_get(self,fields):
        res = super(StatementCommon, self).default_get(fields)
        if self._context.get('active_model') == 'res.partner' and self._context.get('active_id'):
            partner_id = self.env['res.partner'].search([('id','=',self._context.get('active_id'))])
            if partner_id:
                res['partner_id'] = partner_id.id
        return res

    name = fields.Char(string="Name")
    company_id = fields.Many2one("res.company", default=lambda self: self.env.company, string="Company", required=True)
    date_end = fields.Date(required=True, default=fields.Date.context_today)
    show_aging_buckets = fields.Boolean(default=True)
    number_partner_ids = fields.Integer(default=lambda self: len(self._context["active_ids"]))
    filter_partners_non_due = fields.Boolean(string="Don't show partners with no due entries", default=True)
    filter_negative_balances = fields.Boolean("Exclude Negative Balances", default=True)
    aging_type = fields.Selection([("days", "Age by Days"), ("months", "Age by Months")],
        string="Aging Method", default="days", required=True)
    account_type = fields.Selection([("receivable", "Receivable"), ("payable", "Payable")],
        string="Account type", default="receivable",)
    partner_id = fields.Many2one('res.partner',string="Customer")

    @api.onchange("aging_type")
    def onchange_aging_type(self):
        if self.aging_type == "months":
            self.date_end = fields.Date.context_today(self).replace(
                day=1
            ) - relativedelta(days=1)
        else:
            self.date_end = fields.Date.context_today(self)

    def button_export_pdf(self):
        self.ensure_one()
        return self._export()

    def _prepare_statement(self):
        self.ensure_one()
        return {
            "date_end": self.date_end,
            "company_id": self.company_id.id,
            "partner_ids": self._context["active_ids"],
            "show_aging_buckets": self.show_aging_buckets,
            "filter_non_due_partners": self.filter_partners_non_due,
            "account_type": self.account_type,
            "aging_type": self.aging_type,
            "filter_negative_balances": self.filter_negative_balances,
        }

    def _export(self):
        raise NotImplementedError

    # def send_statement_email(self):
    #     template = self.env.ref(
    #         'partner_statement.email_template_customer_statement_server_action')
    #     if template:
    #         if self.partner_id:
    #             partner = self.partner_id
    #             data = self._prepare_statement()
    #             pdf = self.env.ref('partner_statement.action_print_outstanding_statement').sudo()._render_qweb_pdf(res_ids=self.id, data=data)[0]
    #             attachment_name = '%s Customer Statement' % datetime.date.today()
    #             body = 'Customer Statement Generated at %s' % (datetime.date.today())

    #             attachment_id = self.env['ir.attachment'].create({
    #                 'name':  _("%s.pdf") % attachment_name,
    #                 'type': 'binary',
    #                 'datas': base64.encodebytes(pdf),
    #                 'res_model': 'res.partner',
    #                 'res_id': partner.id
    #             })

    #             partner.message_post(body=body, attachment_ids=[attachment_id.id], message_type='comment', subtype_xmlid='mail.mt_note')
    #             _logger.info("Generated and Attached Customer Statement For Partner %s", partner.id)

    #             # TODO: Dhaval: need to add condition which value bases we need to send a mail
    #             # if partner.total_due > 0:
    #             if partner.email:
    #                 # template.email_to = False
    #                 template.email_to = partner.email
    #                 template.attachment_ids  = [(4, attachment_id.id)]
    #                 self.env['mail.template'].browse(
    #                     template.id).with_context(partner=partner).send_mail(self.id, force_send=True)
    #             else:
    #                 message_date = datetime.date.today()
    #                 partner.message_post(
    #                     body=_("Amount Due is zero as on %s so statement email is not sent to the customer"
    #                            % message_date,
    #                     message_type='comment',
    #                     subtype_xmlid='mail.mt_note'))


    def send_statement_email(self):
        template = self.env.ref('partner_statement.email_template_customer_statement_server_action')
        if template:
            partnerRec = self.env['res.partner'].browse(self._context.get('active_ids'))
            for partner in partnerRec:
                data = {
                        "date_end": self.date_end,
                        "company_id": self.company_id.id,
                        "partner_ids": partner.ids,
                        "show_aging_buckets": self.show_aging_buckets,
                        "filter_non_due_partners": self.filter_partners_non_due,
                        "account_type": self.account_type,
                        "aging_type": self.aging_type,
                        "filter_negative_balances": self.filter_negative_balances,
                    }
                pdf = self.env.ref('partner_statement.action_print_outstanding_statement').sudo(
                )._render_qweb_pdf(res_ids=partner.id,data=data)[0]
                attachment_name = '%s Customer Statement' % datetime.date.today()
                body = 'Customer Statement Generated at %s' % (datetime.date.today())
                partner.message_post(body=body, attachments=[(attachment_name, pdf)], message_type='comment')
                _logger.info("Generated and Attached Customer Statement For Partner %s", partner.id)

                attachment_id = self.env['ir.attachment'].create({
                    'name':  _("%s.pdf") % attachment_name,
                    'type': 'binary',
                    'datas': base64.encodebytes(pdf),
                    'res_model': 'res.partner',
                    'res_id': partner.id
                })

                if partner.email:
                    if partner.total_due > 0:
                        template.email_to = False
                        template.email_to = partner.email
                        template.attachment_ids = [(6, 0, [])]
                        template.attachment_ids  = [(4, attachment_id.id)]
                        self.env['mail.template'].browse(
                            template.id).with_context(partner=partner).send_mail(self.id, force_send=True)
                    else:
                        message_date = datetime.date.today()
                        partner.message_post(
                            body=_("Amount Due is zero as on %s so statement email is not sent to the customer"
                                   % message_date))
                else:
                    partner.message_post(body=_("Please set an email on the partner."))
