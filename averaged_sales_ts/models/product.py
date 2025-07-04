from odoo import models,fields,api
from dateutil.relativedelta import relativedelta
from datetime import datetime


class Product(models.Model):
    _inherit = 'product.product'

    #averaged_sales_qty = fields.Float(string="Averaged Sales QTY", help='Averaged Sales QTY of last 3 months')
    averaged_sales_qty = fields.Float(string="Averaged Sales QTY", help='Averaged Sales QTY of last 3 months')

    @api.depends('stock_move_ids.move_line_ids.qty_done')
    def _compute_averaged_sales_qty(self):
        for product in self:
            last_3_month = datetime.now() - relativedelta(months=3)
            move_lines = self.env['stock.move.line'].search([('product_id', '=', product.id), ('state', '=', 'done'), ('date', '>=', last_3_month), ('move_id.picking_code','=','outgoing'), ('move_id.company_id','=',self.env.user.company_id.id)])
            if move_lines:
                product.averaged_sales_qty = sum(move_lines.mapped('qty_done')) / 3
            else:
                product.averaged_sales_qty = 0.0
