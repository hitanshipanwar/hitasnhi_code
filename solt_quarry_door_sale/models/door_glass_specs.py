
from markupsafe import Markup
from odoo import _, api, fields, models
from .specs_sale import _get_factor_convert_ft2_to_in2


class DoorGlassSpecs(models.Model):
    _name = 'door.glass.specs'
    _description = 'Glass Specifications'

    specs_id = fields.Many2one('specs.sale', string='Glass Specs', ondelete='cascade', index=True, copy=False)
    glass_piece_id = fields.Many2one('door.glass.piece', string='ID Glass Piece')
    handing_glass_id = fields.Many2one('door.handing.glass', string='Handing Glass')
    glass_type_id = fields.Many2one('product.attribute.value', string='Glass type',
                                     domain="[('attribute_id.attribute_type', '=', 'glass')]")
    radius_id = fields.Many2one('door.radius', string='Radius')
    sequence = fields.Integer()
    glass_width = fields.Float(string='Width', digits='Product Unit of Measure')
    glass_height = fields.Float(string='Height', digits='Product Unit of Measure')
    glass_qty = fields.Float(string='Qty', digits='Product Unit of Measure', compute="_compute_glass_qty")

    @api.depends('glass_height', 'glass_width')
    def _compute_glass_qty(self):
        for record in self:
            record.glass_qty = (record.glass_width * record.glass_height) / _get_factor_convert_ft2_to_in2(self)

    def write(self, values):
        FIELS_SPECS_NAME = ['glass_piece_id', 'handing_glass_id', 'glass_type_id', 'radius_id',
                            'glass_width', 'glass_height']
        if any(field in values for field in FIELS_SPECS_NAME):
            self._update_line(values)
        result = super().write(values)
        return result

    def _update_line(self, values):
        specs = self.mapped('specs_id')
        for spec in specs:
            spec_lines = self.filtered(lambda x: x.specs_id == spec)
            msg = Markup("<b>%s</b><ul>") % _(f"The glass specifications of the spec {spec.name} were updated by user {self.env.user.name}")
            for line in spec_lines:
                msg += Markup("<li> %s: <br/>") % line.glass_type_id.name
                if 'glass_piece_id' in values and values['glass_piece_id'] != line.glass_piece_id.id:
                    glass_piece_id = self.env['door.glass.piece'].browse(values['glass_piece_id'])
                    msg += _(
                        "PIECE: %(old_value)s -> %(new_value)s",
                        old_value=line.glass_piece_id.name,
                        new_value=glass_piece_id.name
                    ) + Markup("<br/>")
                if 'handing_glass_id' in values and values['handing_glass_id'] != line.handing_glass_id.id:
                    handing_glass_id = self.env['door.handing.glass'].browse(values['handing_glass_id'])
                    msg += _(
                        "HANDING: %(old_value)s -> %(new_value)s",
                        old_value=line.handing_glass_id.name,
                        new_value=handing_glass_id.name
                    ) + Markup("<br/>")
                if 'glass_type_id' in values and values['glass_type_id'] != line.glass_type_id.id:
                    glass_type_id = self.env['product.attribute.value'].browse(values['glass_type_id'])
                    msg += _(
                        "TYPE: %(old_value)s -> %(new_value)s",
                        old_value=line.glass_type_id.name,
                        new_value=glass_type_id.name
                    ) + Markup("<br/>")
                if 'radius_id' in values and values['radius_id'] != line.radius_id.id:
                    radius_id = self.env['door.radius'].browse(values['radius_id'])
                    msg += _(
                        "RADIUS: %(old_value)s -> %(new_value)s",
                        old_value=line.radius_id.name,
                        new_value=radius_id.name
                    ) + Markup("<br/>")
                if 'glass_width' in values and values['glass_width'] != line.glass_width:
                    msg += _(
                        "WIDTH: %(old_value)s -> %(new_value)s",
                        old_value=line.glass_width,
                        new_value=values['glass_width']
                    ) + Markup("<br/>")
                if 'glass_height' in values and values['glass_height'] != line.glass_height:
                    msg += _(
                        "HEIGHT: %(old_value)s -> %(new_value)s",
                        old_value=line.glass_height,
                        new_value=values['glass_height']
                    ) + Markup("<br/>")

            msg += Markup("</ul>")
            spec.message_post(body=msg)