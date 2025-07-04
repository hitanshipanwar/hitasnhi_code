from odoo import api, fields, models, tools, SUPERUSER_ID, _, Command
from odoo.exceptions import AccessError, MissingError, ValidationError, UserError
import json
from odoo.osv.expression import AND, TRUE_DOMAIN, normalize_domain

class CrmInherited(models.Model):
	_inherit = "crm.lead"

	partner_id = fields.Many2one('res.partner', string="Customer",
								 domain="[('customer_rank', '>', 0), ('company_id', 'in', (False, company_id))]")
	platform_ids = fields.Many2many('platform.crm')
	product_requirement = fields.Selection(string="Product Requirements",
										   selection=[('built_in', 'Built - In'), ('loose', 'Stone'),
													  ('doors', 'Doors'), ('other', 'Other')], required=True,
										   default='built_in')
	accessories = fields.One2many('crm.lead.accessories', 'crm_ref_id')
	sizing = fields.Char()

	@api.onchange('stage_id')
	def _onchage_state_restrict_user(self):
		for rec in self:
			if rec.user_id:
				if rec.user_id.id != self.env.user.id:
					raise UserError(_("You are not the owner of this Pipeline...!"))

	def write(self, vals):
		res = super(CrmInherited, self).write(vals)
		sale_orders = self.env['sale.order'].search([('opportunity_id', '=', self.id)])
		for lead in sale_orders:
			lead.user_id = self.user_id
			lead.need_design = True
			lead.designer_id = self.designer_id
			# lead.user_id = vals['user_id']
		return res

	def action_new_quotation(self):
		result = super(CrmInherited, self).action_new_quotation()

		# Send Notification to Sales Person
		res_users = self.env['res.users'].sudo().search([('id', '=', result.get('context').get('default_user_id'))])
		email_from = self.env['ir.mail_server'].sudo().search([], limit=1)
		mail_values_user_check = {
			'subject': 'Sale Order Assigned',
			'email_to': res_users.partner_id.email,
			'email_from': email_from.smtp_user,
			'body_html': '''<div> Dear %s, You have been assigned a <strong>New Sale Order</strong>
						</div>''' % (res_users.partner_id.name)

		}
		create_and_send_email = self.env['mail.mail'].sudo().create(mail_values_user_check).sudo().send()

		result.get('context').update({
			'default_partner_id': self.partner_id.id,
			'default_platform_ids': self.platform_ids.ids,
			'default_product_requirement': self.product_requirement,
			'default_sizing': self.sizing,
			'default_validity_date': self.date_deadline,
		})
		if self.designer_id:
			result.get('context').update({
				'default_need_design': True,
				'default_designer_id': self.designer_id.id
				})

		return result

	def action_set_won(self):
		rec = super(CrmInherited, self).action_set_won()
		order_prices = []
		for order in self.order_ids:
			if order.state == 'sale':
				# total_amount = json.loads(order.tax_totals)
				total_amount = order.tax_totals
				# order_prices.append(total_amount.get('amount_untaxed'))
				order_prices.append(total_amount.get('amount_total'))
				if len(order_prices) > 0:
					self.expected_revenue = min(order_prices)
		return rec


# Not in used currently
class CrmGenerateLeadInherited(models.Model):
	_inherit = "crm.iap.lead.mining.request"

	partner_id = fields.Many2one('res.partner', string="Customer")
	platform_ids = fields.Many2many('platform.crm')
	product_requirement = fields.Selection(string="Product Requirement",
										   selection=[('built_in', 'Built - In'), ('loose', 'Loose Furniture'),
													  ('countertop', 'Countertop'), ('compact_set', 'Compact Set')])
	accessories = fields.Text()
	sizing = fields.Char()


class Platform(models.Model):
	_name = 'platform.crm'
	_description = "Crm Platroms"

	name = fields.Char(string="Name")


class AccessoriesDesign(models.Model):
	_name = 'crm.lead.accessories'
	_description = 'Accessories CRM Design'

	product_id = fields.Many2one('product.product')
	quantity = fields.Float(string="Quantity", required=True, default=1.0)
	price = fields.Float(string='Unit Price')
	subtotal = fields.Float(string="Subtotal", readonly=True)
	crm_ref_id = fields.Many2one('crm.lead')
	sale_ref_id = fields.Many2one('sale.order')
