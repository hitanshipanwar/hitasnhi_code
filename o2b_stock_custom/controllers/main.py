# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import http,_
from odoo.http import request
from datetime import datetime
from odoo.addons.stock_barcode.controllers.stock_barcode import StockBarcodeController
from odoo.exceptions import AccessDenied, UserError
import psycopg2
import time
import logging
_logger = logging.getLogger(__name__)


class MrpProductionController(StockBarcodeController):

	@http.route('/stock_barcode/scan_from_main_menu', type='json', auth='user')
	def main_menu(self, barcode, **kw):
		""" Receive a barcode scanned from the main menu and return the appropriate
			action (open an existing / new picking) or warning.
		"""
		_logger.info("scan_from_main_menu barcode >> %s" % (barcode))
		ret_open_picking = self._try_open_picking(barcode)
		if ret_open_picking:
			return ret_open_picking

		ret_open_picking_type = self._try_open_picking_type(barcode)
		if ret_open_picking_type:
			return ret_open_picking_type

		if request.env.user.has_group('stock.group_stock_multi_locations'):
			ret_new_internal_picking = self._try_new_internal_picking(barcode)
			if ret_new_internal_picking:
				return ret_new_internal_picking

		if 'aisle_id' not in request.session:
			ret_open_product_location = self._try_open_product_location(barcode)
			if ret_open_product_location:
				return ret_open_product_location

		ret_open_aisle_employee = self.try_open_mrp_barcode(barcode)
		if ret_open_aisle_employee:
			return ret_open_aisle_employee

		# ret_open_to_create_aisle_barcode = self.try_open_create_aisle_barcode(barcode)
		# if ret_open_to_create_aisle_barcode:
		# 	return ret_open_to_create_aisle_barcode

		# ret_open_to_update_aisle_barcode = self.try_open_update_aisle_barcode(barcode)
		# if ret_open_to_update_aisle_barcode:
		# 	return ret_open_to_update_aisle_barcode

		company_id = request.env.company.id
		aisle_barcode = request.env['stock.aisle'].search([('barcode', '=', barcode), ('company_id', '=', company_id)], limit=1)
		if aisle_barcode:
			request.session['aisle_id'] = aisle_barcode.id
			action = {'model': 'stock.aisle'}
			return action

		product_barcode = request.env['product.product'].search([('barcode', '=', barcode)], limit=1)
		if 'aisle_id' in request.session:
			if request.session['aisle_id'] and product_barcode:
				request.session['product_id'] = product_barcode.id
				record = request.env['aisle.location'].search([('aisle_id', '=', request.session['aisle_id']), ('product_id', '=', request.session['product_id'])])
				if not record:
					product_barcode.create_aisle_location(request.session['product_id'], request.session['aisle_id'])
					product_barcode.update_aisle(product_barcode)
					action = {'model': 'product.product'}
					request.session.pop('aisle_id', None)
					request.session.pop('product_id', None)
					return action
				else:
					request.session.pop('aisle_id', None)
					request.session.pop('product_id', None)
					return {'warning': _('Duplicate records are not allowed')}

		if barcode == 'O-BTN.empty' and request.session['aisle_id']:
			aisle_barcode = request.env['stock.aisle'].search([('id', '=', request.session['aisle_id'])])
			record = request.env['aisle.location'].search([('aisle_id', '=', request.session['aisle_id'])])
			if record:
				aisle_barcode.free_aisle_location(request.session['aisle_id'])
				request.session.pop('aisle_id', None)
				request.session.pop('product_id', None)
				return barcode
			else:
				barcode = False
				request.session.pop('aisle_id', None)
				request.session.pop('product_id', None)
				return {'warning': _('Aisle location is already emptied')}

		if barcode == 'O-BTN.confirm':
			return {'success': _('Aisle Created')}

		if barcode == 'O-BTN.edit':
			return {'success': _('Aisle Updated')}

		if request.env.user.has_group('stock.group_stock_multi_locations'):
			return {'warning': _('No picking or location or product corresponding to barcode %(barcode)s') % {'barcode': barcode}}
		else:
			return {'warning': _('No picking or product corresponding to barcode %(barcode)s') % {'barcode': barcode}}

	# # @http.route('/stock_barcode/scan_from_main_menu', type='json', auth='user')
	# # def main_menu(self, barcode, **kw):

	# # 	ret_open_aisle_employee = self.try_open_mrp_barcode(barcode)
	# # 	if ret_open_aisle_employee:
	# # 		return ret_open_aisle_employee

	# # 	ret_open_to_create_aisle_barcode = self.try_open_create_aisle_barcode(barcode)
	# # 	if ret_open_to_create_aisle_barcode:
	# # 		return ret_open_to_create_aisle_barcode

	# # 	ret_open_to_update_aisle_barcode = self.try_open_update_aisle_barcode(barcode)
	# # 	if ret_open_to_update_aisle_barcode:
	# # 		return ret_open_to_update_aisle_barcode

	# # 	return super().main_menu(barcode)

	# def try_open_create_aisle_barcode(self, barcode):
	# 	if not 'O-BTN.update' in barcode:
	# 		if 'O-BTN.create' in barcode:
	# 			request.session['barcode'] = barcode
	# 			update_stock_aisle_id = request.env['update.stock.aisle'].create({})
	# 			action = update_stock_aisle_id.action_client_action()
	# 			request.session['last_record_id'] = update_stock_aisle_id.id
	# 			aisle_record = request.env['edit.stock.aisle'].search([('id', '=', request.session['last_record_id'])])
	# 			aisle_record.barcode = request.session['barcode']
	# 			return {'action': action}

	# 		aisle_record = request.env['edit.stock.aisle'].search([('id', '=', request.session['last_record_id'])])

	# 		if request.session['barcode'] == 'O-BTN.create':

	# 			if 'O-BTN.confirm' in barcode:
	# 				record = request.env['update.stock.aisle'].browse(request.session['last_record_id'])
	# 				record.action_confirm()


	# 			product_rec = request.env['product.product'].search([('barcode', '=', barcode)], limit=1)
	# 			if product_rec and 'last_record_id' in request.session:
	# 				aisle_record = request.env['update.stock.aisle'].search([('id', '=', request.session['last_record_id'])])
	# 				if aisle_record:
	# 					search_edit_aisle_ids = aisle_record.update_asile_line_ids.filtered(lambda line: line.product_id and line.product_id.id == product_rec.id)
	# 					print("aisle_record---",aisle_record)
	# 					print("search_edit_aisle_ids---",search_edit_aisle_ids)
	# 					if not search_edit_aisle_ids:
	# 						aisle_record.update_asile_line_ids.create({
	# 							'product_id': product_rec.id,
	# 							'line_id': aisle_record.id,
	# 						})
	# 						action_rec = aisle_record.action_client_action()
	# 						action = {'action': action_rec, 'model': 'product.product'}
	# 						return action

	# 			aisle_rec = request.env['stock.aisle'].search([('barcode', '=', barcode)], limit=1)
	# 			if aisle_rec and 'last_record_id' in request.session:
	# 				aisle_record = request.env['update.stock.aisle'].search([('id', '=', request.session['last_record_id'])])
	# 				if aisle_record:
	# 					search_edit_product_aisle_ids = aisle_record.update_asile_line_ids.filtered(lambda line: line.product_id and not line.aisle_id)
	# 					if search_edit_product_aisle_ids:
	# 						search_edit_product_aisle_ids.write({'aisle_id': aisle_rec.id})
	# 						action_rec = aisle_record.action_client_action()
	# 						action = {'action': action_rec, 'model': 'stock.aisle'}
	# 						return action

	# def try_open_update_aisle_barcode(self, barcode):
	# 	if not 'O-BTN.create' in barcode:
	# 		if 'O-BTN.update' in barcode:
	# 			request.session['barcode'] = barcode
	# 			request.session['last_record_id'] = False
	# 			edit_stock_aisle_id = request.env['edit.stock.aisle'].create({})
	# 			edit_stock_aisle_id.barcode = request.session['barcode']
	# 			action = edit_stock_aisle_id.action_edit_aisle_client_action()
	# 			request.session['last_record_id'] = edit_stock_aisle_id.id
	# 			return {'action': action}
	# 		_logger.warning("session barcode >> %s" % (request.session['barcode']))
	# 		if request.session['barcode'] == 'O-BTN.update':
	# 			if 'O-BTN.edit' in barcode:
	# 					request.session['barcode'] = False
	# 					record = request.env['edit.stock.aisle'].browse(request.session['last_record_id'])
	# 					record.action_edit_confirm()
	# 					request.session['last_record_id'] = False

	# 			product_rec = request.env['product.product'].sudo().search([('barcode', '=', barcode)], limit=1)
	# 			if product_rec and 'last_record_id' in request.session:
	# 				aisle_record = request.env['edit.stock.aisle'].sudo().search([('id', '=', request.session['last_record_id'])])
	# 				if aisle_record:
	# 					search_edit_aisle_ids = aisle_record.edit_aisle_ids.filtered(lambda line: line.product_id and line.product_id.id == product_rec.id)
	# 					print("aisle_record---",aisle_record)
	# 					print("search_edit_aisle_ids---",search_edit_aisle_ids)
	# 					if not search_edit_aisle_ids:
	# 						aisle_record.edit_aisle_ids.create({
	# 							'product_id': product_rec.id,
	# 							'line_id': aisle_record.id,
	# 						})
	# 						action_rec = aisle_record.action_edit_aisle_client_action()
	# 						action = {'action': action_rec, 'model': 'product.product'}
	# 						return action
	# 			aisle_rec = request.env['stock.aisle'].sudo().search([('barcode', '=', barcode)], limit=1)
	# 			_logger.warning("aisle_rec >> %s" % (str(aisle_rec)))
	# 			if aisle_rec and 'last_record_id' in request.session:
	# 				aisle_record = request.env['edit.stock.aisle'].sudo().search([('id', '=', request.session['last_record_id'])])
	# 				if aisle_record:
	# 					search_src_edit_aisle_ids = aisle_record.edit_aisle_ids.filtered(lambda line: line.product_id and not line.source_aisle_id and not line.destination_aisle_id)
	# 					search_dest_edit_aisle_ids = aisle_record.edit_aisle_ids.filtered(lambda line: line.product_id and line.source_aisle_id and not line.destination_aisle_id)
	# 					if search_src_edit_aisle_ids and not search_dest_edit_aisle_ids:
	# 						search_src_edit_aisle_ids.write({'source_aisle_id': aisle_rec.id})
	# 						aisle_rec = False
	# 						action_rec = aisle_record.action_edit_aisle_client_action()
	# 						action = {'action': action_rec, 'model': 'stock.aisle'}
	# 						return action
	# 					elif not search_src_edit_aisle_ids and search_dest_edit_aisle_ids:
	# 						search_dest_edit_aisle_ids.write({'destination_aisle_id': aisle_rec.id})
	# 						aisle_rec = False
	# 						action_rec = aisle_record.action_edit_aisle_client_action()
	# 						action = {'action': action_rec, 'model': 'stock.aisle'}
	# 						return action
	# 				action_rec = aisle_record.action_edit_aisle_client_action()
	# 				action = {'action': action_rec, 'model': 'stock.aisle'}
	# 				return action
	# 			else:
	# 				return {'warning': _('No aisle or product corresponding to barcode %(barcode)s') % {'barcode': barcode}}

	def try_open_mrp_barcode(self, barcode):

		mrp_production = request.env['mrp.production'].search([('barcode', '=', barcode)], limit=1)

		if mrp_production:
			request.session['mrp_production_id'] = mrp_production.id
			fields_to_read = ['id', 'state', 'barcode',]
			action_rec = mrp_production.action_client_action()
			action = {'action': action_rec ,'mrp_production': mrp_production.read(fields_to_read)}
			return action

		if 'checkin' in barcode:
			return self.handle_checkin(barcode)
		elif 'checkout' in barcode:
			return self.handle_checkout(barcode)
		# elif 'O-BTN.validate' in barcode:
		#     return self.mrp_validate(barcode)

		return False

	def handle_checkin(self, barcode):
		mo_record = request.env['mrp.production'].search([('id','=', request.session['mrp_production_id'])])
		if mo_record.state != 'done':
			if 'employee_id' in request.session:
				time_tracking = request.env['mrp.production.checkin.checkout'].search([
					('employee_id', '=', request.session['employee_id']),
					('production_id', '=', request.session['mrp_production_id']),
					('checkin_time', '!=', False),
					('checkout_time', '=', False)
				], limit=1)
				if time_tracking:
					return {'warning': _('User already checked in with barcode %(barcode)s') % {'barcode': barcode}}
				else:
					tracking_ids = mo_record.checkin_checkout_ids
					existing_time_tracking = tracking_ids.filtered(lambda r: r.production_id.id == request.session['mrp_production_id'] and r.employee_id.id == request.session['employee_id'] and r.checkout_time is False)
					if not existing_time_tracking:
						tracking_time = request.env['mrp.production.checkin.checkout'].create({
							'employee_id': request.session['employee_id'],
							'production_id': request.session['mrp_production_id'],
							'checkin_time': datetime.now()
						})
						action = tracking_time.action_client_action()
						return {'action': action}
						# return {'warning': "Checkin"}
						# return {'success': _('Checked in successfully with barcode %(barcode)s') % {'barcode': barcode}}
			else:
				return {'warning': _('Please scan the Employee Barcode first')}
				# return {'warning': _('Select Employee first')}


	def handle_checkout(self, barcode):
		if 'employee_id' in request.session:
			time_tracking = request.env['mrp.production.checkin.checkout'].search([
				('employee_id', '=', request.session['employee_id']),
				('production_id', '=', request.session['mrp_production_id']),
				('checkin_time', '!=', False),
				('checkout_time', '=', False)
			], limit=1)

			if time_tracking:
				end_time = datetime.now()
				time_difference = end_time - time_tracking.checkin_time
				total_seconds = time_difference.total_seconds()
				hours, remainder = divmod(total_seconds, 3600)
				minutes, seconds = divmod(remainder, 60)
				time_tracking.write({'checkout_time': datetime.now(),
									'time_taken': '{:02}:{:02}:{:02}'.format(int(hours), int(minutes), int(seconds))})
				action = time_tracking.action_client_action()
				return {'action': action}
				# return {'warning': "Checkout"}
				# return {'success': _('Checked out successfully with barcode %(barcode)s') % {'barcode': barcode}}
			else:
				return {'warning': _('Need to check in first with barcode %(barcode)s') % {'barcode': barcode}}
		else:
			return {'warning': _('Select Employee first')}


	def mrp_validate(self, barcode):
		if 'mrp_production_id' in request.session:
			mrp_production = request.env['mrp.production'].browse(request.session['mrp_production_id'])
			print('------',mrp_production)
			# mrp_production.sudo().with_context(skip_immediate=True).button_mark_done()
			action = mrp_production._action_generate_immediate_wizard()
			return {'action': action}


			# return {'warning': _('MO validate')}
		# return False