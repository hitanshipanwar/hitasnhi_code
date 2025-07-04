from odoo import models, fields, api

class ResUsers(models.Model):
    _inherit = 'res.users'

    fleet_vehicle_ids = fields.Many2many(
        'fleet.vehicle',
        related='partner_id.fleet_vehicle_ids',
        string="Assigned Vehicles",
    )

    fleet_location_ids = fields.Many2many(
        'stock.location',
        string="Fleet Locations",
        compute="_compute_fleet_locations",
        store=True
    )

    @api.depends('fleet_vehicle_ids', 'fleet_vehicle_ids.fleet_location_id')
    def _compute_fleet_locations(self):
        for user in self:
            user.fleet_location_ids = user.fleet_vehicle_ids.mapped('fleet_location_id')


class ResPartner(models.Model):
    _inherit = 'res.partner'

    fleet_vehicle_ids = fields.Many2many(
        'fleet.vehicle',
        string="Assigned Vehicles",
    )