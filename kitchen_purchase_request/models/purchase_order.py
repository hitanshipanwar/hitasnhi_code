from odoo import fields, models, api, _
from odoo.exceptions import UserError

class PurchaseOrder(models.Model):
	_inherit = "purchase.order"

	purchase_request_id = fields.Many2one('purchase.request',string='Request Order')
	count_purchase_req = fields.Integer("Count Purchase", compute="compute_purchase_request")
	urgency = fields.Selection([('very_urgent', 'Very Urgent'),('within_1_week','Within 1 Week'),('standard_2_weeks','Standard 2 Weeks'),('imported','Imported')])
	mark_as_sent = fields.Boolean(string="Mark RFQ as Send", readonly=True)
	mark_po_as_sent = fields.Boolean(string="Mark PO as Send", readonly=True)
	remarks = fields.Text("Remarks")
	multi_attachments = fields.Many2many('ir.attachment','ir_attachment_purchase_ref','purchase_id','attachment_id',string="Multiple Attchment")
	sale_order_ref_id = fields.Many2one('sale.order', string="Sale Order Reference", help="To Identify the Reference SaleOrder for this Purchase")
	payment_slip = fields.Many2many('ir.attachment', string="Payment Slip")
	suggested_vendor = fields.Char(string="Suggested Vendor")

	def write(self,vals):
		res = super(PurchaseOrder, self).write(vals)
		if 'remarks' in vals:
			if self.purchase_request_id:
				self.purchase_request_id.remarks = self.remarks
		if 'sale_order_ref_id' in vals:
			if self.purchase_request_id:
				self.purchase_request_id.sale_order_ref_id = self.sale_order_ref_id.id
		return res

	def action_create_invoice(self):
		rtn = super(PurchaseOrder, self).action_create_invoice()
		if not self.payment_slip:
			raise UserError(_("Insert Payment Slip..."))
		return rtn


	@api.onchange('sale_order_ref_id')
	def onchange_sale_order_ref_id(self):
		for rec in self:
			if rec.purchase_request_id:
				rec.purchase_request_id.sale_order_ref_id = rec.sale_order_ref_id.id

	def action_mark_as_send(self):
		# for rec in self:
		#     rec.mark_as_sent = True
		#     rec.message_post(body='Sent to customer')
		ir_model_data = self.env['ir.model.data']
		try:
			if self.state not in ['purchase']:
				self.mark_as_sent = True
				self.message_post(body='Sent to customer')
				template_id = self.env.ref('purchase.email_template_edi_purchase')
			else:
				self.mark_po_as_sent = True
				self.message_post(body='Sent to customer')
				template_id = self.env.ref('purchase.email_template_edi_purchase_done')
		except ValueError:
			template_id = False
		if template_id:
			template_id.send_mail(
				self.id,
				force_send=True,
				email_layout_xmlid="mail.mail_notification_layout_with_responsible_signature",
				email_values={'email_to': self.env.user.email, 'recipient_ids': []},
			)

	def action_mark_po_as_send(self):
		for rec in self:
			rec.mark_po_as_sent = True
			rec.message_post(body='Sent to customer')

	def action_rfq_send(self):
		res = super(PurchaseOrder, self).action_rfq_send()
		ir_model_data = self.env['ir.model.data']
		if self.state == 'purchase':
			template_id = ir_model_data._xmlid_lookup('purchase.email_template_edi_purchase_done')[2]
			res.get('context').update({'default_template_id':template_id})
		return res
	
	@api.depends('purchase_request_id')
	def compute_purchase_request(self):
		for record in self:
			if record.purchase_request_id:
				record.count_purchase_req = 1
			else:
				record.count_purchase_req = 0

	@api.model
	def create(self, vals):
		res = super(PurchaseOrder, self).create(vals)
		if self._context.get('active_model') == 'purchase.request' and self._context.get('active_id'):
			request_id = self.env['purchase.request'].browse(self._context.get('active_id'))
			request_id.purchase_id = res.id
			for rec in request_id:
				rec.state = 'rfq'
			if request_id.state == 'rfq':
				request_id.sudo().message_post(body="RFQ Is Generated For Your Request")

		for line in res.order_line:
			if line.pr_line_id:
				line.pr_line_id.combine_rfq_done = True

		
		return res

	def button_cancel(self):
		res = super(PurchaseOrder, self).button_cancel()
		for rec in self.order_line:
			if rec.pr_line_id:
				rec.pr_line_id.combine_rfq_done = False

		return res

	def button_draft(self):
		res = super(PurchaseOrder, self).button_draft()
		for rec in self.order_line:
			if rec.pr_line_id:
				rec.pr_line_id.combine_rfq_done = True

		return res

	def open_request_order(self):
		ctx = dict(self.env.context or {})
		return {
			'name': "RFQ",
			'type': 'ir.actions.act_window',
			'view_type': 'form',
			'view_mode': 'form',
			'res_model': 'purchase.request',
			'res_id' : self.purchase_request_id.id,
			'context': ctx,
			# 'view_id': self.env.ref('kitchen_purchase_request.approve_purchase_request_view_form').id,
			# 'target': 'new'
		}

class StockMoveInherited(models.Model):
	_inherit = 'stock.move'

	@api.onchange('quantity_done')
	def _onchange_quantity_done(self):
		if self.picking_id.picking_type_id.code != 'internal':
			if self.quantity_done > self.product_uom_qty:
				raise UserError('You Can Not Add More Quantity From Demanded')
