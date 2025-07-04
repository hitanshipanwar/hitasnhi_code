from odoo import fields, models, api, _

class SaleOrderLine(models.Model):
    _inherit = 'sale.order'

    picking_internal_ids = fields.One2many('stock.picking','sale_internal_id',string='Picking Internal')
    internal_count = fields.Integer(string='Internal Orders', compute='_compute_internal_picking_ids')


    @api.depends('picking_internal_ids')
    def _compute_internal_picking_ids(self):
        for order in self:
            order.internal_count = len(order.picking_internal_ids)

    def _action_confirm(self):
        res = super(SaleOrderLine,self)._action_confirm()
        if self.is_custom_order:
            for picking in self.picking_ids:
                picking.write({'move_ids':[(5,0)]})
        for order in self:
            for picking in order.picking_ids:
                picking.tag_job_sale_ref = order.id
        return res

    def action_view_internal(self):
        return self._get_action_view_internal_picking(self.picking_internal_ids)

    def _get_action_view_internal_picking(self, pickings):
        action = self.env["ir.actions.actions"]._for_xml_id("stock.action_picking_tree_all")
        if len(pickings) > 1:
            action['domain'] = [('id', 'in', pickings.ids)]
        elif pickings:
            form_view = [(self.env.ref('stock.view_picking_form').id, 'form')]
            if 'views' in action:
                action['views'] = form_view + [(state,view) for state,view in action['views'] if view != 'form']
            else:
                action['views'] = form_view
            action['res_id'] = pickings.id
        # Prepare the context.
        picking_id = pickings.filtered(lambda l: l.picking_type_id.code == 'internal')
        if picking_id:
            picking_id = picking_id[0]
        else:
            picking_id = pickings[0]
        action['context'] = dict(self._context, default_partner_id=self.partner_id.id, default_picking_type_id=picking_id.picking_type_id.id, default_origin=self.name, default_group_id=picking_id.group_id.id)
        return action