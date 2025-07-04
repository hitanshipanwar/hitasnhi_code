from odoo import fields, models, api, _
from odoo.exceptions import UserError

class PurchaseOrderInherited(models.Model):
	_inherit = 'purchase.order'

	state = fields.Selection(selection_add=[
		('approve_pending','Approve Pending'),
		('approved','Approved'),
		('purchase',),])
	
	product_requirement = fields.Selection(selection=[
							('built_in','Built - In'),
							('loose','Stone'),
							('doors','Doors'),
							('other','Other')])
	department_id = fields.Many2one('hr.department', string="Department", related="user_id.department_id")


	manager_id = fields.Many2one('hr.employee',related="department_id.manager_id")
	is_manager_login = fields.Boolean("Is Manager",compute="_compute_is_manager")

	manager_signature = fields.Binary('Signature', copy=False, attachment=True, max_width=1024, max_height=1024)
	manager_name = fields.Char('Signed By', copy=False)
	manager_signed_on = fields.Datetime('Signed On', help='Date of the signature.', copy=False)
	is_higher = fields.Boolean('Higher',compute="_compute_is_higher")

	def send_for_manager_approval(self):
		if self.amount_total > self.department_id.target and self.state != 'approved':
			self.state = 'approve_pending'
			self.message_post(body="Your purchase order amount is more than your department target amount \n You need Department Manager Approval ")
			approval_id = self.env.ref('crm_design.mail_activity_data_approval')
			approval_id.sudo().name = "Approval"
			self.activity_schedule(
					'crm_design.mail_activity_data_approval',
					user_id=self.manager_id.user_id.id)

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
		for rec in self:
			if self.env.user.id == rec.manager_id.user_id.id:
				rec.is_manager_login = True
			else:
				rec.is_manager_login = False

	
	def action_approve(self):
		return {
			'name': "Approve Quotation",
			'type': 'ir.actions.act_window',
			'view_type': 'form',
			'view_mode': 'form',
			'res_model': 'approve.quotation.wizard',
			'view_id': self.env.ref('crm_design.approve_quotation_view_form').id,
			'target': 'new'
		}

	def action_refuse(self):
		return {
				'name': "Reject Quotation",
				'type': 'ir.actions.act_window',
				'view_type': 'form',
				'view_mode': 'form',
				'res_model': 'reject.quotation.wizard',
				'view_id': self.env.ref('crm_design.reject_quotation_view_form').id,
				'target': 'new'
		}


		
