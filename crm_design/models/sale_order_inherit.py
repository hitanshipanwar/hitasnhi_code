from odoo import fields, http, SUPERUSER_ID, _
from odoo import api, fields, models, tools, SUPERUSER_ID, _, Command
from odoo.exceptions import AccessError, MissingError, ValidationError,UserError
import base64
import hashlib
import io
import itertools
import logging
import mimetypes
import os
import re
import uuid
import time
from collections import defaultdict
from PIL import Image

from odoo.tools import config, human_size, ustr, html_escape, ImageProcess, str2bool
from odoo.tools.mimetypes import guess_mimetype
from odoo.osv import expression
from datetime import datetime,timedelta
from odoo.http import request
from odoo.http import content_disposition, Controller, request, route
from odoo.tools.misc import get_lang
from odoo.osv import expression
from string import digits

READONLY_FIELD_STATES = {
	state: [('readonly', True)]
	for state in {'sale', 'done', 'cancel'}
}

class SaleOrderInherited(models.Model):
	_inherit = "sale.order"

	# partner_id = fields.Many2one('res.partner',string="Customer")
	display_name = fields.Char(compute='_compute_display_sale_name')
	partner_id = fields.Many2one(string="Customer",
	required=True, readonly=False, change_default=True, index=True,
	tracking=1,
	states=READONLY_FIELD_STATES,
	domain="[('customer_rank', '>', 0), ('company_id', 'in', (False, company_id))]")

	platform_ids = fields.Many2many('platform.crm')
	product_requirement = fields.Selection(string="Product Requirements",
		selection=[('built_in','Built - In'),('loose','Stone'),('doors','Doors'),('other','Other')], required=True, default='built_in')
	accessories = fields.One2many('crm.lead.accessories','sale_ref_id')
	sizing = fields.Char(string="Subject")

	need_design = fields.Boolean(string="Need Design")
	designer_id = fields.Many2one('res.users',string="Designer",
		domain=lambda self: [("groups_id", "=", self.env.ref( "crm_design.group_allow_to_add_design" ).id)])

	state = fields.Selection(selection_add=[
		('approve_pending','Pending'),
		('approved','Approved'),
		('refused','Refused'),
		('sent','Design/Quotation Sent'),
		('design_confirm','Design Confirm'),
		('site_visit','Site Visit'),
		('site_visited','Visited'),
		('final_approve_pending','Final Pending'),
		('final_approved','Final Approved'),
		('final_refused','Final Refused'),
		('sale',)])

	previous_state = fields.Char("Previous State", default='draft')

	attachment_ids = fields.One2many('ir.attachment','sale_order_attach_ref')

	appoinment_to_visit = fields.Boolean(string='Appointment To Visit Site', copy=False)
	appointment_date = fields.Datetime(string="Appointment Date",readonly=True)
	customer_id = fields.Many2one('res.partner',string="Customer")
	visitor_id = fields.Many2one('res.users',string="Visitor",readonly=True)
	visit_charge = fields.Float(string="Visit Charge")

	material_specification = fields.Text(string="Material Specification",translate=True)
	job_type = fields.Char(string="Job Type",translate=True)
	gloss = fields.Char(string="Gloss/Matt",translate=True)
	code = fields.Char(string="Code",translate=True)

	is_quotation_approved = fields.Boolean(string="Quotation Approved",copy=False)
	is_manager_login = fields.Boolean(compute='_compute_is_visitor')
	is_designer_login = fields.Boolean(compute='_compute_is_designer')

	design_count = fields.Integer(compute="_compute_design_count")
	current_login_id = fields.Boolean(compute="_compute_current_user_id")
	is_final_invoice_created = fields.Boolean('Final Inv Created', copy=False)

	multi_attachments = fields.Many2many('ir.attachment','ir_attachment_design_ref','sale_id','attachment_id',string="Multiple Attachment")
	multi_attachments_ids = fields.One2many("ir.attachment", 'attch_sale_ref_id', string="Attachments")

	term_based_amount = fields.Monetary(string='Total')
	remain_amount = fields.Monetary(string="Remain Amount")

	confirmed_by_customer = fields.Boolean(string="Confirmed By Customer", copy=False)

	final_paid = fields.Boolean(string="Final Invoice Paid", copy=False)
	designer_notified = fields.Boolean(string="Designer Notified", copy=False)
	saleperson_notified = fields.Boolean(string="SalesPerson Notified", copy=False)
	visiter_notes = fields.Html(string='Visitor Notes')
	note = fields.Html('Terms and conditions')

	precent_digits = fields.Float(string="Calculator Sale %")
	sale_per_amt = fields.Float(string="Calculator Amount", compute="_compute_sale_percentage")

	@api.depends('precent_digits')
	def _compute_sale_percentage(self):
		for rec in self:
			rec.sale_per_amt = rec.amount_total * rec.precent_digits / 100 



	# @api.depends('state', 'order_line.invoice_status')
	# def _compute_invoice_status(self):
	# 	super()._compute_invoice_status()
	# 	for order in self:
	# 		if order.invoice_status == 'invoiced':
	# 			fully_paid_status = self.env.ref('crm_design.stage_lead_fully_invoiced')
	# 			order.opportunity_id.stage_id = fully_paid_status.id

	@api.model
	def _compute_display_sale_name(self):
		for rec in self:
			name = ''
			if rec.name:
				name += rec.name
			if rec.partner_id:
				name += "- " + rec.partner_id.name
			rec.display_name = name

	manager_info_ids = fields.One2many('saleorder.manager','manager_info_id',string="Manager Information")
	# manager_signature = fields.Binary('Signature', copy=False, attachment=True, max_width=1024, max_height=1024)
	# manager_name = fields.Char('Signed By', copy=False)
	# manager_signed_on = fields.Datetime('Signed On', help='Date of the signature.', copy=False)

	extra_notes = fields.Html(string="Descriptions")
	mark_as_sent = fields.Boolean(string="Mark RFQ as Send", readonly=True, copy=False)
	is_thai = fields.Boolean(string='Enable Thai')
	is_custom_order = fields.Boolean(string='Custom Order')

	@api.model
	def action_share_design(self):
		action = self.env["ir.actions.actions"]._for_xml_id("portal.portal_share_action")
		action['context'] = {'active_id': self.env.context['active_id'],
							'active_model': self.env.context['active_model'],
							'share_design_link' : True}
		return action

	@api.depends('partner_id')
	def _compute_pricelist_id(self):
		for order in self:
			if not order.partner_id:
				order.pricelist_id = self.env.ref('product.list0')
				# continue
			else:
				order = order.with_company(order.company_id)
				order.pricelist_id = order.partner_id.property_product_pricelist

	@api.onchange('is_thai')
	def onchange_is_thai_name(self):
		for order_line_id in self.order_line:
			if self.is_thai:
				name = '[%s] %s' % (order_line_id.product_id.default_code,order_line_id.product_id.thai_product_name)
				if order_line_id.product_id.thai_sale_description:
					name += '\n' + order_line_id.product_id.thai_sale_description
			else:
				name = '[%s] %s' % (order_line_id.product_id.default_code,order_line_id.product_id.name)
				if order_line_id.product_id.description_sale:
					name += '\n' + order_line_id.product_id.description_sale
			order_line_id.name = name

	def action_mark_as_send(self):
		ir_model_data = self.env['ir.model.data']
		base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
		base_url += self.get_portal_url()
		# result.get('context').update({'my_url':base_url})
		try:
			if self.state not in ['sale']:
				self.mark_as_sent = True
				self.message_post(body='Sent to customer')
				template_id = self.env.ref('sale.email_template_edi_sale')
			else:
				self.mark_as_sent = True
				self.message_post(body='Sent to customer')
				template_id = self.env.ref('sale.mail_template_sale_confirmation')
		except ValueError:
			template_id = False
		if template_id:
			template_id.with_context(my_url=base_url).send_mail(
				self.id,
				force_send=True,
				email_layout_xmlid="mail.mail_notification_layout_with_responsible_signature",
				email_values={'email_to': self.env.user.email, 'recipient_ids': []},
			)
		# for rec in self:
		# 	rec.mark_as_sent = True
		# 	rec.message_post(body='Sent to customer')


	@api.onchange('partner_id')
	def _onchange_partner_id_warning(self):
		res = super(SaleOrderInherited, self)._onchange_partner_id_warning()
		if self.user_id.id != self.env.uid:
			self.user_id = self.env.uid
		return res


	def write(self, vals_list):
		result = super(SaleOrderInherited, self).write(vals_list)
		# if 'appoinment_to_visit' in vals_list:
		if 'appoinment_to_visit' in vals_list or 'state' in vals_list:
			# no need to keep it in vals here
			vals_list.pop('previous_state', None)

			for rec in self:
				rec.previous_state = rec.state

		if vals_list.get('multi_attachments_ids'):

			ir_attachment_obj = self.env['ir.attachment']
			appointment_id = self.env['appointment.visit'].search([('my_order_id','=',self.id)])
			att = []
			for rec in appointment_id.multi_attachments_ids:
				att.append(rec.name)
			for attachment in self.multi_attachments_ids:
				if attachment:
					if attachment.name not in att:
						appointment_id.with_context(no_update=True).write({'multi_attachments_ids':[(0,0,{
							'name': attachment.name,
							'type': 'binary',
							'datas': attachment.datas,
							'res_model': 'sale.order',
							'res_id': self.id
						})]})

		return result

	def preview_design(self):
		self.ensure_one()
		base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
		base_url += "/my/kitchen/design/%s"%(self.id)
		return {
			'type': 'ir.actions.act_url',
			'target': 'self',
			'url': base_url,
		}

	def notify_salesperson(self):
		for record in self:
			if not record.attachment_ids:
				raise UserError(_("Insert Atleast One Design"))

			record.saleperson_notified = True
			record.designer_notified = False
			base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
			base_url += record.get_portal_url()
			email_from = self.env['ir.mail_server'].sudo().search([],limit=1)
			mail_values_user_check = {
				'subject': "Design Is Uploaded",
				'email_to':record.user_id.partner_id.email,
				'email_from':email_from.smtp_user,
				'body_html': '''<div> Dear, %s <br/>
								%s Has Uploded The Design. <br/>
								Reference %s
								</div>'''%(record.user_id.partner_id.name,record.designer_id.partner_id.name,base_url)

				}
			create_and_send_email = self.env['mail.mail'].sudo().create(mail_values_user_check).sudo().send()
			record.sudo().activity_schedule(
				'crm_design.mail_activity_design_send',
				user_id=record.user_id.id)
			record.activity_feedback(['crm_design.mail_activity_design_upload'], user_id=record.designer_id.id)

	def notify_designer(self):
		for record in self:
			if not record.designer_id:
				raise UserError(_("Select Designer First"))
			record.designer_notified = True
			record.saleperson_notified = False
			record.sudo().activity_schedule(
				'crm_design.mail_activity_design_upload',
				user_id=record.designer_id.id)
			if record.opportunity_id:
				record.opportunity_id.message_subscribe(partner_ids=[record.designer_id.partner_id.id])

	# @api.onchange('order_line','payment_term_id','product_requirement')
	# @api.onchange('product_requirement')
	# def _onchange_term_base_amount(self):
	# 	for order in self:
	# 		amount_untaxed = amount_tax = 0.0
	# 		term_amount = remain_amount = 0.0
	# 		# for line in order.order_line:
	# 		# 	amount_untaxed += line.price_subtotal
	# 		# 	amount_tax += line.price_tax
	# 		# amount = (amount_untaxed + amount_tax) - order.visit_charge
	# 		amount = order.amount_total - order.visit_charge
	# 		term_amount = (amount * 30) / 100
	# 		remain_amount = amount - term_amount



	# 		# for line in order.payment_term_id.line_ids:
	# 		# 	if line.value == 'percent':
	# 		# 		amount = (amount_untaxed + amount_tax) - order.visit_charge
	# 		# 		term_amount = (order.amount_total * line.value_amount) / 100
	# 		# 		remain_amount = amount - term_amount
	# 		order.update({
	# 			'term_based_amount': term_amount,
	# 			'remain_amount': remain_amount
	# 		})
	# 		if order.product_requirement == 'built_in':
	# 			# order.note = """
	# 			# 	<span>1. ชำระมัดจำ 30 % เมื่อสั่งซื้อ <strong>"""+ str(order.term_based_amount) +""" </strong> </span><br/>
	# 			# 	<span>2. ชำระส่วนที่เหลือ 70% ก่อนผลิต ล่วงหน้า 3 วัน <strong> """+ str(order.remain_amount) +""" </strong> </span><br/>
	# 			# 	<span>3. ราคานี้ไม่รวมเครื่องใช้ไฟฟ้า ,อุปกรณ์แสงสว่างและ อุปกรณ์เสริมอื่นๆ นอกจากใบเสนอราคานี้</span><br/>
	# 			# 	<span>4. ราคานี้รวมค่าติดตั้ง แต่ไม่รวมถึงการติดตั้งเครื่องใช้ไฟฟ้า งานระบบน้ำ อุปกรณ์เสริมและอื่นๆ นอกจากใบเสนอราคานี้</span><br/>
	# 			# 	<span>5. ในกรณีลูกค้าให้ทางบริษัทสยามอาร์ตฯติดตั้งเครื่องใช้ไฟฟ้า งานระบบน้ำ อุปกรณ์เสริมและอื่นๆ จะมีค่าใช้จ่ายเพิ่มเติมในการติดตั้ง</span><br/>
	# 			# 	<span>6. ในกรณีลูกค้าให้ทางบริษัทสสยามอาร์ตฯ ต่อสายไฟ  เดินท่อ ติดปลั๊กไฟกล่อง PANASONIC สายไฟเบอร์ 2.5 ระยะไม่เกิน 6 เมตร จุดละ 1,500 บ. (กรีดผนัง ฉาบปูนและทาสี)</span><br/>
	# 			# 	<span>7. ในกรณีลูกค้าให้ทางบริษัทสสยามอาร์ตฯ ต่อสายไฟ  เดินท่อ ติดปลั๊กไฟกล่อง PANASONIC สายไฟเบอร์ 4 ระยะไม่เกิน 6 เมตร จุดละ 2,000 บ. (กรีดผนัง ฉาบปูนและทาสี)</span><br/>
	# 			# 	<span>8. ในกรณีลูกค้าซื้ออุปกรณ์ให้ ทางเราติดตั้ง มีค่าใช้ จ่าย คือ อุปกรณ์ ตู้ ล่าง-บน 800/ชุด , ตู้สูง 1600/ชุด  และไม่มีรับประกันอุปกรณ์</span><br/>
	# 			# 	<span>9. ในกรณีลูกค้าแต่งสีพ่นที่ไม่ใช่สีมาตรฐาน จะมีค่าใช้จ่ายในการแต่งสีละ 5,000บ.</span><br/>
	# 			# """

	# 			# <span>1. ชำระมัดจำ 30% เมื่อสั่งซื้อ <strong>"""+ str('%.2f'%(order.term_based_amount)) +""" </strong> บาท </span><br/>
	# 			# <span>2. ชำระส่วนที่เหลือ 70% ก่อนติดตั้งล่วงหน้า 5 วัน <strong> """+ str('%.2f'%(order.remain_amount)) +""" </strong> บาท  </span><br/>

	# 			order.note = """
	# 			<span>1. ชำระมัดจำ 30% เมื่อสั่งซื้อ <strong>"""+ 'xxxx' +""" </strong> บาท </span><br/>
	# 			<span>2. ชำระส่วนที่เหลือ 70% ก่อนติดตั้งล่วงหน้า 5 วัน <strong> """+ 'xxxx' +""" </strong> บาท  </span><br/>
	# 			<span>3. ราคานี้ไม่รวมเครื่องใช้ไฟฟ้า ,อุปกรณ์แสงสว่างและ อุปกรณ์เสริมอื่นๆ นอกจากใบเสนอราคานี้ </span><br/>
	# 			<span>4. ราคานี้รวมค่าติดตั้ง แต่ไม่รวมถึงการติดตั้งเครื่องใช้ไฟฟ้า งานระบบน้ำ อุปกรณ์เสริมและอื่นๆ นอกจากใบเสนอราคานี้ </span><br/>
	# 			<span>5. ในกรณีลูกค้าให้ทางบริษัทสยามอาร์ตฯติดตั้งเครื่องใช้ไฟฟ้า งานระบบน้ำ อุปกรณ์เสริมและอื่นๆ จะมีค่าใช้จ่ายเพิ่มเติมในการติดตั้ง </span><br/>
	# 			<span>6. ในกรณีลูกค้าให้ทางบริษัทสยามอาร์ตฯ ต่อสายไฟ เดินท่อ ติดปลั๊กไฟกล่อง PANASONIC สายไฟเบอร์ 2.5 ระยะไม่เกิน 6 เมตร จุดละ 2,000บาท (กรีดผนัง ฉาบปูนและทาสี) </span><br/>
	# 			<span>7. ในกรณีลูกค้าให้ทางบริษัทสยามอาร์ตฯ ต่อสายไฟ เดินท่อ ติดปลั๊กไฟกล่อง PANASONIC สายไฟเบอร์ 4 ระยะไม่เกิน 6 เมตร จุดละ 2,500บาท (กรีดผนัง ฉาบปูนและทาสี) </span><br/>
	# 			<span>8. ในกรณีลูกค้าซื้ออุปกรณ์ให้ทางบริษัทสยามอาร์ตฯ ติดตั้ง มีค่าใช้จ่าย คือ อุปกรณ์ ตู้ล่าง-บน 1,000บาท/ชุด , ตู้สูง 2,000 บาท/ชุด และไม่มีรับประกันอุปกรณ์ </span><br/>
	# 			<span>9. ในกรณีลูกค้าซื้ออุปกรณ์มือจับให้ทางบริษัทสยามอาร์ตฯ ติดตั้ง มีค่าใช้จ่ายชิ้นละ 50 บาท </span><br/>
	# 			<span>10. ในกรณีลูกค้าแต่งสีพ่นที่ไม่ใช่สีมาตรฐาน จะมีค่าใช้จ่ายในการแต่งสีละ 5,000 บาท </span><br/>
	# 			"""

	def _has_to_be_signed(self, include_draft=False):
		# return (self.state == 'final_approved') and not self.is_expired and self.require_signature and not self.signature
		return (self.state == 'final_approved')

	def _has_to_be_paid(self, include_draft=False):
		transaction = self.get_portal_last_transaction()
		# return self.state == 'final_approved' and not self.is_expired and self.require_payment and transaction.state != 'done' and self.amount_total
		return False

	def _prepare_invoice(self):
		result = super(SaleOrderInherited,self)._prepare_invoice()
		result.update({'product_requirement':self.product_requirement})
		return result

	@api.model
	def _compute_current_user_id(self):
		for record in self:
			if record.create_uid.id == self.env.user.id:
				record.current_login_id = True
			else:
				record.current_login_id = False

	@api.depends('attachment_ids')
	def _compute_design_count(self):
		for record in self:
			record.design_count = self.env['ir.attachment'].search_count([('sale_order_attach_ref','=',self.id)])

	@api.model
	def _compute_is_designer(self):
		design_approval_group_id = self.env.ref('crm_design.group_manager_design').id
		design_manager_ids = self.env['res.users'].search([('groups_id','=',design_approval_group_id)])
		for record in self:
			if self.env.uid in design_manager_ids.ids:
				record.is_designer_login = True
			else:
				record.is_designer_login = False

	@api.model
	def _compute_is_visitor(self):
		quotation_approval_group_id = self.env.ref('crm_design.group_manager_quotation').id
		quotation_manager_ids = self.env['res.users'].search([('groups_id','=',quotation_approval_group_id)])
		for record in self:
			if self.env.uid in quotation_manager_ids.ids:
				record.is_manager_login = True
			else:
				record.is_manager_login = False

	def request_for_final_approval(self):
		employee_rec = self.env['hr.employee'].sudo().search([('user_id', '=', self.env.uid)])
		emp_department_manager = employee_rec.department_id.manager_id
		if not employee_rec:
			raise UserError('Please Set Employee For The User')
		if not employee_rec.department_id:
			raise UserError('Please Set Department For Employee')
		if not employee_rec.department_id.manager_id:
			raise UserError('Please Set Manager For The Department')
		# quotation_approval_group_id = self.env.ref('crm_design.group_manager_quotation').id
		# quotation_manager_ids = self.env['res.users'].search([('groups_id','=',quotation_approval_group_id)])

		for record in self:
			record.state = 'final_approve_pending'
			# for manager in quotation_manager_ids:
			for manager in emp_department_manager:
				approval_id = self.env.ref('crm_design.mail_activity_data_approval')
				approval_id.sudo().name = "Approval"
				record.activity_schedule(
							'crm_design.mail_activity_data_approval',
							user_id=manager.user_id.id)
				base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
				base_url += record.get_portal_url()
				email_from = self.env['ir.mail_server'].sudo().search([],limit=1)
				mail_values_user_check = {
					'subject': "Request For Quotation Approval",
					'email_to':manager.user_id.partner_id.email,
					'email_from':email_from.smtp_user,
					'body_html': '''<div> Dear, %s <br/>
									You have one request for Quotation Approval <br/>
									Reference %s
									</div>'''%(manager.user_id.partner_id.name,base_url)

					}

	def request_for_design_approval(self):

		if not self.attachment_ids:
			raise UserError(_('Insert Atleast One Design To Send For Design Approval'))

		design_approval_group_id = self.env.ref('crm_design.group_manager_design').id
		design_manager_ids = self.env['res.users'].search([('groups_id','=',design_approval_group_id)])

		quotation_approval_group_id = self.env.ref('crm_design.group_manager_quotation').id
		quotation_manager_ids = self.env['res.users'].search([('groups_id','=',quotation_approval_group_id)])

		for record in self:
			record.state = 'approve_pending'
			for manager in design_manager_ids:
				approval_id = self.env.ref('crm_design.mail_activity_data_approval')
				approval_id.sudo().name = "Approval"
				record.activity_schedule(
						'crm_design.mail_activity_data_approval',
						user_id=manager.id)

	def action_approve(self):
		quotation_approval_group_id = self.env.ref('crm_design.group_manager_quotation').id
		quotation_manager_ids = self.env['res.users'].search([('groups_id','=',quotation_approval_group_id)])

		return {
			'name': "Approve Quotation",
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
			'name': "Reject Quotation",
			'type': 'ir.actions.act_window',
			'view_type': 'form',
			'view_mode': 'form',
			'res_model': 'reject.quotation.wizard',
			'context': {'current_id': self.id},
			'view_id': self.env.ref('crm_design.reject_quotation_view_form').id,
			'target': 'new'
		}


	def create_final_invoice(self):
		tax_id = self.env.ref('crm_design.design_tax_ids')
		design_product_id = self.env['product.product'].search([('is_design_product','=',True)])
		# self.write({'order_line':[(0, 0, {
		# 		'product_id': design_product_id.id,
		# 		'product_uom_qty': 1,
		# 		'tax_id':[(6,0,tax_id.ids)]
		# 	})]})
		self.action_confirm()
		invoice_id = self._create_invoices()

		if self.visit_charge > 0:
			invoice_id.write({
				'invoice_line_ids':[(0, 0, {
							'display_type': 'line_note',
							'name': "Previous Visit Charge \t\t\t\t" + str(-self.visit_charge),
							# 'price_unit': -self.visit_charge,
							}
						)]
				})
		invoice_id.is_final_invoice = True
		invoice_id.lead_id = self.opportunity_id.id
		invoice_id.order_id = self.id
		invoice_id.product_requirement = self.product_requirement
		invoice_id.is_thai = self.is_thai

		self.state = 'sale'
		self.is_final_invoice_created = True

		view_id = self.env.ref('account.view_move_form').id
		context = self._context.copy()
		return {
			'view_type':'form',
			'view_mode':'form',
			'views' : [(view_id,'form')],
			'res_model':'account.move',
			'view_id':view_id,
			'type':'ir.actions.act_window',
			'res_id':invoice_id.id,
			'context':context,
		}

	# @http.route(['/my/kitchen/design/<int:sale_order_id>'], type='json', auth="public", website=True)
	def send_design(self):
		# subject = 'Sale Order Design'
		# recipients = self.partner_id.email

		for record in self:
			if not record.attachment_ids:
				raise UserError(_("Insert Atleast One Design"))
			if not record.partner_id.email:
				raise UserError(_("Enter Email"))
			if not any(share_design for share_design in record.attachment_ids.mapped('share_design')):
				raise UserError(_("Make Atleast one design shareable"))

			# record.access_token = str(uuid.uuid4())
			base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')

			base_url += '/my/kitchen/design/%s?access_token=%s' % (self.id,record.access_token)
			email_from = self.env['ir.mail_server'].sudo().search([],limit=1)
			mail_values_user_check = {
				'subject': "Design Is Uploaded",
				'email_to':record.partner_id.email,
				'email_from':email_from.smtp_user,
				'body_html': '''<div> Dear, %s <br/>
								%s Has Uploded The Design. <br/><br/><br/>
								Reference :
								<a href="%s">%s %s</a>
								</div>'''%(record.partner_id.name,record.designer_id.partner_id.name,base_url,base_url,record.access_token)
								}
			create_and_send_email = self.env['mail.mail'].sudo().create(mail_values_user_check).sudo().send()
			self.state = "sent"
			record.activity_feedback(['crm_design.mail_activity_design_send'], user_id=record.user_id.id)
			subtype_id = self.env.ref('mail.mt_comment').id
			self.message_post(body= "<span>Design Is Uploaded</span><br/><br/>" + mail_values_user_check.get('body_html'),
							  message_type='comment',
							  subtype_xmlid='mail.mt_comment',
							  author_id=record.user_id.id)

		# base_url = request.env['ir.config_parameter'].get_param('web.base.url')
		# base_url += '/my/kitchen/design/%s' % self.id
		# message_body = base_url

		# template_obj = self.env['mail.mail']
		# template_data = {
		# 'subject': subject,
		# 'body_html': message_body,
		# 'email_to': recipients
		# }
		# template_id = template_obj.create(template_data)
		# template_obj.send(template_id)
		# template_id.send()

	@api.onchange('product_requirement')
	def _onchange_product_req_set_payment_term(self):
		for record in self:
			record.payment_term_id = self.env.ref('crm_design.account_payment_term_30_percent').id

	# @api.onchange('product_requirement','payment_term_id')
	@api.onchange('product_requirement')
	def _onchange_product_req_set_terms(self):
		for rec in self:
			if rec.product_requirement == 'built_in':
				# rec.note = """
				# 	<span>1. ชำระมัดจำ 30 % เมื่อสั่งซื้อ <strong>"""+ str(rec.term_based_amount) +""" </strong> </span><br/>
				# 	<span>2. ชำระส่วนที่เหลือ 70% ก่อนผลิต ล่วงหน้า 3 วัน <strong> """+ str(rec.remain_amount) +""" </strong> </span><br/>
				# 	<span>3. ราคานี้ไม่รวมเครื่องใช้ไฟฟ้า ,อุปกรณ์แสงสว่างและ อุปกรณ์เสริมอื่นๆ นอกจากใบเสนอราคานี้</span><br/>
				# 	<span>4. ราคานี้รวมค่าติดตั้ง แต่ไม่รวมถึงการติดตั้งเครื่องใช้ไฟฟ้า งานระบบน้ำ อุปกรณ์เสริมและอื่นๆ นอกจากใบเสนอราคานี้</span><br/>
				# 	<span>5. ในกรณีลูกค้าให้ทางบริษัทสยามอาร์ตฯติดตั้งเครื่องใช้ไฟฟ้า งานระบบน้ำ อุปกรณ์เสริมและอื่นๆ จะมีค่าใช้จ่ายเพิ่มเติมในการติดตั้ง</span><br/>
				# 	<span>6. ในกรณีลูกค้าให้ทางบริษัทสสยามอาร์ตฯ ต่อสายไฟ  เดินท่อ ติดปลั๊กไฟกล่อง PANASONIC สายไฟเบอร์ 2.5 ระยะไม่เกิน 6 เมตร จุดละ 1,500 บ. (กรีดผนัง ฉาบปูนและทาสี)</span><br/>
				# 	<span>7. ในกรณีลูกค้าให้ทางบริษัทสสยามอาร์ตฯ ต่อสายไฟ  เดินท่อ ติดปลั๊กไฟกล่อง PANASONIC สายไฟเบอร์ 4 ระยะไม่เกิน 6 เมตร จุดละ 2,000 บ. (กรีดผนัง ฉาบปูนและทาสี)</span><br/>
				# 	<span>8. ในกรณีลูกค้าซื้ออุปกรณ์ให้ ทางเราติดตั้ง มีค่าใช้ จ่าย คือ อุปกรณ์ ตู้ ล่าง-บน 800/ชุด , ตู้สูง 1600/ชุด  และไม่มีรับประกันอุปกรณ์</span><br/>
				# 	<span>9. ในกรณีลูกค้าแต่งสีพ่นที่ไม่ใช่สีมาตรฐาน จะมีค่าใช้จ่ายในการแต่งสีละ 5,000บ.</span><br/>
				# """

				# <span>1. ชำระมัดจำ 30% เมื่อสั่งซื้อ <strong>"""+ str('%.2f'%(rec.term_based_amount)) +""" </strong> บาท </span><br/>
				# <span>2. ชำระส่วนที่เหลือ 70% ก่อนติดตั้งล่วงหน้า 5 วัน <strong> """+ str('%.2f'%(rec.remain_amount)) +""" </strong> บาท  </span><br/>

				rec.note = """
				<span>1. ชำระมัดจำ 30% เมื่อสั่งซื้อ <strong>"""+ 'xxx' +""" </strong> บาท </span><br/>
				<span>2. ชำระส่วนที่เหลือ 70% ก่อนติดตั้งล่วงหน้า 5 วัน <strong> """+ 'xxx' +""" </strong> บาท  </span><br/>
				<span>3. ราคานี้ไม่รวมเครื่องใช้ไฟฟ้า ,อุปกรณ์แสงสว่างและ อุปกรณ์เสริมอื่นๆ นอกจากใบเสนอราคานี้ </span><br/>
				<span>4. ราคานี้รวมค่าติดตั้ง แต่ไม่รวมถึงการติดตั้งเครื่องใช้ไฟฟ้า งานระบบน้ำ อุปกรณ์เสริมและอื่นๆ นอกจากใบเสนอราคานี้ </span><br/>
				<span>5. ในกรณีลูกค้าให้ทางบริษัทสยามอาร์ตฯติดตั้งเครื่องใช้ไฟฟ้า งานระบบน้ำ อุปกรณ์เสริมและอื่นๆ จะมีค่าใช้จ่ายเพิ่มเติมในการติดตั้ง </span><br/>
				<span>6. ในกรณีลูกค้าให้ทางบริษัทสยามอาร์ตฯ ต่อสายไฟ เดินท่อ ติดปลั๊กไฟกล่อง PANASONIC สายไฟเบอร์ 2.5 ระยะไม่เกิน 6 เมตร จุดละ 2,000บาท (กรีดผนัง ฉาบปูนและทาสี) </span><br/>
				<span>7. ในกรณีลูกค้าให้ทางบริษัทสยามอาร์ตฯ ต่อสายไฟ เดินท่อ ติดปลั๊กไฟกล่อง PANASONIC สายไฟเบอร์ 4 ระยะไม่เกิน 6 เมตร จุดละ 2,500บาท (กรีดผนัง ฉาบปูนและทาสี) </span><br/>
				<span>8. ในกรณีลูกค้าซื้ออุปกรณ์ให้ทางบริษัทสยามอาร์ตฯ ติดตั้ง มีค่าใช้จ่าย คือ อุปกรณ์ ตู้ล่าง-บน 1,000บาท/ชุด , ตู้สูง 2,000 บาท/ชุด และไม่มีรับประกันอุปกรณ์ </span><br/>
				<span>9. ในกรณีลูกค้าซื้ออุปกรณ์มือจับให้ทางบริษัทสยามอาร์ตฯ ติดตั้ง มีค่าใช้จ่ายชิ้นละ 50 บาท </span><br/>
				<span>10. ในกรณีลูกค้าแต่งสีพ่นที่ไม่ใช่สีมาตรฐาน จะมีค่าใช้จ่ายในการแต่งสีละ 5,000 บาท </span><br/>
				"""
			if rec.product_requirement == 'loose':
				rec.note = """
					<span>1. ราคาที่เสนอนี้ยังไม่รวมภาษีมูลค่าเพิ่ม 7%</span><br/>
					<span>2. ราคาที่เสนอนี้รวม PACKING ลังไม้แล้ว</span><br/>
					<span>3. ราคาที่เสนอนี้ยังไม่รวมค่าขนส่ง</span><br/>
					<span>4. ราคาที่เสนอนี้ยังไม่รวมค่าติดตั้ง</span><br/>
					<span>5. ราคายังไม่รวมเจาะหลุม ( เจาะหลุมวางบนท็อปเคาเตอร์ = 200 บาท/1หลุม , เจาะหลุมวางใต้ท็อปเคาเตอร์ = 400 บาท/1หลุม)</span><br/>
				"""
			if rec.product_requirement == 'doors':
				rec.note = """
					<span>1. ชำระเต็ม 100 % เมื่อสั่งผลิต </span><br/>
					<span>2. ราคานี้ไม่รวมค่าขนส่ง ลูกค้าเป็นผู้ส่งสินค้าและรับสินค้าเองที่โรงงาน  กรณีลูกค้าต้องการให้ส่งสินค้า ทางบริษัทฯจะใช้บริการขนส่งเอกชนเป็นผู้ส่งมอบสินค้า</span><br/>
					<span>3. กรณีลูกค้าต้องการตรวจคุณภาพสินค้า สามารถแจ้ง และตรวจสินค้าได้ที่โรงงานก่อนทำการ Packing </span><br/>
					<span>4. ราคานี้รวมภาษีมูลค่าเพิ่ม 7% เรียบร้อยแล้ว</span><br/>
				"""
			if rec.product_requirement == 'other':
				rec.note = ""

	@api.onchange('appoinment_to_visit')
	def _onchange_set_state_site_visit(self):
		for rec in self:
			if rec.appoinment_to_visit:
				if rec.state != 'draft':
					rec.state = 'site_visit'
			if rec.appoinment_to_visit == False:
				rec.state = rec.previous_state

	def action_create_appointment(self):
		ctx = dict(self.env.context or {})
		ctx.update({
			'default_customer_id': self.partner_id.id,
			'my_order_id': self.id,
		})

		return {
				'name': _('Create Visit Appointment'),
				'view_mode': 'form',
				'res_model': 'appointment.visit',
				'view_id': self.env.ref('crm_design.visit_appointment_view_form').id,
				'type': 'ir.actions.act_window',
				'target': 'new',
				'context': ctx
		}

	def action_view_appointments(self):
		return {
				'name': _('Appointments'),
				'view_mode': 'calendar',
				'res_model': 'appointment.visit',
				'view_id': self.env.ref('crm_design.visit_appointment_view_calendar').id,
				'type': 'ir.actions.act_window',
				'target': 'new'
		 }


	def action_quotation_send(self):
		result = super(SaleOrderInherited,self).action_quotation_send()
		base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
		base_url += self.get_portal_url()
		result.get('context').update({'my_url':base_url})
		return result



	def _prepare_down_payment_section_line(self, **optional_values):
		res = super(SaleOrderInherited, self)._prepare_down_payment_section_line(**optional_values)

		""" Prepare the values to create a new down payment section.

		:param dict optional_values: any parameter that should be added to the returned down payment section
		:return: `account.move.line` creation values
		:rtype: dict
		"""
		res.update({
			'name': _("Deposit Payments"),
			})
		return res


class SaleOrderLineInherited(models.Model):
	_inherit = 'sale.order.line'

	model_id = fields.Many2one('product.product',string="Model")
	thickness = fields.Float(string="Deep/Thick (mm)")
	width = fields.Float(string="Width (mm)")
	height = fields.Float(string="Height (mm)")
	standard_type = fields.Selection(selection=[('standard','Standard'),('non_standard','Non Standard')])
	is_thai = fields.Boolean(string='Is Thai',related='order_id.is_thai')
	formula = fields.Text(string="Formula")

	@api.onchange('formula')
	def _onchange_formula_set_unitprice(self):
		for rec in self:
			if rec.formula:
				if rec.formula or isinstance(rec.formula, int) or rec.formula in ['=','+','-','*','/','(',')','^','//','**']:
					try:
						# rec.price_unit = eval(rec.formula)
						rec.product_uom_qty = eval(rec.formula)
					except:
						raise UserError(_(' You cannot Enter Values otherthan Numeric And Arithmatic Operator'))

class SaleDesignAttachment(models.Model):
	_inherit = 'ir.attachment'
	# _sql_constraints = [
	# 	('name_attachment_uniq', 'unique(name,sale_order_attach_ref)', 'name must be unique')
	# ]

	approve_state = fields.Selection(string="State",selection=[('draft','Draft'),
		('approve','Approved'),
		('pre_approved','Pre-Approved'),
		('rejected','Rejected')],default='draft')
	share_design = fields.Boolean(string="Share")
	is_approved = fields.Boolean(string="Approved")
	is_rejected = fields.Boolean(string="Rejected")
	comment = fields.Text(string="Customer Review")
	sale_order_attach_ref = fields.Many2one('sale.order')
	is_final_design = fields.Boolean(string="Final Design")
	customer_signature = fields.Image('Signature', help='Signature received through the portal.', copy=False, attachment=True, max_width=1024, max_height=1024)
	my_download_url = fields.Char("Download Url",compute="_compute_download_url")
	attch_sale_ref_id = fields.Many2one("sale.order")

	@api.depends('name')
	def _compute_download_url(self):
		for rec in self:
			# custom_url = '/web/content/%s/%s' % (rec.id, rec.name)
			custom_url = "web/content/?model=ir.attachment&id=" + str(rec.id) + "&filename_field=name&field=datas&download=true&name=" + rec.name,
			rec.my_download_url = custom_url
			rec.access_token = str(uuid.uuid4())

	@api.model_create_multi
	def create(self, vals_list):
		result = super(SaleDesignAttachment, self).create(vals_list)
		for record in result:
			if record.sale_order_attach_ref.attachment_ids:
				for rec in record.sale_order_attach_ref.attachment_ids:
					if rec.name == record.name and not rec.id == record.id:
						raise ValidationError(_("Not allowed to insert same design again !!! \n %s",rec.name))

			# This is for make Document Public to Access anywhere with proper Link
			if record.sale_order_attach_ref:
				record.public = True

			# if record.res_model == 'appointment.visit':
			# 	appointment_id = self.env['appointment.visit'].sudo().search([('id','=',record.res_id)])
				# attachment_id = self.sudo().create({
				# 	'name': record.name,
				# 	'type': 'binary',
				# 	'datas': record.datas,
				# 	'res_model': 'sale.order',
				# 	'res_id': appointment_id.my_order_id
				# })
				# order_id = self.env['sale.order'].browse(appointment_id.my_order_id)
				# order_id.write({'multi_attachments':[(0,0,{
				# 	'name': record.name,
				# 	'type': 'binary',
				# 	'datas': record.datas,
				# 	'res_model': 'sale.order',
				# 	'res_id': appointment_id.my_order_id
				# 	})]})

		return result

	@api.model
	def check(self, mode, values=None):
		""" Restricts the access to an ir.attachment, according to referred mode """
		if self.env.is_superuser():
			return True
		# Always require an internal user (aka, employee) to access to a attachment
		# if not (self.env.is_admin() or self.env.user.has_group('base.group_user')):
		# 	raise AccessError(_("Sorry, you are not allowed to access this document."))
		# collect the records to check (by model)
		model_ids = defaultdict(set)            # {model_name: set(ids)}
		if self:
			# DLE P173: `test_01_portal_attachment`
			self.env['ir.attachment'].flush_model(['res_model', 'res_id', 'create_uid', 'public', 'res_field'])
			self._cr.execute('SELECT res_model, res_id, create_uid, public, res_field FROM ir_attachment WHERE id IN %s', [tuple(self.ids)])
			for res_model, res_id, create_uid, public, res_field in self._cr.fetchall():
				if public and mode == 'read':
					continue
				if not (res_model and res_id):
					continue
				model_ids[res_model].add(res_id)
		if values and values.get('res_model') and values.get('res_id'):
			model_ids[values['res_model']].add(values['res_id'])

		# check access rights on the records
		for res_model, res_ids in model_ids.items():
			# ignore attachments that are not attached to a resource anymore
			# when checking access rights (resource was deleted but attachment
			# was not)
			if res_model not in self.env:
				continue
			if res_model == 'res.users' and len(res_ids) == 1 and self.env.uid == list(res_ids)[0]:
				# by default a user cannot write on itself, despite the list of writeable fields
				# e.g. in the case of a user inserting an image into his image signature
				# we need to bypass this check which would needlessly throw us away
				continue
			records = self.env[res_model].browse(res_ids).exists()
			# For related models, check if we can write to the model, as unlinking
			# and creating attachments can be seen as an update to the model
			access_mode = 'write' if mode in ('create', 'unlink') else mode
			records.check_access_rights(access_mode)
			records.check_access_rule(access_mode)


class DesignAttachment(models.Model):
	_name = 'design.attachment'


class SaleOrderManager(models.Model):
	_name = 'saleorder.manager'

	manager_info_id = fields.Many2one('sale.order')
	manager_signature = fields.Binary('Signature', copy=False, attachment=True, max_width=1024, max_height=1024)
	manager_name = fields.Char('Signed By', copy=False)
	manager_signed_on = fields.Datetime('Signed On', help='Date of the signature.', copy=False)
	state = fields.Selection([('approved','Approve'),('rejected','Reject')])
	is_approved = fields.Boolean(string="Is Approved")

class SaleAdvancePaymentInvInherit(models.TransientModel):
	_inherit = 'sale.advance.payment.inv'
	_description = "Sales Advance Payment Invoice"

	def _get_down_payment_description(self, order):
		res = super(SaleAdvancePaymentInvInherit, self)._get_down_payment_description(order)
		context = {'lang': order.partner_id.lang}
		if self.advance_payment_method == 'percentage':
			name = _("Payment of %s%%", self.amount)
		else:
			name = _('Payment')
		del context

		# sale_order = self.env['sale.order'].browse(self.env.context.get('active_id'))
		# tax = self.env['account.tax'].search([('amount', '=', '0')], limit=1)
		# if not sale_order.amount_tax:
		# 	tax_ids = tax




		return name

	def _prepare_so_line_values(self, order):
		res = super(SaleAdvancePaymentInvInherit, self)._prepare_so_line_values(order)
		sale_order = self.env['sale.order'].browse(self.env.context.get('active_id'))
		tax = self.env['account.tax'].search([('amount', '=', 0)], limit=1)
		res.update({
			'name' : _('Payment'),
			}) 
		if not sale_order.amount_tax:
			res.update({
			'name' : _('Payment'),
			'tax_id' : tax.ids,
			}) 
		return res

	def create_invoices(self):
		invoice_id = self._create_invoices(self.sale_order_ids)

		# if self.sale_order_ids.visit_charge > 0:
		# 	invoice_id.write({
		# 		'invoice_line_ids':[(0, 0, {
		# 					'display_type': 'line_note',
		# 					'name': "Previous Visit Charge \t\t\t\t" + str(-self.visit_charge),
		# 					# 'price_unit': -self.visit_charge,
		# 					}
		# 				)]
		# 		})# invoice_id.product_requirement = self.sale_order_ids.product_requirement
		# invoice_id.is_thai = self.sale_order_ids.is_thai
		
		invoice_id.is_final_invoice = True
		# invoice_id.lead_id = self.sale_order_ids.opportunity_id.id
		# invoice_id.order_id = self.sale_order_ids.id
		# invoice_id.product_requirement = self.sale_order_ids.product_requirement
		# invoice_id.is_thai = self.sale_order_ids.is_thai

		for sale in self.sale_order_ids:
			invoice_id.lead_id = sale.opportunity_id.id
			invoice_id.order_id = sale
			invoice_id.product_requirement = sale.product_requirement
			invoice_id.is_thai = sale.is_thai

		self.sale_order_ids.state = 'sale'
		self.sale_order_ids.is_final_invoice_created = True

		if self.env.context.get('open_invoices'):
			return self.sale_order_ids.action_view_invoice()

		return {'type': 'ir.actions.act_window_close'}



	def _prepare_down_payment_section_values(self, order):
		res = super(SaleAdvancePaymentInvInherit, self)._prepare_down_payment_section_values(order)

		res.update({
			'name': _('Deposit Payments'),
			})

		return res
