from odoo import fields, models, api, _


class PurchaseOrderInherited(models.Model):
	_name = 'platform.platform'


	name = fields.Char(string="Platform Name")