from odoo import fields, models


class StockQuant(models.Model):
    _inherit = 'stock.quant'
    
    reason = fields.Char('Reason')

    def _get_inventory_move_values(self, qty, location_id, location_dest_id, out=False):
        res = super()._get_inventory_move_values(qty, location_id, location_dest_id, out=out)
        if self.reason:
            res['move_line_ids'][0][2]['reason'] = self.reason
            self.reason = ""
        return res
    
    def _get_inventory_fields_write(self):
        res = super()._get_inventory_fields_write()
        res.append('reason')
        return res


class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'
    
    reason = fields.Char('Reason')
