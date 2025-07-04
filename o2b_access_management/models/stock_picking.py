# -*- coding: utf-8 -*-
from odoo import fields, models, api, exceptions, _
from odoo.exceptions import AccessError

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    warehouse_users = fields.Many2many('res.users', 'new_stock_res_user_rel', 'new_picking_id', 'new_user_id', compute="_compute_warehouse_allow_user", store=True)
    location_users = fields.Many2many('res.users', 'new_picking_res_user_rel', 'new_picking_location_id', 'new_picking_user_id', compute="_compute_location_allow_user", store=True)

    @api.depends('location_id', 'location_id.user_ids', 'location_dest_id', 'location_dest_id.user_ids')
    def _compute_location_allow_user(self):
        for rec in self:
            user_ids = set()
            admin_user_ids = self.env.ref('stock.group_stock_manager').users.ids
            if admin_user_ids:
                user_ids.update(admin_user_ids)
            if rec.location_id and rec.location_id.user_ids:
                user_ids.update(rec.location_id.user_ids.ids)
            if user_ids:
                rec.location_users = [(6, 0, list(user_ids))]
            else:
                rec.location_users = False

    @api.depends('location_id', 'location_id.warehouse_id', 'location_id.warehouse_id.user_ids', 'location_dest_id', 'location_dest_id.warehouse_id', 'location_dest_id.warehouse_id.user_ids')
    def _compute_warehouse_allow_user(self):
        for rec in self:
            user_ids = set()
            admin_user_ids = self.env.ref('stock.group_stock_manager').users.ids
            if admin_user_ids:
                user_ids.update(admin_user_ids)
            if rec.location_id and rec.location_id.warehouse_id and rec.location_id.warehouse_id.user_ids:
                user_ids.update(rec.location_id.warehouse_id.user_ids.ids)
            if rec.location_dest_id and rec.location_dest_id.warehouse_id and rec.location_dest_id.warehouse_id.user_ids:
                user_ids.update(rec.location_dest_id.warehouse_id.user_ids.ids)
            if user_ids:
                rec.warehouse_users = [(6, 0, list(user_ids))]
            else:
                rec.warehouse_users = False

    @api.model
    def create(self, vals):
        """Restrict creation for users in stock.group_stock_user unless they are in stock.group_stock_manager."""
        if self.env.user.has_group('stock.group_stock_user') and not self.env.user.has_group('stock.group_stock_manager') and not self.env.user.has_group('o2b_access_management.group_warehoues_user_assigned_van') and not self.env.user.has_group('o2b_access_management.group_manufacturing_access_inventory'):
            raise AccessError(_("You are not allowed to create transfer."))
        return super(StockPicking, self).create(vals)

    def unlink(self):
        """Restrict deletion for users in stock.group_stock_user unless they are in stock.group_stock_manager."""
        if self.env.user.has_group('stock.group_stock_user') and not self.env.user.has_group('stock.group_stock_manager'):
            raise AccessError(_("You are not allowed to delete transfer."))
        return super(StockPicking, self).unlink()

class StockQuant(models.Model):
    _inherit = 'stock.quant'

    def _domain_location_id(self):
        if not self._is_inventory_mode():
            if self.env.user.has_group('o2b_access_management.group_manufacturing_access_inventory'):
                base_domain = [('user_ids', 'in', [self.env.user.id])]
                return base_domain
            else:
                return
            return
        base_domain = [('usage', 'in', ['internal', 'transit'])]
        if self.env.user.has_group('o2b_access_management.group_warehoues_user_assigned_van'):
            base_domain = ['|', ('usage', 'in', ['internal', 'transit']), ('id', 'in', self.env.user.fleet_location_ids.ids)]
        return base_domain

    user_id = fields.Many2one('res.users', default=lambda self: self.env.uid)
    fleet_location_ids = fields.Many2many(
        'stock.location', 
        related='user_id.fleet_location_ids',
        readonly=True
    )
    location_id = fields.Many2one(
        'stock.location', 'Location',
        domain=lambda self: self._domain_location_id(),
        auto_join=True, ondelete='restrict', required=True, index=True)

    new_location_id = fields.Many2one(
        'stock.location', 'Location',
        domain=lambda self: self._domain_location_id(),
        auto_join=True, ondelete='restrict', required=True, index=True)

    location_users = fields.Many2many('res.users', 'new_quant_res_user_rel', 'new_location_id', 'new_user_id', compute="_compute_location_allow_user", store=True)

    @api.depends('location_id', 'location_id.user_ids')
    def _compute_location_allow_user(self):
        for rec in self:
            user_ids = set()
            admin_user_ids = self.env.ref('stock.group_stock_manager').users.ids
            if admin_user_ids:
                user_ids.update(admin_user_ids)
            if rec.location_id and rec.location_id.user_ids:
                user_ids.update(rec.location_id.user_ids.ids)
            if user_ids:
                rec.location_users = [(6, 0, list(user_ids))]
            else:
                rec.location_users = False


    @api.onchange('location_id', 'new_location_id')
    def _onchange_location_fields(self):
        """ Synchronize location_id and new_location_id based on changes """
        user_has_group_van = self.env.user.has_group('o2b_access_management.group_warehoues_user_assigned_van')
        user_has_group_manufacturing = self.env.user.has_group('o2b_access_management.group_manufacturing_access_inventory')
        for rec in self:
            if rec.new_location_id and (user_has_group_van or user_has_group_manufacturing):
                rec.location_id = rec.new_location_id
            elif rec.location_id and not (user_has_group_van or user_has_group_manufacturing):
                rec.new_location_id = rec.location_id

    @api.model
    def create(self, vals):
        """ Synchronize location_id and new_location_id on record creation """
        user_has_group = self.env.user.has_group('o2b_access_management.group_warehoues_user_assigned_van')

        if 'new_location_id' in vals and user_has_group:
            vals['location_id'] = vals['new_location_id']
        elif 'location_id' in vals:
            vals['new_location_id'] = vals['location_id']

        return super(StockQuant, self).create(vals)

    @api.model
    def _is_inventory_mode(self):
        """ 
        Used to control whether a quant was written on or created during an
        "inventory session", meaning a mode where we need to create the stock.move
        record necessary to be consistent with the `inventory_quantity` field.
        """
        if self.env.user.has_group('o2b_access_management.group_warehoues_user_assigned_van') or ('stock.group_stock_manager'):
            return False

        return self.env.context.get('inventory_mode') and self.user_has_groups('stock.group_stock_user')

    @api.model
    def action_update_new_location_id(self):
        """This method will update new_location_id for records where it is empty."""
        records = self.search([('new_location_id', '=', False)])
        for record in records:
            record.new_location_id = record.location_id  


class StockPickingBatch(models.Model):
    _inherit = 'stock.picking.batch'

    warehouse_users = fields.Many2many('res.users', 'stock_batch_res_user_rel', 'picking_batch_id', 'user_id', compute="_compute_warehouse_allow_user_batch_picking", store=True)

    @api.depends('picking_type_id', 'picking_type_id.warehouse_id')
    def _compute_warehouse_allow_user_batch_picking(self):
        for rec in self:
            user_ids = set()
            if rec.picking_type_id and rec.picking_type_id.warehouse_id:
                user_ids.update(rec.picking_type_id.warehouse_id.user_ids.ids)
            if user_ids:
                rec.warehouse_users = [(6, 0, list(user_ids))]
            else:
                rec.warehouse_users = False

    @api.model
    def create(self, vals):
        """Restrict creation for users in stock.group_stock_user unless they are in stock.group_stock_manager."""
        if self.env.user.has_group('stock.group_stock_user') and not self.env.user.has_group('stock.group_stock_manager'):
            raise AccessError(_("You are not allowed to create batch transfer."))
        return super(StockPickingBatch, self).create(vals)

    def unlink(self):
        """Restrict deletion for users in stock.group_stock_user unless they are in stock.group_stock_manager."""
        if self.env.user.has_group('stock.group_stock_user') and not self.env.user.has_group('stock.group_stock_manager'):
            raise AccessError(_("You are not allowed to delete batch transfer."))
        return super(StockPickingBatch, self).unlink()


class StockScrap(models.Model):
    _inherit = 'stock.scrap'

    warehouse_users = fields.Many2many('res.users', 'stock_scrap_res_user_rel', 'picking_scrap_id', 'scrap_user_id', compute="_compute_warehouse_allow_user_scrap", store=True)

    @api.depends('location_id', 'location_id.warehouse_id', 'location_id.warehouse_id.user_ids', 'scrap_location_id', 'scrap_location_id.warehouse_id', 'scrap_location_id.warehouse_id.user_ids')
    def _compute_warehouse_allow_user_scrap(self):
        for rec in self:
            user_ids = set()
            admin_user_ids = self.env.ref('stock.group_stock_manager').users.ids
            if admin_user_ids:
                user_ids.update(admin_user_ids)
            if rec.location_id and rec.location_id.warehouse_id and rec.location_id.warehouse_id.user_ids:
                user_ids.update(rec.location_id.warehouse_id.user_ids.ids)
            if rec.scrap_location_id and rec.scrap_location_id.warehouse_id and rec.scrap_location_id.warehouse_id.user_ids:
                user_ids.update(rec.scrap_location_id.warehouse_id.user_ids.ids)
            if user_ids:
                rec.warehouse_users = [(6, 0, list(user_ids))]
            else:
                rec.warehouse_users = False

    @api.model
    def create(self, vals):
        """Restrict creation for users in stock.group_stock_user unless they are in stock.group_stock_manager."""
        if self.env.user.has_group('stock.group_stock_user') and not self.env.user.has_group('stock.group_stock_manager'):
            raise AccessError(_("You are not allowed to create scrap record."))
        return super(StockScrap, self).create(vals)

    def unlink(self):
        """Restrict deletion for users in stock.group_stock_user unless they are in stock.group_stock_manager."""
        if self.env.user.has_group('stock.group_stock_user') and not self.env.user.has_group('stock.group_stock_manager'):
            raise AccessError(_("You are not allowed to delete scrap record."))
        return super(StockScrap, self).unlink()



class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    def unlink(self):
        """Restrict deletion for record."""
        if self.env.user.has_group('mrp.group_mrp_user') and not self.env.user.has_group('mrp.group_mrp_manager'):
            raise AccessError(_("You are not allowed to delete manufacturing order."))
        if self.env.user.has_group('o2b_access_management.group_cannot_delete_other_mo'):
            for mo in self:
                workcenter_users = mo.workorder_ids.mapped('workcenter_id.user_ids')
                if self.env.user not in workcenter_users:
                    raise AccessError(_("You are not allowed to delete Manufacturing Orders created by other users."))

        return super(MrpProduction, self).unlink()

class MrpWorkOrder(models.Model):
    _inherit = 'mrp.workorder'

    def unlink(self):
        """Restrict deletion for record."""
        if self.env.user.has_group('o2b_access_management.group_cannot_delete_other_mo'):
            for order in self:
                workcenter_users = order.workcenter_id.mapped('user_ids')
                if self.env.user not in workcenter_users:
                    raise AccessError(_("You are not allowed to delete Work Orders belongs to other's work centers."))

        return super(MrpWorkOrder, self).unlink()

class MrpUnbuild(models.Model):
    _inherit = 'mrp.unbuild'

    def unlink(self):
        """Restrict deletion for record."""
        if self.env.user.has_group('o2b_access_management.group_cannot_delete_other_mo'):
            raise AccessError(_("You are not allowed to delete record."))

        return super(MrpUnbuild, self).unlink()


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    def unlink(self):
        """Restrict deletion for record."""
        if self.env.user.has_group('o2b_access_management.group_cannot_delete_other_mo'):
            raise AccessError(_("You are not allowed to delete record."))

        return super(ProductTemplate, self).unlink()

class ProductProduct(models.Model):
    _inherit = 'product.product'

    def unlink(self):
        """Restrict deletion for record."""
        if self.env.user.has_group('o2b_access_management.group_cannot_delete_other_mo'):
            raise AccessError(_("You are not allowed to delete record."))

        return super(ProductProduct, self).unlink()

class MrpBom(models.Model):
    _inherit = 'mrp.bom'

    def unlink(self):
        """Restrict deletion for record."""
        if self.env.user.has_group('o2b_access_management.group_cannot_delete_other_mo'):
            raise AccessError(_("You are not allowed to delete record."))

        return super(MrpBom, self).unlink()

class StockProductionLot(models.Model):
    _inherit = 'stock.production.lot'

    def unlink(self):
        """Restrict deletion for record."""
        if self.env.user.has_group('o2b_access_management.group_cannot_delete_other_mo'):
            raise AccessError(_("You are not allowed to delete record."))

        return super(StockProductionLot, self).unlink()

class StockQuantPackage(models.Model):
    _inherit = 'stock.quant.package'

    def unlink(self):
        """Restrict deletion for record."""
        if self.env.user.has_group('o2b_access_management.group_cannot_delete_other_mo'):
            raise AccessError(_("You are not allowed to delete record."))

        return super(StockQuantPackage, self).unlink()
        

class MrpRoutingWorkcenter(models.Model):
    _inherit = 'mrp.routing.workcenter'

    def unlink(self):
        """Restrict deletion for record."""
        if self.env.user.has_group('o2b_access_management.group_cannot_delete_other_mo'):
            for order in self:
                workcenter_users = order.workcenter_id.mapped('user_ids')
                if self.env.user not in workcenter_users:
                    raise AccessError(_("You are not allowed to delete record."))

        return super(MrpRoutingWorkcenter, self).unlink()


class StockWarehouse(models.Model):
    _inherit = 'stock.warehouse'

    user_ids = fields.Many2many(
        'res.users',
        'stock_warehouse_user_rel',
        'warehouse_id',
        'user_id',
        string='Allowed Users',
        help="Users who are allowed to access this warehouse.")

    @api.model
    def create(self, vals):
        """Restrict deletion for record."""
        if self.env.user.has_group('o2b_access_management.group_cannot_access_warehoues'):
            raise AccessError(_("You are not allowed to create warehouse."))
        
        return super(StockWarehouse, self).create(vals)

    def unlink(self):
        """Restrict deletion for record."""
        if self.env.user.has_group('o2b_access_management.group_cannot_access_warehoues'):
            raise AccessError(_("You are not allowed to delete warehouse."))
        
        return super(StockWarehouse, self).unlink()



class MrpWorkcenter(models.Model):
    _inherit = 'mrp.workcenter'

    user_ids = fields.Many2many(
        'res.users',
        'mrp_workcenter_rel',
        'workcenter_id',
        'user_id',
        string='Allowed Users',
        help="Users who are allowed to access this workcenter.")

    def unlink(self):
        """Restrict deletion for record."""
        if self.env.user.has_group('o2b_access_management.group_cannot_delete_other_mo'):
            raise AccessError(_("You are not allowed to delete work centers."))
        
        return super(MrpWorkcenter, self).unlink()

class StockLocation(models.Model):
    _inherit = 'stock.location'

    user_ids = fields.Many2many(
        'res.users',
        'stock_location_user_rel',
        'location_id',
        'user_id',
        string='Allowed Users',
        help="Users who are allowed to access this location.")
