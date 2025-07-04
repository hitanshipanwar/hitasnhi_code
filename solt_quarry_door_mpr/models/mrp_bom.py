from odoo import models, fields, api


class MrpBom(models.Model):
    _inherit = ["mrp.bom"]
    _description = 'Materials List'

    specs_id = fields.Many2one('specs.sale', string='Specs Sheet')
    is_available = fields.Boolean(string="Available", compute='_compute_is_available', store=True,
        help="Indicates whether this BOM is available for use."
    )

    @api.depends('specs_id')
    def _compute_is_available(self):
        """Marca la BoM como disponible si no está utilizada en ninguna orden de producción activa.
        """
        Production = self.env['mrp.production']
        for bom in self:
            bom = bom.with_company(bom.company_id)
            # Buscar órdenes de producción activas que usen esta BoM.
            if bom.specs_id:
                used = Production.search_count([
                    ('bom_id', '=', bom.id)
                ])
                # Si used es 0, la BoM está disponible.
                bom.is_available = (used == 0)
            else:
                bom.is_available = True

    @api.depends('code', 'specs_id')
    def _compute_display_name(self):
        super(MrpBom, self)._compute_display_name()
        for bom in self:
            if bom.specs_id:
                spec_code = bom.specs_id.sequence_name
                bom.display_name += ':' + spec_code
