from odoo import api, fields, models


class SaleLineChangeOrderLine(models.TransientModel):
    _inherit = 'sale.line.change.order.line'

    def _apply(self):
        super()._apply()
        if self:
            orders = self.mapped('sale_line_id.order_id')
            pickings = orders.picking_ids
            cancelled_moves = pickings.mapped('move_lines').filtered(lambda m: m.state == 'cancel')
            cancelled_moves.write({'product_uom_qty': 0.0})
