from odoo import fields, models, api
from odoo.osv import expression
from lxml import etree

class VendersupplierInherit(models.Model):
	_inherit = "res.partner"

	code = fields.Char(string='Code')
	branch = fields.Char(string='Branch')
	discount = fields.Float(string='Discount')
	# vendor_certificate = fields.Many2many('ir.attachment', 'ir_attachment_vendor_cert_ref', 'partner_id_cert', 'attachment_id_cert', 
	# 	string="Select File")
	# phone = fields.Char(unaccent=False, required=True)

	# @api.model
	# def _get_view(self, view_id=None, view_type='form', **options):
	# 	arch, view = super(VendersupplierInherit, self)._get_view(view_id, view_type, **options)
	# 	if view.type == 'form':
	# 		is_erp_manager = self.env.user.has_group('base.group_erp_manager')
	# 		print("Group Id- ------------------- ", is_erp_manager)
	# 		# doc = etree.XML(res['arch'])
	# 		if not is_erp_manager:
	# 			if view_type == 'form':
	# 				for node in arch.xpath("//form"):
	# 					node.set('create', '0')
	# 			if view_type == 'tree':
	# 				for node in arch.xpath("//tree"):
	# 					node.set('create', '0')
	# 			if view_type == 'kanban':
	# 				for node in arch.xpath("//kanban"):
	# 					node.set('create', '0')
	# 				# res['arch'] = etree.tostring(doc)
	# 	# return res
	# 	return arch, view

	@api.model
	def _search(self, args, offset=0, limit=None, order=None, count=False, access_rights_uid=None):
		context = self._context or {}
		supplier = []
		customer = []
		if context.get("params"):
			params = context.get("params")
			if params.get("model") == "crm.lead":
				args += [('customer_rank', '>', 0)]
			# if params.get("model") == "purchase.order":
			# 	args += [('supplier_rank', '>', 0)]

		if not self.env.user.has_group('base.group_erp_manager'):
			# args += [('customer_rank', '>', 0)]
			if self.env.user.has_group('crm_design.group_allow_suppliers') and self.env.user.has_group('crm_design.group_allow_customers'):
				args = args
			elif self.env.user.has_group('crm_design.group_allow_suppliers'):
				if self._context.get('res_partner_search_mode') == 'customer':
					args +=  [('customer_rank', '>', 0)]
				else:
					# args = expression.OR([args, ('supplier_rank', '>', 0)])
					args += [('supplier_rank', '>', 0)]
			elif self.env.user.has_group('crm_design.group_allow_customers'):
				if self._context.get('res_partner_search_mode') == 'supplier':
					args +=  [('supplier_rank', '>', 0)]
					# args = expression.OR([args, ('customer_rank', '>', 0)])
				else:
					args +=  [('customer_rank', '>', 0)]
		# args = expression.OR([args, supplier, customer])

		return super(VendersupplierInherit, self)._search(args, offset, limit, order, count=count, access_rights_uid=access_rights_uid)

	@api.model
	def create(self, vals):
		res = super(VendersupplierInherit, self).create(vals)
		if self._context.get('is_crm_contact'):
			res.is_public = True
			res.is_company = False
			res.parent_id = False
		if self.env.user.has_group('crm_design.group_allow_customers') and not self.env.user.has_group('crm_design.group_allow_suppliers'):
			res.customer_rank = 1
		if not self.env.user.has_group('crm_design.group_allow_customers') and self.env.user.has_group('crm_design.group_allow_suppliers'):
			res.supplier_rank = 1
		partner_search_mode = self._context.get('res_partner_search_mode')
		if partner_search_mode == 'supplier':
			res.supplier_rank = 1
		if partner_search_mode == 'customer':
			res.customer_rank = 1
		return res