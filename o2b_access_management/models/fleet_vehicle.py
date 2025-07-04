# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools, _
from odoo.exceptions import AccessError, ValidationError

class FleetVehicle(models.Model):
    _inherit = 'fleet.vehicle'    

    @api.constrains('fleet_location_id')
    def _check_unique_location(self):
        for record in self:
            existing_vehicle = self.env['fleet.vehicle'].search([
                ('fleet_location_id', '=', record.fleet_location_id.id),
                ('id', '!=', record.id)])
            if existing_vehicle:
                raise ValidationError('Each vehicle location must be unique.')

    fleet_location_id = fields.Many2one('stock.location', 'Location', tracking=True, store=True)
        

    def write(self, vals):
        """Restrict editing for users in fleet_group_user."""
        if self.env.user.has_group('fleet.fleet_group_user') and not self.env.user.has_group('fleet.fleet_group_manager'):
            raise AccessError(_("You are not allowed to edit vehicles."))

        res = super(FleetVehicle, self).write(vals)
        for vehicle in self:
            if vehicle.driver_id:
                # vehicle.driver_id.sudo().write({'fleet_vehicle_ids': vehicle.id})
                vehicle.driver_id.sudo().write({'fleet_vehicle_ids': [(4, vehicle.id)]})
            # if vehicle.driver_id and vehicle.driver_id.user_ids and vehicle.fleet_location_id:
            #     vehicle.fleet_location_id.write({
            #         'user_ids': [(4, vehicle.driver_id.user_ids.id)]
            #     })
        return res


    @api.model
    def create(self, vals):
        """Override create to update driver's assigned vehicle on vehicle creation."""
        vehicle = super(FleetVehicle, self).create(vals)
        if vehicle.driver_id:
            # vehicle.driver_id.user_id.write({'fleet_vehicle_ids': vehicle.id})
            vehicle.driver_id.write({'fleet_vehicle_ids': [(4, vehicle.id)]})
        # if vehicle.fleet_location_id and vehicle.driver_id and vehicle.driver_id.user_ids:
        #         vehicle.fleet_location_id.write({
        #                 'user_ids': [(4, vehicle.driver_id.user_ids.id)]
        #             })
        return vehicle