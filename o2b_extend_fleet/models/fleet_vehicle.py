# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import date, timedelta, datetime
from dateutil.relativedelta import relativedelta


class FleetVehicle(models.Model):
    _inherit = 'fleet.vehicle'

    insurance_policy_number = fields.Char("Insurance Policy Number", tracking=True)
    insurance_provider = fields.Char("Insurance Provider", tracking=True)
    insurance_expiry_date = fields.Date("Insurance Expiry Date", tracking=True)
    fuel_card_1 = fields.Html('Fuel Card 1')
    fuel_card_2 = fields.Html('Fuel Card 2')
    highway_toll_tag = fields.Many2many(
        'highway.toll.tag', 
        'highway_toll_tag_rel',  # this is the relation table name
        'highway_id', 'toll_tag_id', 
        string='Highway Toll Tags'
    )
    fine_ids = fields.One2many('fleet.fine', 'vehicle_id', string='Fines')
    fine_count = fields.Integer(string='Fine Count', compute='_compute_fine_count')
    # driver_assignment_ids = fields.One2many('fleet.driver.assignment', 'vehicle_id', string="Driver Assignments")
    location = fields.Char(help='Location of the vehicle (garage, ...)', tracking=True)
    next_assignation_date = fields.Date('Assignment Date', help='This is the date at which the car will be available, if not set it means available instantly', tracking=True)


    @api.model
    def _send_insurance_expiry_alerts(self):
        today = date.today()
        alert_days = [30, 15, 7]
        for days in alert_days:
            upcoming = today - timedelta(days=days)
            expiring_vehicles = self.search([('insurance_expiry_date', '=', upcoming)])
            email_template = self.env.ref('o2b_extend_fleet.insurance_expiry_email_template_o2b')
            for vehicle in expiring_vehicles:
                email_template.send_mail(vehicle.id, force_send=True, email_values={
                    'email_to': vehicle.driver_id.email
                    })

    def _compute_fine_count(self):
        for record in self:
            record.fine_count = self.env['fleet.fine'].search_count([('vehicle_id', '=', record.id)])

    def action_view_fines(self):
        return {
            'name': 'Fines',
            'type': 'ir.actions.act_window',
            'res_model': 'fleet.fine',
            'view_mode': 'tree,form',
            'domain': [('vehicle_id', '=', self.id)],
            'context': {'default_vehicle_id': self.id, 'search_default_groupby_driver': 1},
        }

    # @api.model
    # def create(self, vals):
    #     vehicle = super().create(vals)
    #     vehicle._create_driver_assignment(force=True)
    #     return vehicle

    # def write(self, vals):
    #     res = super().write(vals)
    #     if 'driver_id' in vals:
    #         self._create_driver_assignment(force=True)
    #     return res

    # def _create_driver_assignment(self, force=False):
    #     now = fields.Datetime.now()
    #     for vehicle in self:
    #         if vehicle.driver_id:
    #             open_assignments = vehicle.driver_assignment_ids.filtered(lambda a: not a.end_date)
    #             open_assignments.write({'end_date': now})

    #             self.env['fleet.driver.assignment'].create({
    #                 'vehicle_id': vehicle.id,
    #                 'driver_id': vehicle.driver_id.id,
    #                 'start_date': now,
    #             })


class HighwayTollTag(models.Model):
    _name = 'highway.toll.tag'

    name = fields.Char(string='Name')


class Fleet_VehicleLogContract(models.Model):
    _inherit = 'fleet.vehicle.log.contract'

    fine_count = fields.Integer(string='Fine Count', compute='_compute_fine_count')

    def _compute_fine_count(self):
        for record in self:
            record.fine_count = self.env['fleet.fine'].search_count([('vehicle_id', '=', record.vehicle_id.id)])

    def action_view_fines(self):
        return {
            'name': 'Fines',
            'type': 'ir.actions.act_window',
            'res_model': 'fleet.fine',
            'view_mode': 'tree,form',
            'domain': [('vehicle_id', '=', self.vehicle_id.id)],
            'context': {'default_vehicle_id': self.vehicle_id.id, 'search_default_groupby_driver': 1},
        }