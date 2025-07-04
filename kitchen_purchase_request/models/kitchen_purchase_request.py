from odoo import fields, models, api, _
from odoo.exceptions import UserError
from odoo.tools.misc import get_lang
import operator

class PurchaseRequest(models.Model):
	_name = "purchase.request"
	_inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin', 'utm.mixin']
	_description = "Purchase Request"
	_rec_name = "name"

	_STATES = [
		("draft", "Draft"),
		("to_approve", "To be approved"),
		("approved", "Approved"),
		("rejected", "Rejected"),
		("rfq", "RFQ"),
		("done", "Done"),
	]
	po_count = fields.Integer(string="Purchase Order", compute='_get_purchase_order')

	is_thai = fields.Boolean(string='Enable Thai')

	attachment_ids = fields.Many2many('ir.attachment', 'ir_attachmnet_pr_ref', 'purchase_request_id','make_purchase_order_id', string="Attachments")
	remarks = fields.Text(string="Remarks")
	
	def _get_purchase_order(self):
		order = self.env['purchase.order'].search([('purchase_request_id', '=', self.id)])
		count = []
		for rec in order:
			count.append(rec)
		self.po_count = len(count)

	@api.model
	def _my_department_approver(self):
		for rec in self:
			return rec.employee_department_id.manager_id.user_id.id or False

	# def _search(self, args, offset=0, limit=None, order=None, count=False, access_rights_uid=None):
	#     department_id = self.env['hr.department'].search([('name', 'ilike', 'Purchase Department')])
	#     user_ids = department_id.mapped('member_ids.user_id').ids
	#     user_ids.append(department_id.manager_id.user_id.id)
	#     if self.env.is_admin():
	#         args = args
	#     else:
	#         print("Else -------------------------------------------- ")
	#         args = ('|', ('create_uid', '=', self.env.user.id), ('assigned_to', '=', self.env.user.id))
	#         if self.env.user.id in user_ids:
	#             print("Purchase Users---------------------------------- ")
	#             args = ('|', '|', ('create_uid', '=', self.env.user.id), ('assigned_to', '=', self.env.user.id), ('state','=','approved'))
	#     print("Args------------------------ ", args)
	#     return super(PurchaseRequest, self)._search(args, offset=offset, limit=limit, order=order, count=count, access_rights_uid=access_rights_uid)


	name = fields.Char('Request Reference', required=True, index=True, copy=False, default='New', tracking=True,)
	
	current_user_id = fields.Many2one('res.users', default=lambda self: self.env.uid)
	employee_id = fields.Many2one("hr.employee",string="Employee Name",related="current_user_id.employee_id", readonly=True)
	employee_department_id = fields.Many2one("hr.department",string="Employee Department",related="current_user_id.department_id")
	
	request_date = fields.Date(string="Date", default=fields.Date.today())
	notes = fields.Html(string="Notes")
	assigned_to = fields.Many2one("res.users",
		string="Approver",
		tracking=True,
		related="employee_department_id.manager_id.user_id",
	)
	urgency = fields.Selection([('very_urgent', 'Very Urgent'),('within_1_week','Within 1 Week'),('standard_2_weeks','Standard 2 Weeks'),('imported','Imported')])
	state = fields.Selection(selection=_STATES,
		string='Status', required=True, readonly=True, copy=False, tracking=True,
		default='draft')

	is_manager_login = fields.Boolean(compute='_compute_is_manager')
	manager_signature = fields.Binary('Signature', copy=False, attachment=True, max_width=1024, max_height=1024)
	purchase_id = fields.Many2one('purchase.order', string="Purchase Id")
	sale_order_ref_id = fields.Many2one('sale.order', string="Sale Order Reference")
	combine_rfq = fields.Boolean(string="Combined RFQ", compute="compute_combine_rfq", store=True, copy=False)

	# @api.model
	# def create(self):
	# 	print('**********************************************')
	# 	# if not values.get('login', False):
	# 	res = super(PurchaseRequest, self).create()
	# 	print('create method calling  >>>>>>>>>>>>>>>>>>>>>>')
	# 	if self.env.user.has_group('sales_team.group_sale_salesman'):
	# 	 self.env['res.users'].create({
	# 	 'groups_id': 'sales_team.group_sale_salesman_all_leads',
	# 	 })
	# 	return res

	# def _default_order(self):
	# 	orders =  self.env['sale.order'].sudo().search([]).ids
	# 	print('>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>', orders)
	# 	return orders

	# @api.onchange('sale_order_ref_id')
	# def onchange_sale_order_ref_id(self):
	# 	sale_orders = self.env['sale.order'].sudo().search([])
	# 	res = {'domain': {'sale_order_ref_id': []}}
	# 	print(">>>>>>>>>>>hhhhhhhhhhhhhh>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>", sale_orders)
	# 	res['domain']['sale_order_ref_id'] = [('id', 'in', sale_orders.ids)]
	# 	print('res for sale orser ref >>>>>>>>>>>>>>>>>>>>>>>>>>>', res)
	# 	# domain = {'sale_order_ref_id': [('id', 'in', sale_orders.ids)]}
	# 	return res

	# @api.model
	# def view_header_get(self, view_id, view_type):
	# 	print('\n\n\n\n>>>>>>>>>>>>>>>> \n\n', self._context)
	# 	if self._context.get('sale_order_ref_id'):
	# 		return _(
	# 			'Sale Orders: %(sale_orders)s',
	# 			sale_orders=self.env['sale.order'].browse(self.env.context['sale_order_ref_id']).id,
	# 		)
	# 	return super().view_header_get(view_id, view_type)

	# # @api.depends('sale_order_ref_id')
	# def _search(self, args, offset=0, limit=None, order=None, count=False, access_rights_uid=None):
	# 	print('\n\n\n\n\n\n\n\n\n\n>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n', self._context)
	# 	# TDE FIXME: strange
	# 	if self._context.get('search_default_sale_order_ref_id'):
	# 		name = self._context.get('search_default_sale_order_ref_id')
	# 		print('=======================================================0,', name)
	# 		args.append((('sale_order_ref_id', 'child_of', self._context['search_default_sale_order_ref_id'])))
	# 	return super(PurchaseRequest, self)._search(args, offset=offset, limit=limit, order=order, count=count, access_rights_uid=access_rights_uid)


	# @api.model
	# def _search(self, args, offset=0, limit=None, order=None, count=False, access_rights_uid=False):
	# 	all_sale_orders = self.env['sale.order'].sudo().search([])
	# 	# self.sale_order_ref_id = all_sale_orders.id
	# 	# print('>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>', all_sale_orders)
	# 	print('>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>', args)
	# 	return super(PurchaseRequest, self)._search(args, offset=offset, limit=limit, order=order, count=count, access_rights_uid=access_rights_uid)


	@api.depends('product_request_ids.combine_rfq')
	def compute_combine_rfq(self):
		for rec in self:
			rec.combine_rfq = False
			combine_rfq_id = rec.product_request_ids.filtered(
					lambda l: l.combine_rfq 
				)
			if len(combine_rfq_id) >= 1:
				# lines = rec.product_request_ids.mapped('combine_rfq_done')
				# print('---------------------------------------------------->2', lines)
				# if not any(combine_rfq_done for combine_rfq_done in rec.product_request_ids.mapped('combine_rfq_done')):
				# if False in lines:
					# print('>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
					# for combine in combine_rfq_id:
						# if not combine.combine_rfq_done:
					#         print('==========================================')
				rec.combine_rfq = True

			# for line in rec.product_request_ids:
			#     po = self.env['purchase.order'].search([('order_line.combine_rfq_done')])
			#     print('>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
			#     if line.combine_rfq_done:
			#         print('kkkkkkkkkkkkkkkkkkkkkkkkkkkk')
			#         self.combine_rfq = False

	@api.onchange('sale_order_ref_id')
	def onchange_sale_order_ref_id(self):
		for rec in self:
			if rec.purchase_id:
				rec.purchase_id.sale_order_ref_id = rec.sale_order_ref_id.with_context(sale_show_partner_name=True).id

		# To Get All Sale orders
		# sale_orders = self.env['sale.order'].sudo().search([])
		# print(">>>>>>>>>>>hhhhhhhhhhhhhh>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>", sale_orders)
		# # res = {'domain': {'sale_order_ref_id': []}}
		# # res['domain']['sale_order_ref_id'] = [('id', 'in', sale_orders.ids)]
		# # print('res for sale orser ref >>>>>>>>>>>>>>>>>>>>>>>>>>>', res)

		# # domain = {'sale_order_ref_id': [('id', 'in', sale_orders.ids)]}
		# # return res

		# domain = {'sale_order_ref_id': [('id', 'in', sale_orders.ids)]}
		# print("domain ==============================", domain)
		# return {'domain': domain}

	product_request_ids = fields.One2many('product.request.line', 'product_request_id', string="Product Request Id")
	@api.onchange('product_request_ids')
	def _onchange_index_lines(self):
		number = 0
		for line in self.product_request_ids:
			number += 1
			line.item_no = number

	@api.model
	def create(self, vals):
		if vals.get('name', 'New') == 'New':
			vals['name'] = self.env['ir.sequence'].next_by_code('purchase.request') or '/'
		
		res = super(PurchaseRequest,self).create(vals)
		number = 0
		for line in res.product_request_ids:
			number += 1
			line.item_no = number
		
		# Add Approver As Follower
		# if vals["assigned_to"]:
			# res.message_subscribe(partner_ids=[vals["assigned_to"]])
		# if res.assigned_to:
		#    res.message_subscribe(partner_ids=[res.assigned_to.id])
		return res

	def write(self,vals):
		res = super(PurchaseRequest, self).write(vals)
		number = 0
		for line in self.product_request_ids:
			number += 1
			line.item_no = number
			
		# if 'remarks' in vals or 'sale_order_ref_id' in vals:
		#     orders = self.env['purchase.order'].search([('purchase_request_id', '=', self.id)])
		#     for order in orders:
		#         order.remarks = self.remarks
		#         order.sale_order_ref_id = self.sale_order_ref_id.id
		return res

	@api.model
	def _compute_is_manager(self):
		for record in self:
			if record.env.uid in record.assigned_to.ids:
				record.is_manager_login = True
			else:
				record.is_manager_login = False


	def action_send_request(self):
		self.activity_schedule('kitchen_purchase_request.mail_activity_data_department_manager_approval',
						user_id=self.assigned_to.id)
		if self.state == "draft":
			self.state = 'to_approve'


	def action_approve(self):
	   
		# if self.employee_department_id.manager_id:
		#     purchase_user_group = self.env.ref('purchase.group_purchase_user', raise_if_not_found=False)
		#     purchase_manager_group = self.env.ref('purchase.group_purchase_manager', raise_if_not_found=False)
		#     if purchase_user_group:
		#         purchase_user_group.sudo().write({'users': [(4, self.employee_department_id.manager_id.user_id.id)]})
		#     if purchase_manager_group:
		#         purchase_manager_group.sudo().write({'users': [(4, self.employee_department_id.manager_id.user_id.id)]})

		context = {
			'default_purchase_request_id': self.id,
			'default_department_id': self.employee_department_id.id,
			# 'quotation_only': False
		}
		return {
			'name': "Purchase Request",
			'type': 'ir.actions.act_window',
			'view_type': 'form',
			'view_mode': 'form',
			'res_model': 'approve.purchase.request.wizard',
			# 'context': context,
			'view_id': self.env.ref('kitchen_purchase_request.approve_purchase_request_view_form').id,
			'target': 'new'
		}


	def action_reject(self):

		return {
			'name': "Purchase Request",
			'type': 'ir.actions.act_window',
			'view_type': 'form',
			'view_mode': 'form',
			'res_model': 'reject.purchase.request.wizard',
			# 'res_id': self.id,
			# 'context': context,
			'view_id': self.env.ref('kitchen_purchase_request.reject_purchase_request_view_form').id,
			'target': 'new'
		}

	def make_purchase_order(self):
		order_line_record = []
		partners = []
		all_lines = self.product_request_ids.filtered(lambda l: l.combine_rfq and not l.combine_rfq_done)
		no_line = self.product_request_ids.mapped('combine_rfq')
		po = self.env['purchase.order'].search([('purchase_request_id', '=', self.id)])
		po_line = po.order_line.pr_line_id
		po_line_status = po_line.product_request_id
		
		# Check All Partners Are Same Or Not.
		partner_list = []
		lists = []
		is_same = False
		for rec in self.product_request_ids:
			if rec.combine_rfq and not rec.combine_rfq_done:
				partner_list.append(rec.partner_id.id)
				lists = list(set(partner_list))

		# Free From Text Vendor List
		partner_name_list = []
		for rec in self.product_request_ids:
			if rec.combine_rfq and not rec.combine_rfq_done:
				if rec.partner_name:
					partner_name_list.append(rec.partner_name)

		if lists:
			is_same = operator.countOf(lists, lists[0]) == len(lists)
		else:
			is_same = True
		if not is_same:
			raise UserError(_("To create combine PO, all suppliers should be same"))

		# Check if Any lines selected
		if no_line and operator.countOf(no_line, False) == len(no_line):
			raise UserError(_("Select lines to combine"))

		else:
			if all_lines:
				for record in self.product_request_ids:
					if record.combine_rfq and not record.combine_rfq_done:
						order_line_record.append((0,0,{
								'pr_line_id': record.id,
								'standard_type': record.product_type,
								'product_id': record.product_id.id,
								'name': record.product_name if not record.product_id else '',
								'product_uom':record.uom_id.id,
								'urgency' : record.urgency,
								'product_qty' : record.amount_required,}))
			else:
				raise UserError(_('Already RFQ Created'))

		
		ctx = dict(self.env.context or {})
		ctx.update({
			# 'default_suggested_vendor': self.product_request_ids.partner_name,
			'default_suggested_vendor': partner_name_list[0] if partner_name_list else False,
			'default_partner_id': partner_list[0] if partner_list else False,
			'default_purchase_request_id': self.id,
			'default_is_thai': self.is_thai,
			'default_sale_order_ref_id' : self.sale_order_ref_id.id,
			'default_remarks': self.remarks,
			'default_department_id': self.employee_department_id.id,
			'default_order_line' : order_line_record,
			'default_urgency': self.urgency,
			'quotation_only': False,
			'default_multi_attachments': self.attachment_ids.ids,
		})
		return {
			'name': "RFQ",
			'type': 'ir.actions.act_window',
			'view_type': 'form',
			'view_mode': 'form',
			'res_model': 'purchase.order',
			'context': ctx,
			'target': 'new'

		}


	# def open_purchase_order(self):
	#     print('------------------------')
	#     rec = self.env['purchase.request']
	#     ctx = dict(rec.env.context or {})
	#     po = self.env['purchase.order'].search([('id', '=',self.purchase_id.id)])
	#     print('-----------popo-------------',po.id)
	#     return {
	#         'name': "RFQ",
	#         'type': 'ir.actions.act_window',
	#         'view_type': 'form',
	#         'view_mode': 'form',
	#         'res_model': 'purchase.order',
	#         # 'res_id' : self.product_request_id.purchase_id.id,
	#         'res_id' : po.id,
	#         'context': ctx,
	#     }


	def open_purchase_order(self):
		order = self.env['purchase.order'].search([('purchase_request_id', '=', self.id)])
		ctx = dict(self.env.context or {})
		# for rec in order:
		return {
			"name": "RFQ",
			"view_mode": "tree,form",
			"res_model": "purchase.order",
			"view_id": False,
			"type": "ir.actions.act_window",
			"domain": [("id", "in", order.ids)],
		}

class PurchaseProductRequest(models.Model):
	_name = "product.request.line"

	product_request_id = fields.Many2one('purchase.request', string="Product Request Id")
	item_no = fields.Integer('Item No', readonly=True)
	product_name = fields.Char('Product Name')
	# product_name = fields.Char('Product Name', compute='_compute_product_name', inverse='_inverse_product_description')
	product_id = fields.Many2one('product.product', string="Product Code")
	uom_id = fields.Many2one('uom.uom', string="UOM", domain="[('category_id', '=', uom_category_id)]")
	uom_category_id = fields.Many2one(related='product_id.uom_id.category_id')
	amount_required = fields.Float('Amount Required')
	urgency = fields.Selection([('very urgent', 'Very Urgent'),('within 1 week','Within 1 Week'),('standard 2 weeks','Standard 2 Weeks')])
	remark = fields.Text('Remark')
	product_type = fields.Selection(selection=[('standard','Standard'),('non_standard','Non Standard')])
	partner_name = fields.Char(string="Vendor")
	partner_id = fields.Many2one('res.partner', string="Vendor")
	# partner_ids = fields.Many2many('res.partner',compute="_partner_selection", string="Vendor")
	combine_rfq = fields.Boolean(string="Combined RFQ")
	combine_rfq_done = fields.Boolean(string="RFQ Done")
	is_thai = fields.Boolean(string='Is Thai', related="product_request_id.is_thai")
	is_editable = fields.Boolean(default=False)

	def _get_product_purchase_description(self, product_lang):
		self.ensure_one()
		product_name = product_lang.display_name
		if self.product_type == 'standard':
			if product_lang.description_purchase:
				product_name += '\n' + product_lang.description_purchase
		else:
			product_name = product_lang.description_purchase

		return product_name

	# @api.depends('product_id')
	# def _compute_product_name(self):
	#     for line in self:
	#         if not line.product_id:
	#             continue
	#         params = {'product_request_id': line.product_request_id}
	#         seller = line.product_id._select_seller(
	#             partner_id=line.partner_id,
	#             quantity=line.amount_required,
	#             date=line.product_request_id.request_date,
	#             uom_id=line.uom_id,
	#             params=params)
	#         # line.product_name = ''
	#         # if line.product_type == 'standard':
	#         default_names = []
	#         vendors = line.product_id._prepare_sellers({})
	#         for vendor in vendors:
	#             product_ctx = {'seller_id': vendor.id, 'lang': get_lang(line.env, line.partner_id.lang).code}
	#             default_names.append(line._get_product_purchase_description(line.product_id.with_context(product_ctx)))
	#         if not line.product_name or line.product_name in default_names:
	#             product_ctx = {'seller_id': seller.id, 'lang': get_lang(line.env, line.partner_id.lang).code}
	#             line.product_name = line._get_product_purchase_description(line.product_id.with_context(product_ctx))
	#         # else:
	#         #     line.is_editable = True

	# def _inverse_product_description(self):
	#     for line in self:
	#         if not line.product_type == 'standard':
	#             line.product_id.description_purchase = line.product_name 



	# @api.depends('product_id')
	# def _partner_selection(self):
	#     partners = []
	#     for rec in self:
	#         rec.partner_ids = rec.product_id.seller_ids.partner_id.ids

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
					'name': "RFQ",
					'type': 'ir.actions.act_window',
					'view_type': 'form',
					'view_mode': 'form',
					'res_model': 'purchase.order',
					'context': ctx,
					'target': 'new'

				}
