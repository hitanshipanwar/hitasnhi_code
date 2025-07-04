from odoo import api,models,fields

class StockPicking(models.Model):
	_inherit="stock.picking"
	_description="Stock Picking"

	def po_number_smart_button(self):
		for record in self:
			view = {
				'name': 'purchase.order.tree',
				'view_mode': 'tree',
				'view_id': self.env.ref('purchase.purchase_order_kpis_tree').id,
				'res_model': 'purchase.order',
				'type': 'ir.actions.act_window',
				'domain': [('id','in',self.so_id._get_purchase_orders().ids)]
			}
		return view

	so_id = fields.Many2one('sale.order', string="Sale Order", compute="_compute_description")
	po_id = fields.Many2one('purchase.order', string="Purchase Order",compute="_compute_description")
	po_number = fields.Char(string="PO Number")
	po_no = fields.Text(string='Related POs', compute='_compute_purchase_orders')
	po_no_count = fields.Integer(string='Purchase Order' ,compute='po_number_count')

	def po_number_count(self):
		for record in self:
			domain = [('id', '=', self.so_id._get_purchase_orders().ids)]
			record.po_no_count = self.env['purchase.order'].search_count(domain)


	@api.depends('origin')
	def _compute_description(self):
		
		for record in self:
			if record.origin:
				so_recs = self.env['sale.order'].search([('name', '=', record.origin)])
				record.so_id = False
				if so_recs:
					record.so_id = so_recs.id
				record.po_id = False
				po_recs = self.env['purchase.order'].search([('name', '=', record.origin)])
				if po_recs:
					record.po_id = po_recs.id
			else:
				record.so_id = False
				record.po_id = False

	@api.depends("so_id",'write_date')
	def _compute_purchase_orders(self):
		for record in self:
			order_name = ''
			purchase_orders = record.so_id._get_purchase_orders()
			for order in purchase_orders:
				order_name += order.name + ','
			
			record.po_no = order_name
