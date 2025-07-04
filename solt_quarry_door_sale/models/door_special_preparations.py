from odoo import _, api, fields, models

import logging

_logger = logging.getLogger(__name__)


class DoorSpecialPreparations(models.Model):
    _name = 'door.special.preparations'
    _description = 'Door special preparations'

    preparations_ids = fields.Many2many('product.attribute.value', string='Special Prep', domain="[('attribute_id.attribute_type', '=', 'preparations')]")
    amount_preparations = fields.Integer(string='Quantity')
    sequence = fields.Integer()

    specs_id = fields.Many2one('specs.sale', string='Specs', ondelete='cascade', index=True, copy=False)
    # specs_preparations_ids = fields.Many2many(
# 	'product.attribute.value',
#     string='Preparaciones Especiales',
#     related='prep_id.specs_preparations_ids'
# )
