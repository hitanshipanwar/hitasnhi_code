from odoo import _, api, fields, models

class DoorGlassSpecs(models.Model):
    _name = 'door.glass.specs'
    
    glass_piece_id = fields.Many2one(
        'door.glass.piece',
        string='ID Glass Piece'
    )
    handing_glass_id = fields.Many2one(
        'door.handing.glass',
        string='Handing Glass'
    )
    glass_type_id = fields.Many2many(
		'product.attribute.value',
        string='Tipo de Vidrio',
    )
    specs_glass_type_id = fields.Many2many(
		'product.attribute.value',
        string='Tipo de Vidrio',
        related='glass_id.specs_glass_type_id'
    )
    radius_id = fields.Many2one(
        'door.radius',
        string='Radius'
    )
    amount_glass = fields.Integer(
        string='Cantidad'
    )
    sequence = fields.Integer()
    glass_id = fields.Many2one(
        'specs.sale',
        string='Glass Specs'
    )
    glass_width = fields.Float(
    	string='Width',
     	digits=(12, 4)
    )
    glass_height = fields.Float(
    	string='Height',
     	digits=(12, 4)
    )
    glass_qty = fields.Float(
    	string='Qty',
     	digits=(12, 4)
    )