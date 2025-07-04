
from collections import defaultdict
from odoo import models, _


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def action_view_mrp_production(self):
        action = super(SaleOrder, self).action_view_mrp_production()
        self._update_bom_id_from_specs_to_production()

        return action

    def _update_bom_id_from_specs_to_production(self):
        self.ensure_one()
        if self.specs_sale_ids:
            production_updated = self.env['mrp.production']
            bom_used = self.env['mrp.bom']
            valid_specs = self.specs_sale_ids.filtered(lambda s: s.state in ['bom'])
            for spec in valid_specs:
                specs_product_type_id = spec.specs_product_type_id
                production_to_update = self.mrp_production_ids.filtered(lambda p: p.product_tmpl_id == specs_product_type_id and
                                                                                  p.bom_id != spec.bom_ids and p.bom_id.id not in bom_used.ids)
                if len(production_to_update) == 1:
                    production_to_update.write({'bom_id': spec.bom_ids.id})
                    production_updated |= production_to_update
                    bom_used |= spec.bom_ids
                if len(production_to_update) > 1:
                    prod = production_to_update[0].write({'bom_id': spec.bom_ids.id})
                    production_updated |= production_to_update[0]
                    bom_used |= spec.bom_ids


