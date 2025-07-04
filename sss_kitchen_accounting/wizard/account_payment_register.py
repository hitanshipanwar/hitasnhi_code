from odoo import api, fields, models, _
from odoo.exceptions import UserError

class AccountPaymentRegister(models.TransientModel):
	_inherit = "account.payment.register"

	amount_to_paid = fields.Monetary(string='Amount Paid', compute='_compute_amount_paid_tax', readonly=True)
	tax_amount_to_paid = fields.Monetary(string='Tax Paid', compute='_compute_amount_paid_tax', readonly=True)
	tax_paid = fields.Monetary('Paid Tax')
	is_tax_excluded = fields.Boolean("Tax excluded")

	# @api.onchange('is_tax_excluded')
	# def _onchange_tax_excluded(self):
	# 	account_move = self.env['account.move'].search([('id', '=' ,self._context.get('active_id'))])
	# 	for rec in self:
	# 		if rec.is_tax_excluded:
	# 			rec.is_tax_excluded = False
	# 			if account_move.amount_residual == rec.amount:
	# 				raise UserError(_("Amount Due and Paid Amount should not be same in case of Tax excluded...!"))

	@api.depends('amount', 'is_tax_excluded')
	def _compute_amount_paid_tax(self):
		for rec in self:
			account_move = self.env['account.move'].search([('id', '=' ,self._context.get('active_id'))])
			if rec.is_tax_excluded:
				for line in account_move.invoice_line_ids:
					if rec.amount == account_move.amount_residual:
						raise UserError(_("Amount Due and Paid Amount should not be same in case of Tax excluded...!"))
					else:
						tax_amt = account_move.tax_paid
						amt_tax = rec.amount * (7/100)
						amt = tax_amt - amt_tax
						paid_untax_amt = rec.amount + amt_tax

						if amt_tax >= account_move.tax_paid:
							rec.tax_amount_to_paid = account_move.tax_paid
							rec.amount_to_paid = self.amount
						else:
							rec.tax_amount_to_paid = amt_tax
							rec.amount_to_paid = self.amount
			else:
				paid_amt = account_move.tax_totals.get('amount_total') - account_move.tax_totals.get('amount_untaxed')
				rec.amount_to_paid = 0.0
				rec.tax_amount_to_paid = 0.0
				rec.tax_paid = paid_amt
				amt_tax = rec.amount / (7/100 + 1)
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
					elif rec.amount <= account_move.amount_residual:

						tax_amt = account_move.tax_paid

						cal_untax_amt = rec.amount / (7/100 + 1)
						cal_amt_tax = rec.amount - cal_untax_amt
						tax_due = tax_amt - cal_amt_tax 

						if cal_amt_tax <= account_move.tax_paid:
							rec.tax_amount_to_paid = cal_amt_tax
							rec.amount_to_paid = cal_untax_amt
						else:
							rec.tax_amount_to_paid = cal_amt_tax
							rec.amount_to_paid = self.amount - rec.tax_amount_to_paid

					else:
						raise UserError('You Can not Enter Amount More Than Due Amount')
							
	def _create_payment_vals_from_wizard(self, batch_result):
		res = super(AccountPaymentRegister, self)._create_payment_vals_from_wizard(batch_result)
		res.update({
			'amount_to_paid': self.amount_to_paid,
			'tax_amount_to_paid': self.tax_amount_to_paid,
		})
		if self.is_tax_excluded:
			res.update({
				'amount': self.amount + self.tax_amount_to_paid,
			})

		return res


	def action_create_payments(self):
		res = super(AccountPaymentRegister, self).action_create_payments()
		account_move = self.env['account.move'].search([('id', '=' ,self._context.get('active_id'))])
		# if self.is_tax_excluded and self.amount == account_move.amount_residual:
		# 	raise UserError(_("Amount Due and Paid Amount should not be same in case of Tax excluded...!"))
		for move in account_move:
			move.tax_paid -= self.tax_amount_to_paid

		return res

class Accountpayment(models.Model):
	_inherit = 'account.payment'


	amount_to_paid = fields.Monetary(string='Amount Paid', readonly=True)
	tax_amount_to_paid = fields.Monetary(string='Tax Paid', readonly=True)


class AccountMove(models.Model):
	_inherit = 'account.move'

	tax_paid = fields.Monetary('Tax Paid')
	amount_remain = fields.Monetary('Amount Due', compute='_compute_amount_remain')
	tax_remain = fields.Monetary('Tax Due', compute='_compute_amount_remain')

	@api.onchange('invoice_line_ids')
	def _onchange_tax_paid(self):
		tax = self.tax_totals.get('amount_total') - self.tax_totals.get('amount_untaxed')
		self.tax_paid = tax

	def _compute_amount_remain(self):
		self.amount_remain = self.amount_residual - self.tax_paid
		self.tax_remain = self.tax_paid



