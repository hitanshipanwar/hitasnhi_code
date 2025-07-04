# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    specs_sale_ids = fields.One2many('specs.sale', 'specs_sale_id', string='Specs sale')
    specs_sale_count = fields.Integer('Specs count', compute='_compute_specs_sale_count')
    # PORTAL
    is_detail_doc_download = fields.Boolean()
    is_agreement_doc_download = fields.Boolean()

    @api.depends('specs_sale_ids', 'specs_sale_ids.specs_sale_id')
    def _compute_specs_sale_count(self):
        for order in self:
            order.specs_sale_count = len(order.specs_sale_ids)

    def specs_call_view(self):
        self.ensure_one()
        # self._check_specs_sale()
        action = self.env['ir.actions.act_window']._for_xml_id('solt_quarry_door_sale.action_specs_sale')
        domain = [('id', 'in', self.specs_sale_ids.ids)]
        if len(self.specs_sale_ids) == 1:
            form_view = [(self.env.ref('solt_quarry_door_sale.specs_sale_view_form').id, 'form')]
            if 'views' in action:
                action['views'] = form_view + [(state,view) for state,view in action['views'] if view != 'form']
            else:
                action['views'] = form_view
            action['res_id'] = self.specs_sale_ids.id

        if domain:
            action['domain'] = domain
        context = {
            'default_specs_sale_id': self.id,
        }
        if self.env.company.specs_sale_company_id == self.company_id:
            context.update({
                'default_specs_opportunity_id': self.opportunity_id and self.opportunity_id.id or False,
                'default_salesman_id': self.user_id.id
            })
        action['context'] = context
        return action

    @api.onchange('sale_order_template_id')
    def _onchange_sale_order_template_id(self):
        if self.sale_order_template_id:
            order_line = self.order_line.filtered(lambda l: l.sale_specs_id)

            super(SaleOrder, self)._onchange_sale_order_template_id()
            self.order_line |= order_line
        else:
            super(SaleOrder, self)._onchange_sale_order_template_id()

    @api.depends('partner_id', 'company_id', 'team_id')
    def _compute_pricelist_id(self):
        # company for calculation price = cantera eeuu
        company_id = self.env.company.specs_sale_company_id
        for order in self:
            order = order.with_company(order.company_id)
            if order.company_id == company_id:
                if order.state != 'draft':
                    continue
                if not order.team_id and not order.partner_id:
                    order.pricelist_id = False
                    continue
                order.pricelist_id = order.team_id.pricelist_id or order.partner_id.property_product_pricelist
            else:
                super(SaleOrder, order)._compute_pricelist_id()

    @api.depends('team_id')
    def _compute_journal_id(self):
        # company for calculation price = cantera eeuu
        company_id = self.env.company.specs_sale_company_id
        for order in self:
            order = order.with_company(order.company_id)
            if order.company_id == company_id:
                if order.state != 'draft':
                    continue
                if not order.team_id:
                    order.journal_id = False
                    continue
                order.journal_id = order.team_id.sale_journal_id
            else:
                super(SaleOrder, self)._compute_journal_id()

    @api.model_create_multi
    def create(self, vals_list):
        company_id = self.env.company.specs_sale_company_id
        for vals in vals_list:
            if 'company_id' in vals:
                self = self.with_company(vals['company_id'])

            if vals['company_id'] == company_id.id and vals.get('name', _("New")) == _("New"):
                team_id = vals.get('team_id') and self.env['crm.team'].browse(vals.get('team_id'))
                if not team_id.team_sequence_id:
                    raise ValidationError(_(f"The team {team_id.name} do not have a sequence."))
                code = f"{team_id._name}.{team_id.code.lower()}"
                seq_date = fields.Datetime.context_timestamp(
                    self, fields.Datetime.to_datetime(vals['date_order'])
                ) if 'date_order' in vals else None
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    code, sequence_date=seq_date) or _("New")

        return super().create(vals_list)

    def write(self, values):
        if 'team_id' in values and any(so.name != _("New") for so in self):
            raise UserError(_("You cannot change the team because the sequence has already been generated to the order, please delete the order to generate the correct sequence."))
        return super().write(values)

    def _action_cancel(self):
        specs_sale_ids = self.specs_sale_ids.filtered(lambda s: s.state != 'cancel')
        specs_sale_ids.action_state_cancel()
        return super(SaleOrder, self)._action_cancel()


