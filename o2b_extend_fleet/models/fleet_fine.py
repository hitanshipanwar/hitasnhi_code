# -*- coding: utf-8 -*-
from odoo import models, fields, api
from datetime import date, datetime

class FleetFine(models.Model):
    _name = 'fleet.fine'
    _description = 'Vehicle Fine'
    _rec_name = "vehicle_id"

    vehicle_id = fields.Many2one('fleet.vehicle', string='Vehicle', readonly=True)
    driver_id = fields.Many2one('res.partner', string='Driver')
    fine_date = fields.Date(string='Fine Date', required=True, default=fields.Date.context_today)
    fine_type = fields.Many2many(
        'fine.type', 
        'fine_type_rel',
        'fleet_id', 'fine_id', 
        string='Fine Type',
        required=True
    )
    attachment = fields.Binary(string='Attachments')
    file_name = fields.Char("File Name")
    description = fields.Text(string='Comments/Description')


    @api.model
    def create(self, vals):
        if 'vehicle_id' in vals:
            vehicle = self.env['fleet.vehicle'].browse(vals['vehicle_id'])
            vals['driver_id'] = vehicle.driver_id.id
        return super(FleetFine, self).create(vals)

    
    def write(self, vals):
        if 'vehicle_id' in vals:
            vehicle = self.env['fleet.vehicle'].browse(vals['vehicle_id'])
            vals['driver_id'] = vehicle.driver_id.id
        return super(FleetFine, self).write(vals)

    @api.onchange('vehicle_id')
    def _onchange_vehicle_id(self):
        if self.vehicle_id:
            self.driver_id = self.vehicle_id.driver_id


class FineType(models.Model):
    _name = 'fine.type'

    name = fields.Char(string='Name')