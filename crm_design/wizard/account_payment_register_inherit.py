from odoo import api, fields, models, _

class PaymentRegisterInherit(models.TransientModel):
	_inherit = 'account.payment.register'

	invoice_payment_method = fields.Selection([
		('fixed', 'Fixed Amount'),
		('percentage', 'Pay In Percentage')
		], string='Invoice Payment', default='fixed', required=True)

	amount_in_percent = fields.Float(string="Percentage",digits='Account',default=100.00)

	# Override the Payment Value Creation Method
	# def _create_payment_vals_from_wizard(self):	
	# 	prod_requirement = self.env['account.move'].browse(self._context.get('active_ids', [])).product_requirement			
	# 	# self.env['account.move'].browse(self._context.get('active_ids', [])).invoice_vendor_bill_id.product_requirement = prod_requirement
	# 	if self.invoice_payment_method == 'percentage':
	# 		for wizard in self:
	# 			if wizard.source_currency_id == wizard.currency_id:
	# 				# Same currency.
	# 				amount = wizard.source_amount_currency
	# 			elif wizard.currency_id == wizard.company_id.currency_id:
	# 				# Payment expressed on the company's currency.
	# 				amount = wizard.source_amount
	# 			else:
	# 				# Foreign currency on payment different than the one set on the journal entries.
	# 				amount_payment_currency = wizard.company_id.currency_id._convert(wizard.source_amount, wizard.currency_id, wizard.company_id, wizard.payment_date)
	# 				amount = amount_payment_currency
	# 		amount_percent = amount * self.amount_in_percent / 100
	# 		payment_vals = {
	# 			'date': self.payment_date,
	# 			'amount': amount_percent,
	# 			'payment_type': self.payment_type,
	# 			'partner_type': self.partner_type,
	# 			'ref': self.communication,
	# 			'journal_id': self.journal_id.id,
	# 			'currency_id': self.currency_id.id,
	# 			'partner_id': self.partner_id.id,
	# 			'partner_bank_id': self.partner_bank_id.id,
	# 			'payment_method_line_id': self.payment_method_line_id.id,
	# 			'destination_account_id': self.line_ids[0].account_id.id,
	# 			'product_requirement': prod_requirement
	# 		}
	# 	else:
	# 		payment_vals = {
	# 			'date': self.payment_date,
	# 			'amount': self.amount,
	# 			'payment_type': self.payment_type,
	# 			'partner_type': self.partner_type,
	# 			'ref': self.communication,
	# 			'journal_id': self.journal_id.id,
	# 			'currency_id': self.currency_id.id,
	# 			'partner_id': self.partner_id.id,
	# 			'partner_bank_id': self.partner_bank_id.id,
	# 			'payment_method_line_id': self.payment_method_line_id.id,
	# 			'destination_account_id': self.line_ids[0].account_id.id,
	# 			'product_requirement': prod_requirement
	# 		}

	# 		if not self.currency_id.is_zero(self.payment_difference) and self.payment_difference_handling == 'reconcile':
	# 			payment_vals['write_off_line_vals'] = {
	# 				'name': self.writeoff_label,
	# 				'amount': self.payment_difference,
	# 				'account_id': self.writeoff_account_id.id,
	# 			}
	# 	return payment_vals

	@api.depends('amount_in_percent')
	def _compute_payment_difference(self):
		self._constrains_amount_in_percent()
		super(PaymentRegisterInherit, self)._compute_payment_difference()

	@api.constrains('amount_in_percent')
	def _constrains_amount_in_percent(self):
		for rec in self.filtered(lambda x: x.invoice_payment_method == 'percentage'):
			if rec.amount_in_percent > 100.00:
				raise UserError(_("You can't enter percentage more than 100."))
			amount = rec._get_total_amount_in_wizard_currency_to_full_reconcile(rec._get_batches()[0])[0]
			if rec.amount_in_percent == 100.00:
				rec.amount = amount
			elif not rec.amount_in_percent:
				rec.amount = 0.0
			else:
				rec.amount = (rec.amount_in_percent * amount) / 100
