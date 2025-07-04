from odoo import fields, models


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    country_of_origin = fields.Many2one('res.country', 'Country of Origin')
    purchase_order_notes = fields.Text('Notes')
    organic_status = fields.Selection([
        ('NOP', 'NOP'),
        ('COR', 'COR'),
        ('NON-ORG', 'NON-ORG'),
        ('US-CAN EQ.', 'US-CAN EQ.'),
        ('EU', 'EU'),
        ('JAS', 'JAS'),
        ('Letter of Extention', 'Letter of Extention'),
        ('Waiting', 'Waiting'),
        ('N/A', 'N/A'),
        ])

    def _onchange_quantity(self):
        price_unit = self.price_unit
        super(PurchaseOrderLine, self)._onchange_quantity()
        if price_unit:
            self.price_unit = price_unit
