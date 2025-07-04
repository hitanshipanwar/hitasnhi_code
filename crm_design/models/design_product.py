from odoo import api, fields, models, tools, SUPERUSER_ID, _, Command
from odoo.exceptions import AccessError, MissingError, ValidationError,UserError
from odoo.osv import expression

class DesignProductInherit(models.Model):
	_inherit = 'product.product'

	is_design_product = fields.Boolean(string="Design Product")
	is_site_visit_product = fields.Boolean(string="Site Visit Product")
	product_type = fields.Selection(selection=[('standard','Standard'),('non_standard','Non Standard')], string="Standardize", related="product_tmpl_id.standardize_type", readonly=False)
	thai_product_name = fields.Char(string="Thai Product Name")
	thai_sale_description = fields.Text(string="Thai Sale Description")

	def name_get(self):
		res = super().name_get()
		record = False
		# if self._context.get('params'):
		# 	model = self._context.get('params').get('model')
		# 	id = self._context.get('params').get('id')
		# 	record = self.env[model].browse(id)
		pro_list = []
		for pro in self:
			name = ''
			if pro.default_code:
				name = '[%s] ' % pro.default_code
			if self._context.get('is_thai') and pro.thai_product_name:
				name += pro.thai_product_name
			else:
				name += pro.name
			pro_list.append((pro.id,name or ''))
		return pro_list

	def get_product_multiline_description_sale(self):
		""" Compute a multiline description of this product, in the context of sales
				(do not use for purchases or other display reasons that don't intend to use "description_sale").
			It will often be used as the default description of a sale order line referencing this product.
		"""

		if self._context.get('is_thai'):
			code = self.display_name.split(' ')
			if len(code) > 1:
				name = code[0] +' '+ self.thai_product_name if self.thai_product_name else ''
			else:
				name = self.display_name

			if self.thai_sale_description:
				name += '\n' + self.thai_sale_description
		else:
			name = self.display_name
			if self.description_sale:
				name += '\n' + self.description_sale

		return name

	@api.model
	def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):

		res = super(DesignProductInherit, self)._name_search(name, args=None, operator='ilike', limit=100, name_get_uid=None)
		if args:
			thai_domain = ['|', '|', ('thai_product_name', 'ilike', name), ('name', 'ilike', name), ('default_code', 'ilike', name)]
			# args += thai_domain
			thai_product_ids = list(self._search(expression.AND([args, thai_domain]), limit=limit, access_rights_uid=name_get_uid))
			# thai_product_ids = list(self._search(args, limit=limit, access_rights_uid=name_get_uid))
			res = thai_product_ids

		return res

class DesignProductTemplateInherit(models.Model):
	_inherit = 'product.template'

	standardize_type = fields.Selection(selection=[('standard','Standard'),('non_standard','Non Standard')], default='standard', string="Standardize")
