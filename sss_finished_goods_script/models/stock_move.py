from odoo import fields, models, api


class StockMove(models.Model):
	_inherit = "stock.move"

	componants = fields.Float(string="Components")

	@api.onchange('weight')
	def onchange_weight_in_move(self):
		for rec in self:
			if rec.product_id:
				rec.product_id.weight = rec.weight