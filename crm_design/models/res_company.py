from odoo import fields, models, api

class ResCompanyInherit(models.Model):
	_inherit = "res.company"

	thai_add = fields.Char(string='Thai Company')
	thai_street1 = fields.Char(string='Thai Street1')
	thai_street2 = fields.Char(string='Thai Street2')
	thai_city = fields.Char(string='Thai City')
	thai_state = fields.Char(string='Thai State')
	thai_country = fields.Char(string='Thai Country')