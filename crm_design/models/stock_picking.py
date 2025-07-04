from odoo import api, fields, models, _
from odoo.exceptions import UserError

class StockPicking(models.Model):
	_inherit = 'stock.picking'

	picking_type_code = fields.Selection(
        related='picking_type_id.code',
        readonly=True,
        default='internal')

	def button_validate(self):
		# res = super(StockPicking, self).button_validate()
		if self.picking_type_code != 'incoming':
			if self.tag_job_sale_ref and self.tag_job_sale_ref.is_custom_order:
				# if any (self.move_line_ids.filtered(lambda l: l.qty_done > l.product_id.with_context(location_id = l.location_id).qty_available)):
				moves = self.move_line_ids.filtered(lambda l: l.qty_done > l.product_id.with_context(location_id = l.location_id).qty_available)
				for move in moves:
					on_hand_from_quant = self.env['stock.quant'].search([('location_id', '=', move.location_id.id), ('product_id', '=', move.product_id.id)], limit=1)
					if on_hand_from_quant:
						if move.qty_done > on_hand_from_quant.quantity:
							if move.reserved_uom_qty < 0:
								raise UserError(_('Currently onhand %s quantity available for %s at %s')%(move.product_id.with_context(location_id = move.location_id).qty_available, move.product_id.name,move.location_id.name))
			else:
				for rec in self.move_ids_without_package:
					quant_id = self.env['stock.quant'].search([('location_id', '=', rec.location_id.id), ('product_id', '=', rec.product_id.id)], limit=1)
					if rec.quantity_done > quant_id.quantity :
						raise UserError(_('Currently onhand %s quantity available for %s at %s')%(quant_id.quantity, rec.product_id.name, rec.location_id.name))

		# return res
		return super(StockPicking, self).button_validate()

class StockMove(models.Model):
	_inherit = 'stock.move'

	def action_open_label(self):
		action = self.env['ir.actions.act_window']._for_xml_id('product.action_open_label_layout')
		for rec in self:
			action['context'] = {'default_product_ids': rec.product_id.ids}
		return action


class StockReturnPicking(models.TransientModel):
	_inherit = 'stock.return.picking'


	def _create_returns(self):
		active_id = self.env['stock.picking'].browse(self.env.context.get('active_id'))
		# location = self.env['stock.quant'].
		for rec in active_id.move_ids_without_package:
			for record in self.product_return_moves:
				on_hand_from_quant = self.env['stock.quant'].search([('location_id', '=', self.location_id.id), ('product_id', '=', record.product_id.id)], limit=1)
				if rec.product_id.id == record.product_id.id:
					if record.quantity > rec.quantity_done:
						raise UserError(_("You Can Not Return More Quantity %s That You Pucrchased %s", record.quantity , rec.quantity_done))

					# if record.quantity > on_hand_from_quant.quantity:
					# 	raise UserError(_("'Currently onhand %s quantity available for product %s at location %s'", on_hand_from_quant.quantity, record.product_id.name, self.location_id.name))
		
		res = super(StockReturnPicking, self)._create_returns()

		return res