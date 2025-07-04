from odoo import fields, models


class StockPicking(models.Model):
    _inherit = 'stock.picking'
    
    def _action_done(self):
        res = super(StockPicking, self)._action_done()
        for pick in self.filtered(lambda p: p.purchase_id and p.partner_id):
            # we KNOW this is for some company
            fname = 'us_last_vendor_id'
            if pick.company_id.country_id.code == 'CA':
                fname = 'ca_last_vendor_id'
            pick.move_lines.product_id.write({
                fname: pick.partner_id.id,
            })
        return res
