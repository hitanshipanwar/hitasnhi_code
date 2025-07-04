from odoo import fields, models, api, _


class PurchaseOrderInherited(models.Model):
	_inherit = 'purchase.order'

	is_thai = fields.Boolean(string='Enable Thai')

	@api.onchange('is_thai')
	def onchange_is_thai_name(self):
		for order_line_id in self.order_line:
			if self.is_thai:
				self = self.with_context(is_thai=True)
				name = '[%s] %s' % (order_line_id.product_id.default_code,order_line_id.product_id.thai_product_name)
				if order_line_id.product_id.thai_sale_description:
					name += '\n' + order_line_id.product_id.thai_sale_description
			else:
				self = self
				name = order_line_id.product_id.display_name
				if order_line_id.product_id.description_purchase:
					name += '\n' + order_line_id.product_id.description_purchase
			order_line_id.name = name

class PurchaseOrderLine(models.Model):
	_inherit = 'purchase.order.line'

	is_thai = fields.Boolean(string='Is Thai',related='order_id.is_thai')