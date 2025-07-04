from odoo import models, fields


class StockMove(models.Model):
    _inherit = 'stock.move'
    _order = 'stock_aisle asc'

    stock_aisle = fields.Char(string="Aisle", store=True)
    # stock_aisle = fields.Char(string="Aisle")

    def create(self, vals):
        res = super(StockMove, self).create(vals)
        for move in res:
            if move.product_id:
                if move.company_id.show_mo_validation:
                    move.stock_aisle = move.product_id.sudo().ca_aisle_id.name
                else:
                    move.stock_aisle = move.product_id.sudo().aisle.name
        return res

class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'
    _order = 'stock_aisle asc'

    stock_aisle = fields.Char(string="Aisle", related='move_id.stock_aisle', store=True)
    # stock_aisle = fields.Char(string="Aisle")
    

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def action_update_stock_aisle(self):
        for rec in self:
            for line in rec.move_ids_without_package:
                if rec.company_id.show_mo_validation:
                    line.stock_aisle = line.product_id.sudo().ca_aisle_id.name
                else:
                    line.stock_aisle = line.product_id.sudo().aisle.name