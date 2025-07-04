# Copyright 2004-2009 Tiny SPRL (<http://tiny.be>).
# Copyright 2016 ACSONE SA/NV (<http://acsone.eu>)
# Copyright 2015-2019 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from odoo import api, fields, models


class PurchaseOrder(models.Model):
	_inherit = "purchase.order"

	total_discount_amount = fields.Monetary("Discount Amt", compute='_compute_total_discount_amount', store=True)

	# adding discount calculation to depends
	@api.depends('order_line.discount_amount')
	def  _compute_tax_totals(self):
		return super()._compute_tax_totals()

	@api.depends('order_line.discount_amount')
	def _compute_total_discount_amount(self):
		for order in self:
			amount_disc = 0.0
			for line in order.order_line:
				amount_disc += line.discount_amount
		order.update({
			'total_discount_amount': amount_disc,
		})

	def _add_supplier_to_product(self):
		"""Insert a mapping of products to PO lines to be picked up
		in supplierinfo's create()"""
		self.ensure_one()
		po_line_map = {
			line.product_id.product_tmpl_id.id: line for line in self.order_line
		}
		return super(
			PurchaseOrder, self.with_context(po_line_map=po_line_map)
		)._add_supplier_to_product()

	# @api.depends('order_line.taxes_id', 'order_line.price_subtotal', 'amount_total', 'amount_untaxed', 'order_line.discount_amount', 'order_line.discount', 'order_line.discount_selection')
	# def  _compute_tax_totals(self):
	# 	res = super(PurchaseOrder, self)._compute_tax_totals()
	# 	for order in self:
	# 		order_lines = order.order_line.filtered(lambda x: not x.display_type) 
	# 		print('order_lines>>>>>>>>>>>>>>>>>>>>>>>>>', order_lines)
	# 		order.tax_totals.update({
	# 			'total_discount_amount': 100
	# 			})
	# 		# order.tax_totals = self.env['account.tax']._prepare_tax_totals(
	# 		#     [x._convert_to_tax_base_line_dict() for x in order_lines],
	# 		#     order.currency_id or order.company_id.currency_id,
	# 		# )
	# 		print("order.tax_totals =================================", order.tax_totals)
	# 	return res



class PurchaseOrderLine(models.Model):
	_inherit = "purchase.order.line"

	# adding discount to depends
	@api.depends("discount", "discount_selection","discount_amount")
	def _compute_amount(self):
		return super()._compute_amount()

	def _convert_to_tax_base_line_dict(self):
		vals = super()._convert_to_tax_base_line_dict()
		vals.update({"discount": self.discount,
					 "discount_selection": self.discount_selection,
					 "discount_amount": self.discount_amount})
		return vals

	discount = fields.Float(string="Discount", digits="Discount")
	discount_selection = fields.Selection(string='Dis Selection', selection=[('by_percent', 'By Percent'), ('by_price', 'By Price')], default="by_percent")
	discount_amount = fields.Float(string="Discount Calculation", compute="_compute_discount_calculation")


	# _sql_constraints = [
	# 	(
	# 		"discount_limit",
	# 		"CHECK (discount <= 100.0)",
	# 		"Discount must be lower than 100%.",
	# 	)
	# ]

	@api.depends('product_qty', 'price_unit', 'discount', 'discount_selection')
	def _compute_discount_calculation(self):
		for rec in self:
			if rec.discount_selection == 'by_price':
				rec.discount_amount = rec.discount
			else:
				rec.discount_amount = rec.price_unit * rec.discount / 100


	def _get_discounted_price_unit(self):
		"""Inheritable method for getting the unit price after applying
		discount(s).

		:rtype: float
		:return: Unit price after discount(s).
		"""
		self.ensure_one()
		if self.discount_selection == 'by_price':
			if self.discount:
				return self.price_unit - self.discount
		else:   
			if self.discount:
				return self.price_unit * (1 - self.discount / 100)
		return self.price_unit

	def _get_stock_move_price_unit(self):
		"""Get correct price with discount replacing current price_unit
		value before calling super and restoring it later for assuring
		maximum inheritability.

		HACK: This is needed while https://github.com/odoo/odoo/pull/29983
		is not merged.
		"""
		# Use 'skip_update_price_unit' context key to avoid infinite
		# recursion. Updating the price_unit field here triggers the
		# 'write' method of 'purchase.order.line' in stock_account
		# module which triggers this method again.
		if self.env.context.get("skip_update_price_unit"):
			return super()._get_stock_move_price_unit()
		price_unit = False
		price = self._get_discounted_price_unit()
		if price != self.price_unit:
			# Only change value if it's different
			price_unit = self.price_unit
			self.with_context(skip_update_price_unit=True).price_unit = price
		price = super()._get_stock_move_price_unit()
		if price_unit:
			self.with_context(skip_update_price_unit=True).price_unit = price_unit
		return price

	@api.onchange("product_qty", "product_uom")
	def _onchange_quantity(self):
		"""
		Check if a discount is defined into the supplier info and if so then
		apply it to the current purchase order line
		"""
		if self.product_id:
			date = None
			if self.order_id.date_order:
				date = self.order_id.date_order.date()
			seller = self.product_id._select_seller(
				partner_id=self.partner_id,
				quantity=self.product_qty,
				date=date,
				uom_id=self.product_uom,
			)
			self._apply_value_from_seller(seller)
		return

	@api.model
	def _apply_value_from_seller(self, seller):
		"""Overload this function to prepare other data from seller,
		like in purchase_triple_discount module"""
		if not seller:
			return
		self.discount = seller.discount

	def _prepare_account_move_line(self, move=False):
		vals = super(PurchaseOrderLine, self)._prepare_account_move_line(move)
		vals["discount"] = self.discount
		return vals

	@api.model
	def _prepare_purchase_order_line(
		self, product_id, product_qty, product_uom, company_id, supplier, po
	):
		"""Apply the discount to the created purchase order"""
		res = super()._prepare_purchase_order_line(
			product_id, product_qty, product_uom, company_id, supplier, po
		)
		partner = supplier.partner_id
		uom_po_qty = product_uom._compute_quantity(product_qty, product_id.uom_po_id)
		seller = product_id.with_company(company_id)._select_seller(
			partner_id=partner,
			quantity=uom_po_qty,
			date=po.date_order and po.date_order.date(),
			uom_id=product_id.uom_po_id,
		)
		res.update(self._prepare_purchase_order_line_from_seller(seller))
		return res

	@api.model
	def _prepare_purchase_order_line_from_seller(self, seller):
		"""Overload this function to prepare other data from seller,
		like in purchase_triple_discount module"""
		if not seller:
			return {}
		return {"discount": seller.discount}

	def write(self, vals):
		res = super().write(vals)
		if "discount" in vals or "price_unit" in vals:
			for line in self.filtered(lambda l: l.order_id.state == "purchase"):
				# Avoid updating kit components' stock.move
				moves = line.move_ids.filtered(
					lambda s: s.state not in ("cancel", "done")
					and s.product_id == line.product_id
				)
				moves.write({"price_unit": line._get_discounted_price_unit()})
		return res
