from odoo import fields, models, api, _
from odoo.exceptions import UserError
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, format_amount, format_date, formatLang, get_lang, groupby
from odoo.tools.float_utils import float_compare, float_is_zero, float_round

class PurchaseOrderInherited(models.Model):
	_inherit = 'purchase.order.line'

	urgency = fields.Selection([('very urgent', 'Very Urgent'),('within 1 week','Within 1 Week'),('standard 2 weeks','Standard 2 Weeks')])
	standard_type = fields.Selection(selection=[('standard','Standard'),('non_standard','Non Standard')])
	line_id = fields.Char(string='Line Id')
	pr_line_id = fields.Many2one('product.request.line',string='Line Id')
	is_editable = fields.Boolean(default=False)
	name = fields.Text(
		string='Description', required=True, compute='_compute_price_unit_and_date_planned_and_name', store=True, readonly=False)
	