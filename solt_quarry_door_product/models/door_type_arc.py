from odoo import fields, models, api

TYPE_ARC = {
    'none': 'None',
    'simulated_eyebrow': 'Simulated Eyebrow arch',
    'custom': 'Custom',
    'darla': 'Darla',
    'eliptical': 'Eliptical',
    'eyebrow': 'Eyebrow',
    'full': 'Full',
    'gothic': 'Gothic',
    'provenzal': 'Provenzal',
}


class DoorTypeArc(models.Model):
    _name = 'door.type.arc'
    _inherit = 'door.abstract'
    _description = 'Door type of arc'

    type_arc = fields.Selection([
        ('none', 'None'),
        ('simulated_eyebrow', 'Simulated Eyebrow arch'),
        ('custom', 'Custom'),
        ('darla', 'Darla'),
        ('eliptical', 'Eliptical'),
        ('eyebrow', 'Eyebrow'),
        ('full', 'Full'),
        ('gothic', 'Gothic'),
        ('provenzal', 'Provenzal'),
    ], 'Type', default='none')
    name = fields.Char('Name', required=True, compute="_compute_name")

    @api.depends('type_arc')
    def _compute_name(self):
        for record in self:
            record.name = TYPE_ARC.get(record.type_arc, '')
