# -*- coding: utf-8 -*-
##########################################################################
# Author      : O2b Technologies Pvt. Ltd.(<www.o2btechnologies.com>)
# Copyright(c): 2016-Present O2b Technologies Pvt. Ltd.
# All Rights Reserved.
#
# This program is copyright property of the author mentioned above.
# You can`t redistribute it and/or modify it.
#
##########################################################################
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    checkin_checkout_ids = fields.One2many('mrp.production.checkin.checkout', 'production_id',
                                           string="Check-in/Check-out Log")
    barcode_image = fields.Binary(string="Barcode Image")
    barcode_checkin_text = fields.Char(string="Barcode checkin",copy=False)
    barcode_checkout_text = fields.Char(string="Barcode checkout",copy=False)
    barcode_validate = fields.Char(string="Barcode checkout",copy=False)
    barcode = fields.Char(string="Barcode" ,copy=False)
    total_time_taken = fields.Char(string="Total Time Taken", compute="_compute_total_time_taken")

    def button_mark_done(self):
        for rec in self:
            if not rec.checkin_checkout_ids and rec.company_id.show_mo_validation == True:
                raise ValidationError(_("Without Time Tracking Manufacturing Order can't be executed."))

        res = super(MrpProduction, self).button_mark_done()
        return res

    @api.model
    def button_barcode_order(self):
        for record in self:
            record.barcode = record.id
            if record.name:
                record.barcode_checkin_text = 'checkin'
            if record.name:
                record.barcode_checkout_text = 'checkout'

    @api.model
    def create(self, vals_list):
        res = super(MrpProduction, self).create(vals_list)
        for record in res:
            record.barcode = record.id
            if record.name:
                record.barcode_checkin_text = 'checkin'
            if record.name:
                record.barcode_checkout_text = 'checkout'
        return res

    def action_confirm(self):
        res = super(MrpProduction, self).action_confirm()
        for record in self:
            record.barcode = record.id
            if record.name:
                record.barcode_checkin_text = 'checkin'
                # record.barcode_checkin_text = str(record.id) + '-checkin'
            if record.name:
                record.barcode_checkout_text = 'checkout'
                # record.barcode_checkout_text = str(record.id) + '-checkout'
            # if record.name:
            #     record.barcode_checkout_text = str(record.id) + '-validate'

        return res

    def action_client_action(self):
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'mrp.production',
            'views': [[self.env.ref('o2b_stock_custom.view_mrp_production_barcode').id, 'form']],
            'res_id': self.id,
            'target': 'new',
        }
        # """ Open the mobile view specialized in handling barcodes on mobile devices. """
        # action = self.env['ir.actions.act_window']._for_xml_id('o2b_stock_custom.mrp_production_tree_action')
        # # action = self.env['ir.actions.actions']._for_xml_id('o2b_stock_custom.mrp_production_tree_action')
        # return action

    @api.depends('checkin_checkout_ids.time_taken')
    def _compute_total_time_taken(self):
        for rec in self:
            total_seconds = 0
            for line in rec.checkin_checkout_ids:
                if line.time_taken:
                    time_parts = line.time_taken.split(':')
                    hours, minutes, seconds = map(int, time_parts)
                    total_seconds += hours * 3600 + minutes * 60 + seconds

            total_hours, remainder = divmod(total_seconds, 3600)
            total_minutes, total_seconds = divmod(remainder, 60)
            
            total_time = '{:02}:{:02}:{:02}'.format(int(total_hours), int(total_minutes), int(total_seconds))

            rec.total_time_taken = total_time


class MrpProductionCheckinCheckout(models.Model):
    _name = 'mrp.production.checkin.checkout'
    _description = 'MRP Production Check-in/Check-out Log'

    checkin_time = fields.Datetime(string="Check-in Time")
    checkout_time = fields.Datetime(string="Check-out Time")
    employee_id = fields.Many2one('hr.employee')
    production_id = fields.Many2one('mrp.production', string="Production Order", required=True)
    time_taken = fields.Char(string="Time Taken")

    def action_client_action(self):
        print('-0----',self)
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'mrp.production.checkin.checkout',
            'views': [[self.env.ref('o2b_stock_custom.view_mrp_production_time_tracking_form_inherited').id, 'form']],
            'res_id': self.id,
            'target': 'new',
        }
