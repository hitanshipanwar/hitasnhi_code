from odoo import fields, models


class StockPickingImage(models.Model):
    _name = 'stock.picking.image'
    _description = 'Stock Picking Image'
    
    name = fields.Char(required=True)
    sequence = fields.Integer(default=10, index=True)
    picking_id = fields.Many2one('stock.picking', 'Transfer', required=True)
    image_1000 = fields.Image("Image", max_width=1000, max_height=1000, required=True)


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    validated_by = fields.Many2one('res.users', readonly=True)
    validated_on = fields.Datetime(readonly=True)
    stock_image_ids = fields.One2many('stock.picking.image', 'picking_id', string='Images')

    def button_validate(self):
        res = super(StockPicking, self).button_validate()
        self.validated_by = self.env.user
        self.validated_on = fields.Datetime.now()
        return res
