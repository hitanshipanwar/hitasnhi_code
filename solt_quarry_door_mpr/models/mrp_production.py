# -*- coding: utf-8 -*-

from odoo import models, fields, api


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    specs_id = fields.Many2one('specs.sale', string='Spec', compute="_compute_mrp_production_child_count", store=True)
    mrp_shipment = fields.Char("No. Embarque")
    bom_id = fields.Many2one(
        'mrp.bom', 'Bill of Material', readonly=False,
        domain="""[
            '&', 
               '&',
                   '|', ('company_id', '=', False), ('company_id', '=', company_id),
                   '&',
                       '|', ('product_id','=', product_id),
                       '&', ('product_tmpl_id.product_variant_ids','=', product_id), ('product_id','=', False),
                   ('type', '=', 'normal'),
               ('is_available', '=', True)]""",
        check_company=True, compute='_compute_bom_id', store=True, precompute=True,
        help="Bills of Materials, also called recipes, are used to autocomplete components and work order instructions.")

    @api.depends('procurement_group_id.stock_move_ids.created_production_id.procurement_group_id.mrp_production_ids',
                 'procurement_group_id.stock_move_ids.move_orig_ids.created_production_id.procurement_group_id.mrp_production_ids',
                 'bom_id.specs_id'
                 )
    def _compute_mrp_production_child_count(self):
        for production in self:
            super(MrpProduction, self)._compute_mrp_production_child_count()
            if production.bom_id.specs_id:
                production.specs_id = production.bom_id.specs_id
            else:
                children = production._get_children()
                sources = production._get_sources()
                spec = (children | sources).mapped('specs_id')
                production.specs_id = spec
                (children | sources).update({'specs_id': spec})
            production.bom_id._compute_is_available()

    def action_confirm(self):
        res = super(MrpProduction, self).action_confirm()
        for production in self:
            if production.mrp_shipment:
                children = production._get_children()
                children.mrp_shipment = production.mrp_shipment
        return res

    @api.depends('procurement_group_id', 'procurement_group_id.stock_move_ids.group_id')
    def _compute_picking_ids(self):
        super(MrpProduction, self)._compute_picking_ids()
        for order in self:
            if order.specs_id:
                order._update_move_description(order.picking_ids)
                if order.move_finished_ids:
                    for move in order.move_finished_ids:
                        if move.description_picking and self.specs_id.name not in move.description_picking:
                            description_picking = move.description_picking + '\n' + self.specs_id.name
                            move.description_picking = description_picking
                        if not move.description_picking:
                            description_picking = self.specs_id.name
                            move.description_picking = description_picking

    def _update_move_description(self, picking_ids):
        self.ensure_one()
        for move in picking_ids.move_ids_without_package:
            if move.description_picking and self.specs_id.name not in move.description_picking:
                description_picking = move.description_picking + '\n' + self.specs_id.name
                move.description_picking = description_picking