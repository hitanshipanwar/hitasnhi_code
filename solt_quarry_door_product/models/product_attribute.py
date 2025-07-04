# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

ATTRIBUTE_TYPE = [
    ('family', 'Family Attribute'),
    ('color', 'Color Attribute'),
    ('forge', 'WrouhtIron Attribute'),
    ('anchor', 'Anchor Attribute'),
    ('hinge', 'Hinge Attribute'),
    ('molding', 'Molding Attribute'),
    ('handle', 'Pull Handle Attribute'),
    ('deadbolt', 'Deadbolt Attribute'),
    ('arc', 'Arc Attribute'),
    ('glass', 'Glass Attribute'),
    ('dust_guard', 'Threshold Type Attribute'),
    ('latch', 'Latch Attribute'),
    ('flashing', 'Flashing Attribute'),
    ('preparations', 'Preparations Attribute'),
    ('panel', 'Bottom Panel Attribute'),
    ('setup', 'Setup Attribute'),
]


class ProductAttribute(models.Model):
    _inherit = 'product.attribute'

    attribute_type = fields.Selection(ATTRIBUTE_TYPE, 'Attribute type', help="Technical field to identify the type of attribute")

    @api.constrains('attribute_type')
    def _check_is_color_attribute(self):
        for record in self:
            if record.attribute_type:
                product_att = record._get_record()
                attribute_type_name = record._get_attribute_type_name()
                if product_att.filtered(lambda r: r.attribute_type == record.attribute_type):
                    raise ValidationError(_("There is already an attribute marked as the {}.".format(attribute_type_name.get(record.attribute_type))))

    def _get_attribute_type_name(self):
        return {
            'family': _('Family Attribute'),
            'color': _('Color Attribute'),
            'forge': _('Forge Attribute'),
            'anchor': _('Anchor Attribute'),
            'hinge': _('Hinge Attribute'),
            'molding': _('Molding Attribute'),
            'handle': _('Pull Handle Attribute'),
            'deadbolt': _('Deadbolt Attribute'),
            'arc': _('Arc Attribute'),
            'glass': _('Glass Attribute'),
            'dust_guard': _('Threshold Type Attribute'),
            'latch': _('Latch Attribute'),
            'flashing': _('Flashing Attribute'),
            'preparations': _('Preparations Attribute'),
            'panel': _('Bottom Panel Attribute'),
            'setup': _('Setup Attribute'),
        }

    def _get_record(self):
        self.ensure_one()
        return self.env[self._name].search([('id', '!=', self.id)])