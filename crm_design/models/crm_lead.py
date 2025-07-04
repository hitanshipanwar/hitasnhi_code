from odoo import api, fields, models, _
from odoo.exceptions import UserError

class CrmLead(models.Model):
	_inherit = 'crm.lead'

	quotation_cancel_count = fields.Integer(compute='_compute_sale_data')
	total_count = fields.Char()
	invoice_paid_amount_total = fields.Monetary("Invoice Paid Amount",compute='_compute_invoice_paid_data', currency_field='company_currency', store=True)

	progressbar_amount = fields.Monetary('Amount', currency_field='company_currency', compute='_compute_progressbar_amt', store=True)
	designer_id = fields.Many2one('res.users', string="Designer",
		domain=lambda self: [("groups_id", "=", self.env.ref( "crm_design.group_allow_to_add_design" ).id)])
	unassigned_designer = fields.Selection(selection=[('un_assigned', 'Unassigned')], compute="_compute_unassigned_designer", store=True)

	@api.depends('designer_id')
	def _compute_unassigned_designer(self):
		for rec in self:
			if rec.designer_id:
				rec.unassigned_designer = ''
			else:
				rec.unassigned_designer = 'un_assigned'


	@api.depends('order_ids.invoice_ids.payment_state', 'order_ids.invoice_ids.currency_id')
	def _compute_invoice_paid_data(self):
		for lead in self:
			company_currency = lead.company_currency or self.env.company.currency_id
			sale_orders = lead.order_ids.filtered_domain(self._get_lead_sale_order_domain())
			paid_total = 0.0
			for order in sale_orders:
				for invoice in order.invoice_ids:
					 paid_total += invoice.currency_id._convert(
						(invoice.amount_total - invoice.amount_residual), company_currency, lead.company_id, fields.Date.today()
					)
					# paid_total += (invoice.amount_total - invoice.amount_residual)
			lead.invoice_paid_amount_total = paid_total

	@api.depends('stage_id', 'expected_revenue', 'order_ids', 'order_ids.invoice_ids.payment_state')
	def _compute_progressbar_amt(self):
		for rec in self:
			if rec.stage_id.is_won:
				rec.progressbar_amount = rec.sale_amount_total
			elif rec.stage_id.id == self.env.ref('crm_design.stage_lead_fully_invoiced').id:
				rec.progressbar_amount = rec.invoice_paid_amount_total
			else:
				rec.progressbar_amount = rec.expected_revenue

	def unlink(self):
		if not self.env.user.has_group('base.group_system') and not self.env.user.has_group('base.group_erp_manager'):
			if self.env.user.id != self.create_uid.id:
				raise UserError(_('%s You are not able to delete record.' %(self.env.user.name)))
		return super(CrmLead, self).unlink()

	def _compute_sale_data(self):

		res = super(CrmLead,self)._compute_sale_data()

		for lead in self:
			quotation_cancel_cnt = 0
			for order in lead.order_ids:
				if order.state in ['cancel',]:
					quotation_cancel_cnt += 1

			lead.quotation_cancel_count = quotation_cancel_cnt
		return res


	def action_view_sale_quotation(self):
		action = self.env["ir.actions.actions"]._for_xml_id("crm_design.action_quotations_with_onboarding_crm_lead")
		action['context'] = {
			'search_default_draft': 1,
			'search_default_cancel': 1,

			'search_default_partner_id': self.partner_id.id,
			'default_partner_id': self.partner_id.id,
			'default_opportunity_id': self.id
		}
		action['domain'] = [('opportunity_id', '=', self.id), ('state', 'in', ['draft', 'sent','cancel'])]
		quotations = self.mapped('order_ids').filtered(lambda l: l.state in ('draft', 'sent','cancel'))
		if len(quotations) == 1:
			action['views'] = [(self.env.ref('sale.view_order_form').id, 'form')]
			action['res_id'] = quotations.id
		return action