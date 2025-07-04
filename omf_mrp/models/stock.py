from odoo import fields, models


class Picking(models.Model):
    _inherit = "stock.picking"

    inventory_reconciled = fields.Boolean()

    def action_open_quants(self):
        products = self.move_ids_without_package.product_id
        action = products.action_open_quants()
        action["name"] = 'Reconcile Inventory'
        return action
