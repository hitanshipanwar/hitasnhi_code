from odoo import fields, models, api, SUPERUSER_ID,  _
from collections import defaultdict
from odoo.tools import groupby
from odoo.tools import float_compare
from dateutil.relativedelta import relativedelta


class StockPicking(models.Model):
	_inherit = 'stock.picking'

	tag_job_sale_ref = fields.Many2one("sale.order", "Tag Job/Sales Reference")
	remarks = fields.Text(string="Remarks", tracking=True)

	def write(self,vals):
		res = super(StockPicking, self).write(vals)
		if 'remarks' in vals:
			if self.purchase_id:
				self.purchase_id.remarks = self.remarks
		if 'tag_job_sale_ref' in vals:
			if self.purchase_id:
				self.purchase_id.sale_order_ref_id = self.tag_job_sale_ref.id
		return res

class StockRuleInherited(models.Model):
	_inherit = 'stock.rule'


	@api.model
	def _run_buy(self, procurements):
		print("hitanshi panwar")
		procurements_by_po_domain = defaultdict(list)
		print('procurements_by_po_domain =============', procurements_by_po_domain)
		errors = []
		for procurement, rule in procurements:

			# Get the schedule date in order to find a valid seller
			procurement_date_planned = fields.Datetime.from_string(procurement.values['date_planned'])

			supplier = False
			if procurement.values.get('supplierinfo_id'):
				supplier = procurement.values['supplierinfo_id']
			else:
				supplier = procurement.product_id.with_company(procurement.company_id.id)._select_seller(
					partner_id=procurement.values.get("supplierinfo_name"),
					quantity=procurement.product_qty,
					date=procurement_date_planned.date(),
					uom_id=procurement.product_uom)

			# Fall back on a supplier for which no price may be defined. Not ideal, but better than
			# blocking the user.
			supplier = supplier or procurement.product_id._prepare_sellers(False).filtered(
				lambda s: not s.company_id or s.company_id == procurement.company_id
			)[:1]

			if not supplier:
				msg = _('There is no matching vendor price to generate the purchase order for product %s (no vendor defined, minimum quantity not reached, dates not valid, ...). Go on the product form and complete the list of vendors.') % (procurement.product_id.display_name)
				errors.append((procurement, msg))

			partner = supplier.partner_id
			# we put `supplier_info` in values for extensibility purposes
			procurement.values['supplier'] = supplier
			procurement.values['propagate_cancel'] = rule.propagate_cancel

			domain = rule._make_po_get_domain(procurement.company_id, procurement.values, partner)
			procurements_by_po_domain[domain].append((procurement, rule))

		if errors:
			raise ProcurementException(errors)

		for domain, procurements_rules in procurements_by_po_domain.items():
			print("===============================================")
			# Get the procurements for the current domain.
			# Get the rules for the current domain. Their only use is to create
			# the PO if it does not exist.
			procurements, rules = zip(*procurements_rules)

			# Get the set of procurement origin for the current domain.
			origins = set([p.origin for p in procurements])
			# Check if a PO exists for the current domain.
			# po = self.env['purchase.order'].sudo().search([dom for dom in domain], limit=1)
			po = self.env['purchase.order'].sudo().search([dom for dom in domain], limit=1)
			print("po ============================================", po)
			company_id = procurements[0].company_id
			if not po:
				positive_values = [p.values for p in procurements if float_compare(p.product_qty, 0.0, precision_rounding=p.product_uom.rounding) >= 0]
				if positive_values:
					# We need a rule to generate the PO. However the rule generated
					# the same domain for PO and the _prepare_purchase_order method
					# should only uses the common rules's fields.
					vals = rules[0]._prepare_purchase_order(company_id, origins, positive_values)
					# The company_id is the same for all procurements since
					# _make_po_get_domain add the company in the domain.
					# We use SUPERUSER_ID since we don't want the current user to be follower of the PO.
					# Indeed, the current user may be a user without access to Purchase, or even be a portal user.
					print("=========1111111111111111==========valsvalsvalsvals=======================", vals)
					po = self.env['purchase.order'].with_company(company_id).with_user(SUPERUSER_ID).create(vals)
					print("=========1111111111111111=================================", po)
			else:
				# If a purchase order is found, adapt its `origin` field.
				if po.origin:
					missing_origins = origins - set(po.origin.split(', '))
					if missing_origins:
						po.write({'origin': po.origin + ', ' + ', '.join(missing_origins)})
				else:
					po.write({'origin': ', '.join(origins)})

			procurements_to_merge = self._get_procurements_to_merge(procurements)
			procurements = self._merge_procurements(procurements_to_merge)

			po_lines_by_product = {}
			grouped_po_lines = groupby(po.order_line.filtered(lambda l: not l.display_type and l.product_uom == l.product_id.uom_po_id), key=lambda l: l.product_id.id)
			for product, po_lines in grouped_po_lines:
				po_lines_by_product[product] = self.env['purchase.order.line'].concat(*po_lines)
			po_line_values = []
			for procurement in procurements:
				po_lines = po_lines_by_product.get(procurement.product_id.id, self.env['purchase.order.line'])
				po_line = po_lines._find_candidate(*procurement)

				if po_line:
					# If the procurement can be merge in an existing line. Directly
					# write the new values on it.
					vals = self._update_purchase_order_line(procurement.product_id,
						procurement.product_qty, procurement.product_uom, company_id,
						procurement.values, po_line)
					po_line.write(vals)
				else:
					if float_compare(procurement.product_qty, 0, precision_rounding=procurement.product_uom.rounding) <= 0:
						# If procurement contains negative quantity, don't create a new line that would contain negative qty
						continue
					# If it does not exist a PO line for current procurement.
					# Generate the create values for it and add it to a list in
					# order to create it in batch.
					partner = procurement.values['supplier'].partner_id
					po_line_values.append(self.env['purchase.order.line']._prepare_purchase_order_line_from_procurement(
						procurement.product_id, procurement.product_qty,
						procurement.product_uom, procurement.company_id,
						procurement.values, po))
					# Check if we need to advance the order date for the new line
					order_date_planned = procurement.values['date_planned'] - relativedelta(
						days=procurement.values['supplier'].delay)
					if fields.Date.to_date(order_date_planned) < fields.Date.to_date(po.date_order):
						po.date_order = order_date_planned
			self.env['purchase.order.line'].sudo().create(po_line_values)
		print('po_line_values ===========================', po_line_values)
		print('po ===========================', po)


	def _prepare_purchase_order(self, company_id, origins, values):
		print('_prepare_purchase_order =============================values=', values)
		print('_prepare_purchase_order ==============================origins', origins)
		print('_prepare_purchase_order ==============================company_id', company_id)
		""" Create a purchase order for procuremets that share the same domain
		returned by _make_po_get_domain.
		params values: values of procurements
		params origins: procuremets origins to write on the PO
		"""
		purchase_date = min([fields.Datetime.from_string(value['date_planned']) - relativedelta(days=int(value['supplier'].delay)) for value in values])

		# Since the procurements are grouped if they share the same domain for
		# PO but the PO does not exist. In this case it will create the PO from
		# the common procurements values. The common values are taken from an
		# arbitrary procurement. In this case the first.
		values = values[0]
		partner = values['supplier'].partner_id

		fpos = self.env['account.fiscal.position'].with_company(company_id)._get_fiscal_position(partner)

		gpo = self.group_propagation_option
		group = (gpo == 'fixed' and self.group_id.id) or \
				(gpo == 'propagate' and values.get('group_id') and values['group_id'].id) or False

		return {
			'partner_id': partner.id,
			'user_id': False,
			'picking_type_id': self.picking_type_id.id,
			'company_id': company_id.id,
			'currency_id': partner.with_company(company_id).property_purchase_currency_id.id or company_id.currency_id.id,
			'dest_address_id': values.get('partner_id', False),
			'origin': ', '.join(origins),
			'payment_term_id': partner.with_company(company_id).property_supplier_payment_term_id.id,
			'date_order': purchase_date,
			'fiscal_position_id': fpos.id,
			'group_id': group
		}


	def make_purchase_order(self):
		order_line_record = []
		for record in self:
			order_line_record.append((0,0,{
					'pr_line_id': record.id,
					'standard_type': record.product_type,
					'product_id': record.product_id.id,
					'name': record.product_name if not record.product_id else '',
					'product_uom':record.uom_id.id,
					'urgency' : record.urgency,
					'product_qty' : record.amount_required,}))
		rec = self.env['purchase.request']
		ctx = dict(rec.env.context or {})
		ctx.update({
			'default_suggested_vendor': self.partner_name if self.partner_name else '',
			'default_partner_id': self.partner_id.id,
			'default_is_thai': self.is_thai,
			'default_purchase_request_id': self.product_request_id.id,
			'default_sale_order_ref_id' : self.product_request_id.sale_order_ref_id.id,
			'default_remarks' : self.product_request_id.remarks,
			'default_department_id': self.product_request_id.employee_department_id.id,
			'default_order_line' : order_line_record,
			'default_urgency': self.product_request_id.urgency,
			'quotation_only': False,
			'default_multi_attachments': self.product_request_id.attachment_ids.ids,
		})
		return {
					'name': "PR",
					'type': 'ir.actions.act_window',
					'view_type': 'form',
					'view_mode': 'form',
					'res_model': 'purchase.request',
					'context': ctx,
					'target': 'new'

				}
