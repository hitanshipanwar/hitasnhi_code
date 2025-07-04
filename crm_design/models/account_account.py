from odoo import api, fields, models
from odoo.exceptions import AccessError, MissingError, ValidationError,UserError
from odoo.osv import expression

class AccountAccount(models.Model):
	_inherit = 'account.account'

	thai_account_name = fields.Char('Thai Account Name')

	def name_get(self):
		res = super().name_get()
		# record = False
		# if self._context.get('params'):
		# 	model = self._context.get('params').get('model')
		# 	id = self._context.get('params').get('id')
		# 	record = self.env[model].browse(id)
		account_list = []
		account_line_list = []
		for account in self:
			name = ''
			if account.code:
				name = '%s ' % account.code
			if self._context.get('is_thai'):
				if account.thai_account_name:
					name += account.thai_account_name
				else:
					name += account.name
			else:
				name += account.name
			
			account_list.append((account.id,name or ''))
		return account_list

	@api.model
	def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
		res = super(AccountAccount, self)._name_search(name, args=None, operator='ilike', limit=100, name_get_uid=None)
		if args:
			thai_domain = ['|', '|', ('thai_account_name', 'ilike', name), ('name', 'ilike', name), ('code', 'ilike', name)]
			thai_account_ids = list(self._search(expression.AND([args, thai_domain]), limit=limit, access_rights_uid=name_get_uid))
			res = thai_account_ids
		return res	

class AccountTax(models.Model):
	_inherit = 'account.tax'

	thai_tax_name = fields.Char('Thai Tax Name')

	def name_get(self):
		res = super().name_get()
		# record = False
		# if self._context.get('params'):
		# 	model = self._context.get('params').get('model')
		# 	id = self._context.get('params').get('id')
		# 	record = self.env[model].browse(id)
		tax_list = []
		for tax in self:
			name = ''
			if self._context.get('is_thai'):
				if tax.thai_tax_name:
					name += tax.thai_tax_name
				else:
					name += tax.name
			else:
				name += tax.name
			
			tax_list.append((tax.id,name or ''))
		return tax_list

	@api.model
	def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
		res = super(AccountTax, self)._name_search(name, args=None, operator='ilike', limit=100, name_get_uid=None)
		if args:
			thai_domain = ['|', ('thai_tax_name', 'ilike', name), ('name', 'ilike', name)]
			thai_tax_ids = list(self._search(expression.AND([args, thai_domain]), limit=limit, access_rights_uid=name_get_uid))
			res = thai_tax_ids
		return res	