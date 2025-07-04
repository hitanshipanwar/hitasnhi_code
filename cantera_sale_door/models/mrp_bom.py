from odoo import models, fields, api

class MrpBom(models.Model):
    _inherit = ["mrp.bom"]
    _description = 'Lista de Materiales'

    specs_id = fields.Many2one(
		'specs.sale',
		string='Hoja de Specs'
	)