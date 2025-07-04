from odoo import api, fields, models, _
import json
from collections import defaultdict
from odoo.exceptions import AccessError, MissingError, ValidationError

class AccountMoveInherite(models.Model):
	_inherit = 'account.move'

	is_final_invoice = fields.Boolean("Final Invoice",copy=False)
	receipt_status = fields.Selection([
        ('pending', 'Not Received'),
        ('partial', 'Partially Received'),
        ('full', 'Fully Received'),
    ], string='Receipt Status', compute="_compute_receipt_status")

	def _compute_receipt_status(self):
		for rec in self:
			po = self.env['purchase.order'].search([('id', '=', rec.line_ids.purchase_line_id.order_id.id)])
			rec.receipt_status = po.receipt_status


	state = fields.Selection(selection=[
			('draft', 'Draft'),
			('sent','Send'),
			('approve_pending','Pending'),
			('approved','Approved'),
			('refused','Refused'),
			('posted', 'Posted'),
			('cancel', 'Cancelled'),
		], string='Status', required=True, readonly=True, copy=False, tracking=True,
		default='draft')
	is_manager_login = fields.Boolean(compute='_compute_is_visitor')

	is_visit_invoice = fields.Boolean("Visit Invoice")
	visitor_id = fields.Many2one('res.users')
	appointment_id = fields.Many2one('appointment.visit')
	appointment_access_link = fields.Char('Access Link')
	current_login_id = fields.Boolean(compute="_compute_current_user_id")

	confirmed_by_customer = fields.Boolean(string="Confirmed By Customer", copy=False)
	paymentslip_uploaded = fields.Boolean(string="PaymentSlip Uploaded", copy=False)

	product_requirement = fields.Selection(string="Product Requirements", selection=[
		('built_in','Built - In'),
		('loose','Stone'),
		('doors','Doors'),
		('other','Other')])

	lead_id = fields.Many2one('crm.lead')
	order_id = fields.Many2one('sale.order')

	manager_signature = fields.Binary('Signature', copy=False, attachment=True, max_width=1024, max_height=1024)
	manager_name = fields.Char('Signed By', copy=False)
	manager_signed_on = fields.Datetime('Signed On', help='Date of the signature.', copy=False)
	amount_to_pay = fields.Monetary(string="Amount To Pay",compute="_compute_amount_to_pay")
	is_thai = fields.Boolean(string='Enable Thai')
	payslip_multi_attachments = fields.Many2many('ir.attachment','ir_attachment_pay_ref','account_id','attachment_id', string="Multiple Attchment")

	def button_draft(self):
		self.confirmed_by_customer = False
		self.paymentslip_uploaded = False
		return super().button_draft()

	@api.depends('posted_before', 'state', 'journal_id', 'date')
	def _compute_name(self):
		def journal_key(move):
			return (move.journal_id, move.journal_id.refund_sequence and move.move_type)

		def date_key(move):
			return (move.date.year, move.date.month)

		grouped = defaultdict(  # key: journal_id, move_type
			lambda: defaultdict(  # key: first adjacent (date.year, date.month)
				lambda: {
					'records': self.env['account.move'],
					'format': False,
					'format_values': False,
					'reset': False
				}
			)
		)
		self = self.sorted(lambda m: (m.date, m.ref or '', m.id))
		highest_name = self[0]._get_last_sequence() if self else False

		# Group the moves by journal and month
		for move in self:
			if not highest_name and move == self[0] and not move.posted_before and move.date:
				# In the form view, we need to compute a default sequence so that the user can edit
				# it. We only check the first move as an approximation (enough for new in form view)
				pass
			elif (move.name and move.name != '/'):
				try:
					if not move.posted_before:
						move._constrains_date_sequence()
					# Has already a name or is not posted, we don't add to a batch
					continue
				except ValidationError:
					# Has never been posted and the name doesn't match the date: recompute it
					pass
			group = grouped[journal_key(move)][date_key(move)]
			if not group['records']:
				# Compute all the values needed to sequence this whole group
				move._set_next_sequence()
				group['format'], group['format_values'] = move._get_sequence_format_param(move.name)
				group['reset'] = move._deduce_sequence_number_reset(move.name)
			group['records'] += move

		# Fusion the groups depending on the sequence reset and the format used because `seq` is
		# the same counter for multiple groups that might be spread in multiple months.
		final_batches = []
		for journal_group in grouped.values():
			journal_group_changed = True
			for date_group in journal_group.values():
				if (
					journal_group_changed
					or final_batches[-1]['format'] != date_group['format']
					or dict(final_batches[-1]['format_values'], seq=0) != dict(date_group['format_values'], seq=0)
				):
					final_batches += [date_group]
					journal_group_changed = False
				elif date_group['reset'] == 'never':
					final_batches[-1]['records'] += date_group['records']
				elif (
					date_group['reset'] == 'year'
					and final_batches[-1]['records'][0].date.year == date_group['records'][0].date.year
				):
					final_batches[-1]['records'] += date_group['records']
				else:
					final_batches += [date_group]

		# Give the name based on previously computed values
		for batch in final_batches:
			for move in batch['records']:
				move.name = batch['format'].format(**batch['format_values'])
				batch['format_values']['seq'] += 1
			batch['records']._compute_split_sequence()

		self.filtered(lambda m: not m.name).name = '/'
	
	@api.depends('invoice_payment_term_id')
	def _compute_amount_to_pay(self):
		for record in self:
			record.amount_to_pay = 0
			if record.invoice_payment_term_id:
				for line in record.invoice_payment_term_id.line_ids[0]:
					if line.value == 'percent':
						# invoice_totals = json.loads(self.tax_totals)
						invoice_totals = self.tax_totals
						total = invoice_totals.get('amount_total')
						amount = total*line.value_amount/100
						record.amount_to_pay = amount
					if line.value == 'balance':
						# invoice_totals = json.loads(self.tax_totals)
						invoice_totals = self.tax_totals
						total = invoice_totals.get('amount_total')
						record.amount_to_pay = total
					if line.value == 'fixed':
						record.amount_to_pay = line.value_amount

	def action_invoice_sent(self):
		result = super(AccountMoveInherite,self).action_invoice_sent()
		base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
		base_url += self.get_portal_url()
		result.get('context').update({'my_url':base_url})

		if self.state != 'posted':
			self.state='sent'
		

		return result

	@api.model
	def _compute_current_user_id(self):
		for record in self:
			if record.create_uid.id == self.env.user.id:
				record.current_login_id = True
			else:
				record.current_login_id = False

	def _compute_amount(self):
		res = super(AccountMoveInherite, self)._compute_amount()
		for record in self:
			if record.payment_state == 'paid' and record.is_final_invoice:
				# record.lead_id.action_set_won()
				if self.line_ids and self.line_ids.sale_line_ids and self.line_ids.sale_line_ids.order_id:
					for line in self.line_ids.sale_line_ids:
						for invoice in line.order_id.invoice_ids:
							if invoice.is_final_invoice == True:
								line.order_id.final_paid = True
								fully_paid_status = self.env.ref('crm_design.stage_lead_fully_invoiced')
								line.order_id.opportunity_id.stage_id = fully_paid_status.id

				# if all(invoice.payment_state == 'paid' for invoice in record.order_id.invoice_ids):
				# 	record.order_id.final_paid = True
				# 	fully_paid_status = self.env.ref('crm_design.stage_lead_fully_invoiced')
				# 	record.order_id.opportunity_id.stage_id = fully_paid_status.id
			
			if record.payment_state == 'paid' and record.is_visit_invoice and record.appointment_id:
				email_from = self.env['ir.mail_server'].sudo().search([],limit=1)
				mail_values_user_check = {
				'subject': 'Visit Charges Paid by %s' % (record.partner_id.name) ,
				'email_to':record.visitor_id.partner_id.email,
				'email_from':email_from.smtp_user,
				'body_html': '''<div> Dear <strong> %s </strong>, <br/>
									Site visit charges are paid. <br/>
									Now you can confirm your visit.
								</div>'''
								% (record.visitor_id.partner_id.name)
				}
				create_and_send_email = self.env['mail.mail'].sudo().create(mail_values_user_check).sudo().send()
				self.appointment_id.sudo().message_post(body='Site Visit Charges are paid. Now you can confirm your visit.')
			return res

	@api.model
	def _compute_is_visitor(self):
		quotation_approval_group_id = self.env.ref('crm_design.group_manager_quotation').id
		quotation_manager_ids = self.env['res.users'].search([('groups_id','=',quotation_approval_group_id)])
		for record in self:
			if self.env.uid in quotation_manager_ids.ids:
				record.is_manager_login = True
			else:
				record.is_manager_login = False

	def request_for_approval(self):
		quotation_approval_group_id = self.env.ref('crm_design.group_manager_quotation').id
		quotation_manager_ids = self.env['res.users'].search([('groups_id','=',quotation_approval_group_id)])

		for rec in self:
			rec.state = 'approve_pending'
			for manager in quotation_manager_ids:
					approval_id = self.env.ref('crm_design.mail_activity_data_approval')
					approval_id.sudo().name = "Approval"
					rec.activity_schedule(
						'crm_design.mail_activity_data_approval',
						user_id=manager.id)
			base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
			base_url += rec.get_portal_url()
			email_from = self.env['ir.mail_server'].sudo().search([],limit=1)
			mail_values_user_check = {
				'subject': "Request For Design Approval",
				'email_to':rec.user_id.partner_id.email,
				'email_from':email_from.smtp_user,
				'body_html': '''<div> Dear, %s <br/>
								You have one request for Design Approval <br/>
								Reference %s
								</div>'''%(manager.partner_id.name,base_url)

				}

	def action_approve(self):
		return {
			'name': "Approve Invoice",
			'type': 'ir.actions.act_window',
			'view_type': 'form',
			'view_mode': 'form',
			'res_model': 'approve.quotation.wizard',
			'context': {'current_id': self.id},
			'view_id': self.env.ref('crm_design.approve_quotation_view_form').id,
			'target': 'new'
		}

	def action_refuse(self):
		return {
			'name': "Reject Invoice",
			'type': 'ir.actions.act_window',
			'view_type': 'form',
			'view_mode': 'form',
			'res_model': 'reject.quotation.wizard',
			'context': {'current_id': self.id},
			'view_id': self.env.ref('crm_design.reject_quotation_view_form').id,
			'target': 'new'
		}

	@api.onchange('is_thai')
	def onchange_is_thai_name(self):
		for invoice_line_id in self.invoice_line_ids:
			if self.is_thai:
				name = '[%s] %s' % (invoice_line_id.product_id.default_code,invoice_line_id.product_id.thai_product_name)
				if invoice_line_id.product_id.thai_sale_description:
					name += '\n' + invoice_line_id.product_id.thai_sale_description
				invoice_line_id.name = name
			else:
				if invoice_line_id.partner_id.lang:
					product = invoice_line_id.product_id.with_context(lang=invoice_line_id.partner_id.lang)
				else:
					product = invoice_line_id.product_id
				values = []
				if product.partner_ref:
					values.append(product.partner_ref)
				if invoice_line_id.journal_id.type == 'sale':
					if product.description_sale:
						values.append(product.description_sale)
				elif invoice_line_id.journal_id.type == 'purchase':
					if product.description_purchase:
						values.append(product.description_purchase)
				invoice_line_id.name = '\n'.join(values)


class AccountMoveLine(models.Model):
	_inherit = 'account.move.line'

	is_thai = fields.Boolean(string='Is Thai',related='move_id.is_thai')