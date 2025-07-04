from odoo import api, fields, models

class HREmployeeInherit(models.Model):
	_inherit = 'hr.department'
	
	currency_id = fields.Many2one("res.currency", string="Currency")
	target = fields.Monetary(string="Target Amount")
