from odoo import api, fields, models, _

class AccountPaymentInherited(models.Model):
	_inherit = 'account.payment'

	product_requirement = fields.Selection(string="Product Requirements",
		selection=[('built_in','Built - In'),('loose','Stone'),('doors','Doors'),('other','Other')])