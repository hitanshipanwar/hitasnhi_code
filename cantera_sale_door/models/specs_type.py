from odoo import fields, models


class SpcsType(models.Model):
    _name = 'specs.type'
    _description = 'Etapas de Specs'

    name = fields.Char(
	    string='Nombre de la etapa',
	    required=True
    )
    active = fields.Boolean(
       string='Activo',
       default=True
    )
    sequence = fields.Integer(string='Secuencia')

    description = fields.Text(string='Descripción')
   
    rating_template_id = fields.Many2one(
        'mail.template',
        string='Plantilla de email de calificación',
    )
