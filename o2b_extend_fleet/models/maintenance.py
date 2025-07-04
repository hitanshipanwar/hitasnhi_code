# -*- coding: utf-8 -*-
from odoo import fields, models
from datetime import date, datetime, timedelta

class VehicleMaintenance(models.Model):
    _inherit = 'maintenance.request'

    next_scheduled_maintenance_date = fields.Date(string="Next Scheduled Maintenance")
    expected_mileage = fields.Integer(string="Expected Mileage at Maintenance")

    def _send_maintenance_reminders(self):
        today = date.today()
        upcoming_date = today - timedelta(days=7)
        template = self.env.ref('o2b_extend_fleet.mail_template_maintenance_reminder')

        records = self.search([
            ('next_scheduled_maintenance_date', '=', upcoming_date)
        ])
        for rec in records:
            if template:
                template.send_mail(rec.id, force_send=True)