# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import http,_
from odoo.http import request
from datetime import datetime
from odoo.addons.stock_barcode.controllers.stock_barcode import StockBarcodeController


class StockApiController(StockBarcodeController):

	@http.route()
	def main_menu(self, barcode, **kw):
		ret_open_hr_employee = self.try_open_hr_employee(barcode)
		if ret_open_hr_employee:
			return ret_open_hr_employee
		return super().main_menu(barcode)

	def try_open_hr_employee(self, barcode):

		hr_employee = request.env['hr.employee'].search([
			('barcode', '=', barcode),
		], limit=1)

		if hr_employee:
			request.session['employee_id'] = hr_employee.id
			fields_to_read = ['id', 'name', 'barcode',]  # Add the fields you want to read
			action = {'model': 'hr.employee' ,'hr_employee': hr_employee.read(fields_to_read)}
			# return {'warning': _('Employee Loging %(employee)s') % {'employee': hr_employee.name}}
			return action


		stock_picking = request.env['stock.picking'].search([
			('name', '=', barcode),
		], limit=1)
		if stock_picking:
			if 'employee_id' in request.session:
				request.session['picking_id'] = stock_picking.id
				picking_record = request.env['stock.picking'].browse(request.session['picking_id'])
				tracking_ids = picking_record.time_tracking_ids
				next_serial_number = len(stock_picking.time_tracking_ids) + 1
				existing_time_tracking = tracking_ids.filtered(lambda r: r.picking_id == stock_picking)
				if not existing_time_tracking and 'employee_id' in request.session:
					new_time_tracking = request.env['time.tracking'].create({
						's_no': next_serial_number,
						'employee_id': request.session['employee_id'],
						'picking_id': stock_picking.id,
						'start_time': datetime.now()
					})

					stock_picking.write({
						'time_tracking_ids': [(4, new_time_tracking.id)]
					})
			else:
				return {'warning': _('Please scan the Employee Barcode first')}
				
		return False