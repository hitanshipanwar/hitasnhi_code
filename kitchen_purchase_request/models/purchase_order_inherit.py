from odoo import fields, models, api, _
from odoo.exceptions import UserError

class PurchaseOrderInherited(models.Model):
	_inherit = 'purchase.order'

	state = fields.Selection(selection_add=[
		('approve_pending','Approve Pending'),
		('approved','Approved'),
		('purchase',),])
	
	product_requirement = fields.Selection(selection=[
							('low_value','Low Value'),
							('raw_material','Raw Material'),
							('accessory','Accessory'),
							('equipment','Equipment')] ,string="Product Category")
	department_id = fields.Many2one('hr.department', string="Department", related="user_id.department_id")


	manager_id = fields.Many2one('hr.employee',related="department_id.manager_id")
	is_manager_login = fields.Boolean("Is Manager",compute="_compute_is_manager")

	manager_signature = fields.Binary('Signature', copy=False, attachment=True, max_width=1024, max_height=1024)
	manager_name = fields.Char('Signed By', copy=False)
	manager_signed_on = fields.Datetime('Signed On', help='Date of the signature.', copy=False)
	is_higher = fields.Boolean('Higher',compute="_compute_is_higher")

	def send_for_manager_approval(self):
		# if self.amount_total > self.department_id.target and self.state != 'approved':
		if self.state != 'approved':
			self.state = 'approve_pending'
			self.message_post(body="Your purchase order amount is more than your department target amount \n You need Department Manager Approval ")
				
			purchase_department = self.env.ref('kitchen_purchase_request.purchase_department_PD')
			
			self.activity_feedback('kitchen_purchase_request.mail_activity_data_purchase_user_approval', user_id=self.user_id.id)
			# employee_ids = self.env['hr.employee'].sudo().search([('department_id','=',purchase_department.id)])
			if purchase_department.manager_id:
					self.activity_schedule('kitchen_purchase_request.mail_activity_data_purchase_user_approval', user_id=purchase_department.manager_id.user_id.id)


			# self.activity_schedule(
			# 		'crm_design.mail_activity_data_approval',
			# 		user_id=self.manager_id.user_id.id)

	@api.model
	def create(self, values):
		res = super(PurchaseOrderInherited, self).create(values)
		if res.manager_id:
			purchase_user_group = self.env.ref('purchase.group_purchase_user', raise_if_not_found=False)
			purchase_manager_group = self.env.ref('purchase.group_purchase_manager', raise_if_not_found=False)
			if purchase_user_group:
				purchase_user_group.sudo().write({'users': [(4, res.manager_id.user_id.id)]})
			if purchase_manager_group:
				purchase_manager_group.sudo().write({'users': [(4, res.manager_id.user_id.id)]})
		return res


	@api.depends('amount_total')
	def _compute_is_higher(self):
		for record in self:
			if record.amount_total > record.department_id.target:
				record.is_higher = True
			else:
				record.is_higher = False

	@api.model
	def _compute_is_manager(self):
		purchase_department = self.env.ref('kitchen_purchase_request.purchase_department_PD')
		for rec in self:
			if purchase_department.manager_id:
				if self.env.user.id == purchase_department.manager_id.user_id.id:
					rec.is_manager_login = True
				else:
					rec.is_manager_login = False
			else:
				rec.is_manager_login = False

	def approve_rfq(self):
		for rec in self:
			if not self.multi_attachments:
				raise UserError(_("Insert Atleast one Attachment..."))
			if rec.purchase_request_id:
				purchase_user_group = self.env.ref('purchase.group_purchase_user', raise_if_not_found=False)

				if purchase_user_group:
					for user in purchase_user_group.users:
						rec.purchase_request_id.activity_feedback(['kitchen_purchase_request.mail_activity_data_purchase_user_approval'], user_id=user.id)
			rec.state = 'approve_pending'
			purchase_department = self.env.ref('kitchen_purchase_request.purchase_department_PD')
			if purchase_department and purchase_department.manager_id:
					self.activity_schedule('kitchen_purchase_request.mail_activity_data_purchase_department_manager_approval', user_id=purchase_department.manager_id.user_id.id)
	
	def button_confirm(self):
		for order in self:
			if order.state not in ['draft', 'sent','approve_pending']:
				continue
			order._add_supplier_to_product()
			# Deal with double validation process
			if order._approval_allowed():
				order.button_approve()
			else:
				order.write({'state': 'to approve'})
			if order.partner_id not in order.message_partner_ids:
				order.message_subscribe([order.partner_id.id])
		return True

	def action_approve(self):
		return {
			'name': "Approve Quotation",
			'type': 'ir.actions.act_window',
			'view_type': 'form',
			'view_mode': 'form',
			'res_model': 'approve.rfq.wizard',
			'view_id': self.env.ref('kitchen_purchase_request.approve_rfq_wizard_view_form').id,
			'target': 'new'
		}

	def action_refuse(self):
		return {
				'name': "Reject Quotation",
				'type': 'ir.actions.act_window',
				'view_type': 'form',
				'view_mode': 'form',
				'res_model': 'reject.rfq.wizard',
				'view_id': self.env.ref('kitchen_purchase_request.reject_rfq_quotation_view_form').id,
				'target': 'new'
		}
