import string
from odoo import api, models, fields


class AddNotes(models.Model):
    _inherit = "sale.order"

    order_notes_for_transfer = fields.Html(string="Order Notes")

    @api.model
    def write(self, vals):
        rec = super(AddNotes, self).write(vals)
        for picking in self.picking_ids:
            picking.note = self.order_notes_for_transfer
        return rec


class StockPicking(models.Model):
    _inherit = "stock.picking"

    @api.model
    def create(self, vals):
        rec = super(StockPicking, self).create(vals)
        if rec.origin:
            sale_order_id = self.env['sale.order'].search([('name', '=', rec.origin)])
            if sale_order_id:
                rec.note = sale_order_id.order_notes_for_transfer
        return rec
