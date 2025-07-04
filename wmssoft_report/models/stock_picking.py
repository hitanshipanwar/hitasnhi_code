from odoo import fields, models


class StockPickingInherits(models.Model):
    _inherit = 'stock.picking'

    cartons = fields.Char(string="Cartons")
    # rep_template_id = fields.Many2one('report.company', 'Templates to Print', required=True)
    rep_template_id = fields.Many2one('report.company', 'Templates to Print', related='partner_id.rep_template_id')


class StockMove(models.Model):
    _inherit = 'stock.move'
    
    org_qty = fields.Float('Orginal Move Qty')
    
    # def _get_new_picking_values(self):
    #     res = super(StockMove, self)._get_new_picking_values()
    #     res['rep_template_id'] = self.mapped('group_id.sale_id.rep_template_id').id
    #     return res
    
    def _prepare_move_split_vals(self, qty):
        res = super(StockMove, self)._prepare_move_split_vals(qty)
        res['org_qty'] = qty
        return res


class StockRule(models.Model):
    _inherit = 'stock.rule'
    
    def _get_stock_move_values(self, product_id, product_qty, product_uom, location_id, name, origin, company_id, values):
        res = super(StockRule, self)._get_stock_move_values(product_id, product_qty, product_uom, location_id, name, origin, company_id, values)
        res['org_qty'] = res.get('product_uom_qty', product_qty)
        return res


class StockLocationRoute(models.Model):
    _inherit = 'stock.location.route'

    short_name = fields.Text("Short Name")

