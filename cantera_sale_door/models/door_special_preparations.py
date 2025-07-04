from odoo import _, api, fields, models



import logging
_logger = logging.getLogger(__name__)




class DoorSpecialPreparations(models.Model):
    _name = 'door.special.preparations'
    
    preparations_ids = fields.Many2many(
		'product.attribute.value',
        string='Preparaciones Especiales',
    )
    amount_preparations = fields.Integer(
        string='Cantidad'
    )
    sequence = fields.Integer()
    
    prep_id = fields.Many2one(
        'specs.sale',
        string='Preparaciones Especiales'
    )
    specs_preparations_ids = fields.Many2many(
		'product.attribute.value',
        string='Preparaciones Especiales',
        related='prep_id.specs_preparations_ids'
    )