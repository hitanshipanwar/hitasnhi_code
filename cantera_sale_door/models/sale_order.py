from odoo import models, fields, api

class SaleOrder(models.Model):
    _inherit = ["sale.order"]
    _description = 'Presupuesto'

    campo_o2m_ids = fields.One2many(
        'specs.sale',
        'specs_sale_id', 
        string='specs'
    )
    specs_count = fields.Integer(
        string='Total Specs',
        compute='_count_specs'
    )

    @api.depends('campo_o2m_ids.specs_sale_id')
    def _count_specs(self):
        for record in self:
            score = self.env['specs.sale'].search([
                ('specs_sale_id', '=', record.id)
            ])
            record.specs_count = len(score)

    def specs_call_view(self):
        return {
            "name": 'Specs',
            "view_mode": 'tree,form',
            "res_model": 'specs.sale',
            "type": 'ir.actions.act_window',
            "target": 'current',
            "domain": [
                ('specs_sale_id', '=', self.id)
            ],
            "context": {'default_specs_sale_id': self.id}
        }
    