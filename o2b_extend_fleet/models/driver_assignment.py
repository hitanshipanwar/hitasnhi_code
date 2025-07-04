# -*- coding: utf-8 -*-
from odoo import models, fields, api
from datetime import date, datetime

class FleetDriverAssignment(models.Model):
    _name = 'fleet.driver.assignment'
    _description = 'Temporary Driver Assignment'
    _order = "start_date desc"

    vehicle_id = fields.Many2one('fleet.vehicle', required=True, ondelete='cascade')
    driver_id = fields.Many2one('res.partner', string="Driver")
    start_date = fields.Datetime(required=True)
    end_date = fields.Datetime()
    active = fields.Boolean(default=True)