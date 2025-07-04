@api.depends('amount')
	def _compute_amount_paid_tax(self):
		for rec in self:
			account_move = self.env['account.move'].search([('id', '=' ,self._context.get('active_id'))])
			paid_amt = account_move.tax_totals.get('amount_total') - account_move.tax_totals.get('amount_untaxed')
			rec.amount_to_paid = 0.0
			rec.tax_amount_to_paid = 0.0
			rec.tax_paid = paid_amt
			amt_tax = rec.amount * (7/100)
			tax_total = account_move.tax_totals
			amt_total = tax_total.get('amount_total')
			untax_amt = tax_total.get('amount_untaxed')
			amt_taxs = amt_total - untax_amt
			amt_taxed = amt_tax - amt_taxs
			amt = amt_taxs - amt_tax
			for line in account_move.invoice_line_ids:
				if rec.amount == account_move.amount_residual:
					rec.amount_to_paid = self.amount - account_move.tax_paid
					rec.tax_amount_to_paid = account_move.tax_paid
				else:
					tax_amt = account_move.tax_paid
					amt_tax = rec.amount * (7/100)
					amt = tax_amt - amt_tax
					paid_untax_amt = rec.amount - amt_tax

					if amt_tax >= account_move.tax_paid:
						rec.tax_amount_to_paid = account_move.tax_paid
						rec.amount_to_paid = self.amount - account_move.tax_paid
					else:
						rec.tax_amount_to_paid = amt_tax
						rec.amount_to_paid = self.amount - rec.tax_amount_to_paid