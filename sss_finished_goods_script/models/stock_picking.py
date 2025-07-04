from odoo import fields, models, api

class StockPicking(models.Model):
	_inherit = 'stock.picking'

	attachment_ids = fields.Many2many('ir.attachment', 'ir_attachment_picking_ref', 'picking_id', 'attachment_id', string="Attach a file")
	total_packing_qty = fields.Float("Packing Qty", compute="_compute_all_quantities")
	total_packing_weight = fields.Float("Packing Weight (kg)", compute="_compute_all_quantities")
	total_componants_qty = fields.Float("Components Qty", compute="_compute_all_quantities")
	sale_internal_id = fields.Many2one('sale.order',string="Sale Internal")

	@api.depends('move_ids_without_package')
	def _compute_all_quantities(self):
		for rec in self:
			rec.total_packing_qty = 0.0
			rec.total_packing_weight = 0.0
			rec.total_componants_qty = 0.0
			if rec.move_ids_without_package:
				rec.total_packing_qty = len(rec.move_ids_without_package)
				rec.total_packing_weight = sum(rec.move_ids_without_package.mapped('weight'))
				rec.total_componants_qty = sum(rec.move_ids_without_package.mapped('componants'))
			# for move in rec.move_ids_without_package:
			# 	rec.total_packing_qty += move.
			# 	rec.total_packing_weight += move.
			# 	rec.total_componants_qty += move.

	@api.onchange('picking_type_id')
	def onchange_picking_type_id(self):
		for line in self:
			res = {'domain': {'partner_id': []}}
			if line.picking_type_id.code == 'internal':
				res['domain']['partner_id'] = [('employee_ids', '!=', False)]
			return res
