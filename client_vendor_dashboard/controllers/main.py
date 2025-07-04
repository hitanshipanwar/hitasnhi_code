# -*- coding: utf-8 -*-
from odoo import http, fields, _
from odoo.http import request
from datetime import datetime, date, time
from bs4 import BeautifulSoup
from dateutil.relativedelta import relativedelta
from odoo.exceptions import ValidationError, UserError, AccessError
from werkzeug.wrappers import Response
import json
import requests
from twilio.rest import Client
import logging
import random
from odoo.service import db, security
import werkzeug
import werkzeug.utils
from werkzeug.utils import redirect
import contextlib
from hashlib import sha256
import passlib.context
import re
from odoo.exceptions import AccessDenied
from dateutil.relativedelta import relativedelta
import mimetypes
_logger = logging.getLogger(__name__)
import base64
try:
	from base64 import encodebytes
except ImportError:
	from base64 import encodestring as encodebytes

import io 
import pytesseract
from pdf2image import convert_from_bytes
from PyPDF2 import PdfFileReader
import textract
import os
import requests
import tempfile

class ClientVendorDashboard(http.Controller):


	@http.route('/vendor/login', auth='public', website=True)
	def dashboard_login(self, **kw):
		_logger.info("===============/vendor/login calling=========== : %s" % kw)
		message = kw.get('usererror')
		_logger.info('--: %s' % message)
		base_url = request.env['ir.config_parameter'].sudo().get_param('client_subscription.host_db_url')
		response = werkzeug.utils.redirect(f'{base_url}/vendor/login')
		response.set_cookie('session_id', '', expires=0)
		response.set_cookie('csrf_token', '', expires=0)
		response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
		response.headers['Pragma'] = 'no-cache'
		response.headers['Expires'] = '0'
		logo_url = request.env['ir.config_parameter'].sudo().get_param('client_subscription.db_logo')
		_logger.info("===========else calling==================: %s" % logo_url)
		response = http.request.render('client_vendor_dashboard.dashboard_login', {'logo_url': logo_url})
		response.headers['Cache-Control'] = 'no-store, must-revalidate'
		response.headers['Pragma'] = 'no-cache'
		response.headers['Expires'] = '0'
		return response
		
		
	# @http.route('/vendor/login/email', type='http', website=True ,methods=['POST'], csrf=False ,auth="public")
	@http.route('/vendor/login/email', type='http', website=True , csrf=False ,auth="public")
	def login_via_email(self, redirect=None, **kw):
		can_login = False
		_logger.info("===========we are in /vendor/login/email ========", kw)
		login_via_opt = kw.get('login_with_otp')
		login_via_email = kw.get('login_with_usermail')
		logo_url = request.env['ir.config_parameter'].sudo().get_param('client_subscription.db_logo')
		host_db_url = request.env['ir.config_parameter'].sudo().get_param('client_subscription.host_db_url')
		my_db_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
		_logger.info("loign via opt: %s and login_via_opt : %s ",login_via_opt,login_via_email)
		if login_via_email and login_via_email=='YES':  
			user_email = kw.get('email')
			user_password = kw.get('password')
			_logger.info("user_email: %s user_password : %s ",user_email,user_password)
			if user_email:
				api_url = f"{host_db_url}/api/db/subscription/state"
				data = {'url': my_db_url}
				headers = {'Content-Type': 'application/json'}
				_logger.info("=========================== data: %s " % data)
				try:
					response = requests.post(api_url, json=data, headers=headers, verify=False)
					response.raise_for_status()  # Raise an exception for HTTP errors
					response_data = response.json()
					_logger.info("Subscription API Response: %s", response_data)
				except requests.RequestException as e:
					_logger.error("Failed to call subscription API: %s", e)
					raise ValidationError("Could not verify subscription status. Please try again later.")

				# if 'result' in response_data and response_data['result'].get('status') == 'success':
				if response_data and response_data.get('status') == 'success':
					if response_data.get('state') == 'active':
					# if response_data['result'].get('state') == 'active':
						can_login = True
				else:
					raise ValidationError("Invalid response from subscription API.")
			if can_login:
				login_user = request.env['res.users'].sudo().search([('login','=',user_email)])
				login_user_count = request.env['res.users'].sudo().search_count([('login','=',user_email)])
				if login_user_count and login_user_count == 1:
					if login_user.has_group('base.group_portal') and not login_user.has_group('base.group_public') and not login_user.has_group('base.group_user'):
						login_success = True
						request.session['loginstatus'] = login_success
						try:
							credential = {'login': user_email, 'password': user_password, 'type': 'password'}
							uid = request.session.authenticate(request.env.cr.dbname, credential)
							# uid = request.session.authenticate(request.env.cr.dbname, user_email, user_password)
						except AccessDenied:
							request.session['wrongEmail'] = False
							request.session['wrongCode'] = True
							return http.request.render('client_vendor_dashboard.dashboard_login', {'logo_url': logo_url})
							# alert_script = """
							# <script>
							#     alert("Authentication failed from odoo server due to wrong Password");
							#     window.location.href = '/vendor/login';
							# </script>
							# """
							# return alert_script

							# invalid_cred_msg = 'Authentication failed from odoo server due to wrong Password.'
							# redirect_url = '/vendor/login?usererror={}'.format(invalid_cred_msg)        
							# return request.redirect(redirect_url)

						if uid:
							client_db = request.env.cr.dbname
							base_url = request.env['ir.config_parameter'].sudo().get_param('client_subscription.host_db_url')
							_logger.info ("Login successful. User ID: {}".format(uid))
							login_message = 'You have successfully logged in'        
							request.session['login_message'] = login_message
							return werkzeug.utils.redirect(f'{base_url}/vendor?db={client_db}&partner_id={login_user.partner_id.id}&client_url={my_db_url}')
										 
					else:
						alert_script = """
						<script>
							alert("Only Portal Vendor User can login.Please use different User Email or Password.");
							window.location.href = '/vendor/login';
						</script>
									"""
						return alert_script
				else:
					request.session['wrongCode'] = False
					request.session['wrongEmail'] = True
					return http.request.render('client_vendor_dashboard.dashboard_login', {'logo_url': logo_url})
					# alert_script = """
					# <script>
					#     alert("Invalid User Name Or Password.Try again.");
					#     window.location.href = '/vendor/login';
					# </script>
					# """
					# return alert_script
			else:
				print("============================")
				return http.request.render('client_vendor_dashboard.session_expired_template')
 

	@http.route('/vendor/home', type='json', auth='public', methods=['POST'], csrf=False)
	# @http.route('/vendor/home', type='http', auth='public', csrf=False)
	def dashboard_home(self):
		print("==============================", request.env.user)
		_logger.info("self /vendor/home =====================")
		data = json.loads(request.httprequest.data)
		_logger.info("self /vendor/home =====================: %s" % data)
		base_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
		vendor_id = data.get('partner_id')
		per_page = data.get('per_page')
		page = data.get('page')
		kw = data.get('kw')
		po_search_name = data.get('name')
		search_data = data.get('search_data')
		res_partner = request.env['res.partner'].sudo().search([('id', '=', vendor_id)])
		current_user = request.env['res.users'].sudo().search([('partner_id', '=', res_partner.id)])
		print("========================================", current_user)
		print("========================================", res_partner)
		print("========================================", data.get('login'))
		email = current_user.login
		user_name = current_user.name
		user_image = current_user.image_1920
		company_id = current_user.company_id
		company_address = (
				(company_id.street or "") + ", " + (company_id.street2 or "")
			).strip(", ")
		
		# if current_user.has_group('base.group_portal') and not current_user.has_group('base.group_public') and not current_user.has_group('base.group_user'):
		_logger.info("User is a valid vendor.")
		
		vendor_name = request.env['res.partner'].sudo().search([('id', '=', vendor_id)])
		related_partners = request.env['res.partner'].sudo().search([
			'|', 
			('id', '=', vendor_id),
			'|', 
			('parent_id', '=', vendor_id),
			('id', '=', vendor_name.parent_id.id)
		])
		if vendor_name.child_ids:
			related_partners |= vendor_name.child_ids
		print("vendor_name =================================", vendor_name)
		print("vendor_name =================================", vendor_id)
		purchase_orders = request.env['purchase.order'].sudo().search([('state', '=', 'purchase'),('partner_id', 'in',related_partners.ids),('invoice_status','=','to invoice')])
		purchase_records = []
		for po in purchase_orders:
			purchase_records.append({
				'id': po.id,
				'name': po.name,
				'invoice_status': po.invoice_status,
				'date_approve': po.date_approve.strftime('%m/%d/%Y'),
				'amount_total': po.amount_total,
				'amount_untaxed': po.amount_untaxed,
				'amount_tax': po.amount_tax,
				'partner_name': po.partner_id.name,
				'location': po.partner_id.city,
			})
		print("purchase_records ***************** " , purchase_records)
		invoice_billed = request.env['account.move'].sudo().search(['&',('partner_id','in',related_partners.ids),('payment_state','in',['not_paid']),('state','in',['posted'])])
		unpaid_inv_total_count = request.env['account.move'].sudo().search_count(['&',('partner_id','in',related_partners.ids),('payment_state','in',['not_paid']),('state','in',['posted'])])
		print("total_count =========== " , unpaid_inv_total_count)
		invoice_records_billed = []
		for inv in invoice_billed:
			invoice_records_billed.append({
				'name': inv.name,
				# 'invoice_status': inv.invoice_status,
				# 'date_order': inv.date_order.strftime('%Y-%m-%d'),
				# 'amount_total': inv.amount_total,
				# 'partner_name': inv.partner_id.name,
				# 'location': inv.partner_id.city,
			})
		print("invoice_records_billed ******************* " , invoice_records_billed)
		invoice_paid = request.env['account.move'].sudo().search(['&',('partner_id','in',related_partners.ids),('payment_state','in',['paid','in_payment']),('state','in',['posted'])])
		if per_page and page:
			orders = invoice_paid.sudo().search(['&',('partner_id','in',related_partners.ids),('payment_state','in',['paid']),('state','in',['posted'])], limit=per_page, offset=(page - 1) * per_page)
			invoice_paid = orders

		if kw.get("fillterby") and kw.get("sortby") and kw.get("fillterby") =='BILL' and kw.get("sortby")=='ASC':
			if per_page and page:
				orders = invoice_paid.sudo().search(['&',('partner_id','in',related_partners.ids),('payment_state','in',['paid']),('state','in',['posted'])], limit=per_page, offset=(page - 1) * per_page ,order='name DESC')
				invoice_paid = orders
			else:
				orders = invoice_paid.sudo().search(['&',('partner_id','in',related_partners.ids),('payment_state','in',['paid']),('state','in',['posted'])], order='name DESC')
				invoice_paid = orders
		if kw.get("fillterby") and kw.get("sortby") and kw.get("fillterby") =='BILL' and kw.get("sortby")=='DESC':
			if per_page and page:
				orders = invoice_paid.sudo().search(['&',('partner_id','in',related_partners.ids),('payment_state','in',['paid']),('state','in',['posted'])], limit=per_page, offset=(page - 1) * per_page ,order='name ASC')
				invoice_paid = orders
			else:
				orders = invoice_paid.sudo().search(['&',('partner_id','in',related_partners.ids),('payment_state','in',['paid']),('state','in',['posted'])], order='name ASC')
				invoice_paid = orders
		if kw.get("fillterby") and kw.get("sortby") and kw.get("fillterby") =='INVOICE' and kw.get("sortby")=='ASC':
			if per_page and page:
				orders = invoice_paid.sudo().search(['&',('partner_id','in',related_partners.ids),('payment_state','in',['paid']),('state','in',['posted'])], limit=per_page, offset=(page - 1) * per_page ,order='payment_reference DESC')
				invoice_paid = orders
			else:
				orders = invoice_paid.sudo().search(['&',('partner_id','in',related_partners.ids),('payment_state','in',['paid']),('state','in',['posted'])] ,order='payment_reference DESC')
				invoice_paid = orders
		if kw.get("fillterby") and kw.get("sortby") and kw.get("fillterby") =='INVOICE' and kw.get("sortby")=='DESC':
			if per_page and page:
				orders = invoice_paid.sudo().search(['&',('partner_id','in',related_partners.ids),('payment_state','in',['paid']),('state','in',['posted'])], limit=per_page, offset=(page - 1) * per_page ,order='payment_reference ASC')
				invoice_paid = orders
			else:
				orders = invoice_paid.sudo().search(['&',('partner_id','in',related_partners.ids),('payment_state','in',['paid']),('state','in',['posted'])], order='payment_reference ASC')
				invoice_paid = orders
		if kw.get("fillterby") and kw.get("sortby") and kw.get("fillterby") =='INVDATE' and kw.get("sortby")=='ASC':
			if per_page and page:
				orders = invoice_paid.sudo().search(['&',('partner_id','in',related_partners.ids),('payment_state','in',['paid']),('state','in',['posted'])], limit=per_page, offset=(page - 1) * per_page,order='invoice_date ASC')
				invoice_paid = orders
			else:
				orders = invoice_paid.sudo().search(['&',('partner_id','in',related_partners.ids),('payment_state','in',['paid']),('state','in',['posted'])], order='invoice_date ASC')
				invoice_paid = orders
		if kw.get("fillterby") and kw.get("sortby") and kw.get("fillterby") =='INVDATE' and kw.get("sortby")=='DESC':
			if per_page and page:
				orders = invoice_paid.sudo().search(['&',('partner_id','in',related_partners.ids),('payment_state','in',['paid']),('state','in',['posted'])], limit=per_page, offset=(page - 1) * per_page, order='invoice_date DESC')
				invoice_paid = orders
			else:
				orders = invoice_paid.sudo().search(['&',('partner_id','in',related_partners.ids),('payment_state','in',['paid']),('state','in',['posted'])], order='invoice_date DESC')
				invoice_paid = orders
		if kw.get("fillterby") and kw.get("sortby") and kw.get("fillterby") =='DUEDATE' and kw.get("sortby")=='ASC' :
			if per_page and page:
				orders = invoice_paid.sudo().search(['&',('partner_id','in',related_partners.ids),('payment_state','in',['paid']),('state','in',['posted'])], limit=per_page, offset=(page - 1) * per_page ,order='invoice_date_due ASC')
				invoice_paid = orders
			else:
				orders = invoice_paid.sudo().search(['&',('partner_id','in',related_partners.ids),('payment_state','in',['paid']),('state','in',['posted'])], order='invoice_date_due ASC')
				invoice_paid = orders
		if kw.get("fillterby") and kw.get("sortby") and kw.get("fillterby") =='DUEDATE' and kw.get("sortby")=='DESC' :
			if per_page and page:
				orders = invoice_paid.sudo().search(['&',('partner_id','in',related_partners.ids),('payment_state','in',['paid']),('state','in',['posted'])], limit=per_page, offset=(page - 1) * per_page ,order='invoice_date_due DESC')
				invoice_paid = orders
			else:
				orders = invoice_paid.sudo().search(['&',('partner_id','in',related_partners.ids),('payment_state','in',['paid']),('state','in',['posted'])], order='invoice_date_due DESC')
				invoice_paid = orders
		if kw.get("fillterby") and kw.get("sortby") and kw.get("fillterby") =='TOTAL' and kw.get("sortby")=='ASC':
			if per_page and page:
				orders = invoice_paid.sudo().search(['&',('partner_id','in',related_partners.ids),('payment_state','in',['paid']),('state','in',['posted'])], limit=per_page, offset=(page - 1) * per_page,order='amount_total_signed DESC')
				invoice_paid = orders
			else:
				orders = invoice_paid.sudo().search(['&',('partner_id','in',related_partners.ids),('payment_state','in',['paid']),('state','in',['posted'])], order='amount_total_signed DESC')
				invoice_paid = orders
		if kw.get("fillterby") and kw.get("sortby") and kw.get("fillterby") =='TOTAL' and kw.get("sortby")=='DESC':
			if per_page and page:
				orders = invoice_paid.sudo().search(['&',('partner_id','in',related_partners.ids),('payment_state','in',['paid']),('state','in',['posted'])], limit=per_page, offset=(page - 1) * per_page,order='amount_total_signed ASC')
				invoice_paid = orders
			else:
				orders = invoice_paid.sudo().search(['&',('partner_id','in',related_partners.ids),('payment_state','in',['paid']),('state','in',['posted'])], order='amount_total_signed ASC')
				invoice_paid = orders
		if kw.get("fillterby") and kw.get("sortby") and kw.get("fillterby") =='MONTH' and kw.get("sortby")=='ASC':
			per_page =total_count
			current_date = datetime.now().date()
			start_of_month = date(current_date.year, current_date.month, 1)
			end_of_month = start_of_month + relativedelta(months=1, days=-1)
			current_month_domain = [('invoice_date', '>=', start_of_month), ('invoice_date', '<=', end_of_month)]
			combined_domain = ['&','&', '&', ('partner_id','in',related_partners.ids),('payment_state','in',['paid']),('state','in',['posted'])]
			combined_domain.extend(current_month_domain)
			orders = invoice_paid.sudo().search(combined_domain, limit=per_page, offset=(page - 1) * per_page)
			invoice_paid = orders
		if kw.get("fillterby") and kw.get("sortby") and kw.get("fillterby") =='YEAR' and kw.get("sortby")=='ASC' :
			per_page =total_count
			current_date = datetime.now().date()
			start_of_month = date(current_date.year, current_date.month, 1)
			end_of_month = start_of_month + relativedelta(months=1, days=-1)
			current_year_domain = [('invoice_date', '>=', date(current_date.year, 1, 1)), ('invoice_date', '<=', date(current_date.year, 12, 31))]
			combined_domain = ['&','&', '&', ('partner_id','in',related_partners.ids),('payment_state','in',['paid']),('state','in',['posted'])]
			combined_domain.extend(current_year_domain)
			orders = invoice_paid.sudo().search(combined_domain, limit=per_page, offset=(page - 1) * per_page)
			invoice_paid = orders

		paid_invocie_total_invoice_amount = 0.0
		for data in invoice_paid:
			paid_invocie_total_invoice_amount = paid_invocie_total_invoice_amount + data.amount_total_signed
			print("paid_invocie_total_invoice_amount============ " , paid_invocie_total_invoice_amount)

		paid_inv_total_count = request.env['account.move'].sudo().search_count(['&',('partner_id','in',related_partners.ids),('payment_state','in',['paid''in_payment', ]),('state','in',['posted'])])
		print("total_count =========== " , paid_inv_total_count)
		invoice_records_paid = []
		for inv in invoice_paid:
			invoice_records_paid.append({
				'id': inv.id,
				'name': inv.name,
				'invoice_date': inv.invoice_date.strftime('%m/%d/%Y') if inv.invoice_date else inv.invoice_date,
				'payment_reference': inv.payment_reference,
				'payment_state': inv.payment_state,
				'invoice_date_due': inv.invoice_date_due.strftime('%m/%d/%Y') if inv.invoice_date_due else inv.invoice_date_due,
				'invoice_purchase_order': inv.invoice_purchase_order,
				'amount_total_signed': inv.amount_total_signed,
			})
		print("invoice_records_paid*************** " , invoice_records_paid)
		invoice_order = request.env['account.move'].sudo().search(['&',('partner_id','in',related_partners.ids),('payment_state','in',['not_paid']),('state','in',['posted'])])
		invoice_records = []
		for inv in invoice_order:
			invoice_records.append({
				'id': inv.id,
				'name': inv.name,
				'invoice_date': inv.invoice_date.strftime('%m/%d/%Y') if inv.invoice_date else inv.invoice_date,
				'payment_reference': inv.payment_reference,
				'payment_state': inv.payment_state,
				'invoice_date_due': inv.invoice_date_due.strftime('%m/%d/%Y') if inv.invoice_date_due else inv.invoice_date_due,
				'invoice_purchase_order': inv.invoice_purchase_order,
				'amount_total_signed': inv.amount_total_signed,
			})
		print("invoice_records ************** " ,invoice_records)
		po_records = purchase_orders.sudo().search([('state', '=', 'purchase'),('partner_id', 'in',related_partners.ids),('invoice_status', '=', 'to invoice')],order='name ASC')
		if per_page and page:
			orders = po_records.sudo().search(['&',('partner_id', 'in',related_partners.ids),('invoice_status', '=', 'to invoice'),('state', '=', 'purchase')], limit=per_page, offset=(page - 1) * per_page)
			po_records = orders

		if kw.get("fillterby") and kw.get("sortby") and kw.get("fillterby") =='PO' and kw.get("sortby")=='ASC' :
			if per_page and page:
				po_records = purchase_orders.sudo().search([('state', '=', 'purchase'),('partner_id', 'in',related_partners.ids),('invoice_status', '=', 'to invoice')],limit=per_page, offset=(page - 1) * per_page, order='name DESC')
			else:
				po_records = purchase_orders.sudo().search([('state', '=', 'purchase'),('partner_id', 'in',related_partners.ids),('invoice_status', '=', 'to invoice')], order='name DESC')
			print("1.po_records ********************* " , po_records)
		if kw.get("fillterby") and kw.get("sortby") and kw.get("fillterby") =='PO' and kw.get("sortby")=='DESC':
			if per_page and page:
				po_records = purchase_orders.sudo().search([('state', '=', 'purchase'),('partner_id', 'in',related_partners.ids),('invoice_status', '=', 'to invoice')],limit=per_page, offset=(page - 1) * per_page, order='name ASC')
			else:
				po_records = purchase_orders.sudo().search([('state', '=', 'purchase'),('partner_id', 'in',related_partners.ids),('invoice_status', '=', 'to invoice')], order='name ASC')
			print("2.po_records ******************* " ,po_records)

		if kw.get("fillterby") and kw.get("sortby") and kw.get("fillterby") =='AMOUNT' and kw.get("sortby")=='ASC':
			if per_page and page:
				po_records = purchase_orders.sudo().search([('state', '=', 'purchase'),('partner_id', 'in',related_partners.ids),('invoice_status', '=', 'to invoice')],limit=per_page, offset=(page - 1) * per_page, order='amount_total DESC')
			else:
				po_records = purchase_orders.sudo().search([('state', '=', 'purchase'),('partner_id', 'in',related_partners.ids),('invoice_status', '=', 'to invoice')],order='amount_total DESC')
		if kw.get("fillterby") and kw.get("sortby") and kw.get("fillterby") =='AMOUNT' and kw.get("sortby")=='DESC':
			if per_page and page:
				po_records = purchase_orders.sudo().search([('state', '=', 'purchase'),('partner_id', 'in',related_partners.ids),('invoice_status', '=', 'to invoice')],limit=per_page, offset=(page - 1) * per_page, order='amount_total ASC')
			else:
				po_records = purchase_orders.sudo().search([('state', '=', 'purchase'),('partner_id', 'in',related_partners.ids),('invoice_status', '=', 'to invoice')], order='amount_total ASC')
		if kw.get("fillterby") and kw.get("sortby") and kw.get("fillterby") =='MONTH' and kw.get("sortby")=='ASC':
			per_page =total_count
			current_date = datetime.now().date()
			start_of_month = date(current_date.year, current_date.month, 1)
			end_of_month = start_of_month + relativedelta(months=1, days=-1)
			current_month_domain = [('date_approve', '>=', start_of_month), ('date_approve', '<=', end_of_month)]
			# combined_domain = ['&','&', '&', ('vendor_location', '=',vendor_name),('invoice_status','not in',['invoiced','no'])]
			combined_domain = ['&','&', '&', ('partner_id', '=',vendor_name),('invoice_status', '=', 'to invoice'),('state', '=', 'purchase')]
			combined_domain.extend(current_month_domain)
			po_records = PurchaseOrder.sudo().search(combined_domain, limit=per_page, offset=(page - 1) * per_page)
		if kw.get("fillterby") and kw.get("sortby") and kw.get("fillterby") =='YEAR' and kw.get("sortby")=='ASC':
			per_page =total_count
			current_date = datetime.now().date()
			start_of_month = date(current_date.year, current_date.month, 1)
			end_of_month = start_of_month + relativedelta(months=1, days=-1)
			current_year_domain = [('date_approve', '>=', date(current_date.year, 1, 1)), ('date_approve', '<=', date(current_date.year, 12, 31))]
			# combined_domain = ['&','&', '&', ('vendor_location', '=',vendor_name),('invoice_status','not in',['invoiced','no'])]
			combined_domain = ['&','&', '&', ('partner_id', '=',vendor_name),('invoice_status', '=', 'to invoice'),('state', '=', 'purchase')]
			combined_domain.extend(current_year_domain)
			po_records = PurchaseOrder.sudo().search(combined_domain, limit=per_page, offset=(page - 1) * per_page)

		po_orders = []
		for po in po_records:
			po_orders.append({
				'id': po.id,
				'name': po.name,
				'partner_name': po.partner_id.name,
				'invoice_status': po.invoice_status,
				'date_approve': po.date_approve.strftime('%m/%d/%Y'),
				'amount_total': po.amount_total,
				'amount_untaxed': po.amount_untaxed,
				'amount_tax': po.amount_tax,
				'partner_name': po.partner_id.name,
				'location': po.partner_id.city,
				'payment_term_id': po.payment_term_id.name
			})
		total_po_orders = purchase_orders.sudo().search_count([('state', '=', 'purchase'),('partner_id', 'in',related_partners.ids),('invoice_status', '=', 'to invoice')])
		print("total_po_orders *************************", total_po_orders)
		print("po_orders **************** " , po_orders)
		print("po_orders **************** " , po_records)
		invoice_records = invoice_order.sudo().search(['&',('partner_id','in',related_partners.ids),('payment_state','in',['not_paid']),('state','in',['posted'])], order='invoice_date DESC')
		if per_page and page:
			if per_page and page:
				orders = invoice_records.sudo().search(['&',('partner_id','in',related_partners.ids),('payment_state','in',['not_paid']),('state','in',['posted'])], limit=per_page, offset=(page - 1) * per_page)
				invoice_records = orders
			else:
				orders = invoice_records.sudo().search(['&',('partner_id','in',related_partners.ids),('payment_state','in',['not_paid']),('state','in',['posted'])])
				invoice_records = orders
		if kw.get("fillterby") and kw.get("sortby") and kw.get("fillterby") =='BILL' and kw.get("sortby")=='ASC' :
			if per_page and page:
				orders = invoice_records.sudo().search(['&',('partner_id','in',related_partners.ids),('payment_state','in',['not_paid']),('state','in',['posted'])], limit=per_page, offset=(page - 1) * per_page ,order='name DESC')
				invoice_records = orders
			else:
				orders = invoice_records.sudo().search(['&',('partner_id','in',related_partners.ids),('payment_state','in',['not_paid']),('state','in',['posted'])] ,order='name DESC')
				invoice_records = orders
		if kw.get("fillterby") and kw.get("sortby") and kw.get("fillterby") =='BILL' and kw.get("sortby")=='DESC' :
			if per_page and page:
				orders = invoice_records.sudo().search(['&',('partner_id','in',related_partners.ids),('payment_state','in',['not_paid']),('state','in',['posted'])], limit=per_page, offset=(page - 1) * per_page ,order='name ASC')
				invoice_records = orders
			else:
				orders = invoice_records.sudo().search(['&',('partner_id','in',related_partners.ids),('payment_state','in',['not_paid']),('state','in',['posted'])], order='name ASC')
				invoice_records = orders
		if kw.get("fillterby") and kw.get("sortby") and kw.get("fillterby") =='INVOICE' and kw.get("sortby")=='ASC' :
			if per_page and page:
				orders = invoice_records.sudo().search(['&',('partner_id','in',related_partners.ids),('payment_state','in',['not_paid']),('state','in',['posted'])], limit=per_page, offset=(page - 1) * per_page ,order='payment_reference DESC')
				invoice_records = orders
			else:
				orders = invoice_records.sudo().search(['&',('partner_id','in',related_partners.ids),('payment_state','in',['not_paid']),('state','in',['posted'])] ,order='payment_reference DESC')
				invoice_records = orders
		if kw.get("fillterby") and kw.get("sortby") and kw.get("fillterby") =='INVDATE' and kw.get("sortby")=='ASC' :
			if per_page and page:
				orders = invoice_records.sudo().search(['&',('partner_id','in',related_partners.ids),('payment_state','in',['not_paid']),('state','in',['posted'])], limit=per_page, offset=(page - 1) * per_page ,order='invoice_date ASC')
				invoice_records = orders
			else:
				orders = invoice_records.sudo().search(['&',('partner_id','in',related_partners.ids),('payment_state','in',['not_paid']),('state','in',['posted'])], order='invoice_date ASC')
				invoice_records = orders
		if kw.get("fillterby") and kw.get("sortby") and kw.get("fillterby") =='DUEDATE' and kw.get("sortby")=='ASC' :
			if per_page and page:
				orders = invoice_records.sudo().search(['&',('partner_id','in',related_partners.ids),('payment_state','in',['not_paid']),('state','in',['posted'])], limit=per_page, offset=(page - 1) * per_page ,order='invoice_date_due ASC')
				invoice_records = orders
			else:
				orders = invoice_records.sudo().search(['&',('partner_id','in',related_partners.ids),('payment_state','in',['not_paid']),('state','in',['posted'])], order='invoice_date_due ASC')
				invoice_records = orders
		if kw.get("fillterby") and kw.get("sortby") and kw.get("fillterby") =='TOTAL' and kw.get("sortby")=='ASC' :
			if per_page and page:
				orders = invoice_records.sudo().search(['&',('partner_id','in',related_partners.ids),('payment_state','in',['not_paid']),('state','in',['posted'])], limit=per_page, offset=(page - 1) * per_page ,order='amount_total_signed DESC')
				invoice_records = orders
			else:
				orders = invoice_records.sudo().search(['&',('partner_id','in',related_partners.ids),('payment_state','in',['not_paid']),('state','in',['posted'])], order='amount_total_signed DESC')
				invoice_records = orders
		if kw.get("fillterby") and kw.get("sortby") and kw.get("fillterby") =='TOTAL' and kw.get("sortby")=='DESC' :
			if per_page and page:
				orders = invoice_records.sudo().search(['&',('partner_id','in',related_partners.ids),('payment_state','in',['not_paid']),('state','in',['posted'])], limit=per_page, offset=(page - 1) * per_page ,order='amount_total_signed ASC')
				invoice_records = orders
			else:
				orders = invoice_records.sudo().search(['&',('partner_id','in',related_partners.ids),('payment_state','in',['not_paid']),('state','in',['posted'])], order='amount_total_signed ASC')
				invoice_records = orders
		if kw.get("fillterby") and kw.get("sortby") and kw.get("fillterby") =='MONTH' and kw.get("sortby")=='ASC' :
			current_date = datetime.now().date()
			per_page =total_count
			start_of_month = date(current_date.year, current_date.month, 1)
			end_of_month = start_of_month + relativedelta(months=1, days=-1)
			current_month_domain = [('invoice_date', '>=', start_of_month), ('invoice_date', '<=', end_of_month)]
			combined_domain = ['&', '&', ('partner_id','in',related_partners.ids),('payment_state','in',['not_paid']),('state','in',['posted'])]
			combined_domain.extend(current_month_domain)
			orders = invoice_records.sudo().search(combined_domain, limit=per_page, offset=(page - 1) * per_page)
			invoice_records = orders
		if kw.get("fillterby") and kw.get("sortby") and kw.get("fillterby") =='YEAR' and kw.get("sortby")=='ASC':
			per_page =total_count
			current_date = datetime.now().date()
			start_of_month = date(current_date.year, current_date.month, 1)
			end_of_month = start_of_month + relativedelta(months=1, days=-1)
			current_year_domain = [('invoice_date', '>=', date(current_date.year, 1, 1)), ('invoice_date', '<=', date(current_date.year, 12, 31))]
			combined_domain = ['&', '&', ('partner_id','in',related_partners.ids),('payment_state','in',['not_paid']),('state','in',['posted'])]
			combined_domain.extend(current_year_domain)
			orders = invoice_records.sudo().search(combined_domain, limit=per_page, offset=(page - 1) * per_page)
			invoice_records = orders

		total_invoice_amount = 0.0
		total_invoice_amount1 = 0.0
		for data in invoice_records:
			total_invoice_amount1 = total_invoice_amount1 + data.amount_total_signed
		print("total_invoice_amount1 ===============  " , total_invoice_amount1)
		invoice_rec = []
		for inv in invoice_records:
			invoice_rec.append({
				'id': inv.id,
				'name': inv.name,
				'invoice_date': inv.invoice_date.strftime('%m/%d/%Y') if inv.invoice_date else inv.invoice_date,
				'payment_reference': inv.payment_reference,
				'payment_state': inv.payment_state,
				'invoice_date_due': inv.invoice_date_due.strftime('%m/%d/%Y') if inv.invoice_date_due else inv.invoice_date_due,
				'invoice_purchase_order': inv.invoice_purchase_order,
				'amount_total_signed': inv.amount_total_signed,

			})
		print("invoice_rec ******************* " , invoice_rec)

		print("po_orders =====================", po_orders)
		print("po_search_name ***************************", po_search_name)
		search_purchase_records_list = []
		search_purchase_records_new_list = []
		search_invoice_records_billed_list = []
		search_invoice_records_paid_list = []
		search_invoice_records_list = []
		if po_search_name:
			if '/' in po_search_name and not any(char.isalpha() for char in po_search_name):
				print("###################################")
				try:
					print("try *****************************")
					string_date = datetime.strptime(po_search_name, '%m/%d/%Y').date()
					# date = datetime.strftime(string_date, '%Y-%m-%d')
					date = datetime.strftime(string_date, '%m/%d/%Y')
					start_date = datetime.combine(string_date, datetime.min.time())
					end_date = datetime.combine(string_date, datetime.max.time())
					print("start_date ******************************", start_date)
					print("end_date ******************************", end_date)
					# purchase_records = request.env['purchase.order'].search([
					# ('date_approve', '>=', start_date),('date_approve', '<', end_date),('invoice_status','=','to invoice')])
					purchase_records = request.env['purchase.order'].sudo().search([
					('date_approve', '>=', start_date),('date_approve', '<', end_date),('invoice_status', '!=', 'fully_billed')])
					for po in purchase_records:
						search_purchase_records_list.append({
							'id': po.id,
							'name': po.name,
							'partner_name': po.partner_id.name,
							'invoice_status': po.invoice_status,
							'date_approve': po.date_approve.strftime('%Y-%m-%d'),
							'amount_total': po.amount_total,
							'amount_untaxed': po.amount_untaxed,
							'amount_tax': po.amount_tax,
							'partner_name': po.partner_id.name,
							'location': po.partner_id.city,
						})
				except Exception as e:
					print("except *************************")
					purchase_records = []
					pass
			else:
				purchase_records = request.env['purchase.order'].sudo().search(['&',('partner_id', 'in',related_partners.ids),('name', 'ilike', po_search_name),('invoice_status', '!=', 'fully_billed'),('state', '=', 'purchase')])
				for po in purchase_records:
					search_purchase_records_list.append({
						'id': po.id,
						'name': po.name,
						'partner_name': po.partner_id.name,
						'invoice_status': po.invoice_status,
						'date_approve': po.date_approve.strftime('%m/%d/%Y'),
						'amount_total': po.amount_total,
						'amount_untaxed': po.amount_untaxed,
						'amount_tax': po.amount_tax,
						'partner_name': po.partner_id.name,
						'location': po.partner_id.city,
					})
				# purchase_records = request.env['purchase.order'].sudo().search(['&',('vendor_location', 'in',related_partners.ids),('name', '=', name),('invoice_status','=','to invoice')])

			# invoice_records_billed = request.env['account.move'].sudo().search([('customer_location','in',related_partners.ids),('payment_state','in',['not_paid']),'|','|',('name', 'ilike', name),('state','in',['posted','draft']),('payment_reference','ilike', name)])
			# invoice_records_paid = request.env['account.move'].sudo().search([('customer_location','in',related_partners.ids),('payment_state','in',['paid','in_payment']),'|','|',('name', 'ilike', name),('state','in',['posted']),('payment_reference','ilike', name)])
			search_purchase_records_new = request.env['purchase.order'].sudo().search([('state', '=', 'purchase'),('partner_id', 'in',related_partners.ids),('invoice_status', '!=', 'fully_billed')])
			for po in search_purchase_records_new:
				search_purchase_records_new_list.append({
					'id': po.id,
					'name': po.name,
					'partner_name': po.partner_id.name,
					'invoice_status': po.invoice_status,
					'date_approve': po.date_approve.strftime('%m/%d/%Y'),
					'amount_total': po.amount_total,
					'amount_untaxed': po.amount_untaxed,
					'amount_tax': po.amount_tax,
					'partner_name': po.partner_id.name,
					'location': po.partner_id.city,
				})
			search_invoice_records_billed = request.env['account.move'].sudo().search(['&',('partner_id','in',related_partners.ids),('payment_state','in',['not_paid']),('state','in',['posted'])])
			for inv in search_invoice_records_billed:
				search_invoice_records_billed_list.append({
				'id': inv.id,
				'name': inv.name,
				'invoice_date': inv.invoice_date.strftime('%m/%d/%Y') if inv.invoice_date else inv.invoice_date,
				'payment_reference': inv.payment_reference,
				'payment_state': inv.payment_state,
				'invoice_date_due': inv.invoice_date_due.strftime('%m/%d/%Y') if inv.invoice_date_due else inv.invoice_date_due,
				'invoice_purchase_order': inv.invoice_purchase_order,
				'amount_total_signed': inv.amount_total_signed,

			})
			search_invoice_records_paid = request.env['account.move'].sudo().search(['&',('partner_id','in',related_partners.ids),('payment_state','in',['paid','in_payment']),('state','in',['posted'])])
			for inv in search_invoice_records_paid:
				search_invoice_records_paid_list.append({
				'id': inv.id,
				'name': inv.name,
				'invoice_date': inv.invoice_date.strftime('%m/%d/%Y') if inv.invoice_date else inv.invoice_date,
				'payment_reference': inv.payment_reference,
				'invoice_date_due': inv.invoice_date_due.strftime('%m/%d/%Y') if inv.invoice_date_due else inv.invoice_date_due,
				'payment_state': inv.payment_state,
				'invoice_purchase_order': inv.invoice_purchase_order,
				'amount_total_signed': inv.amount_total_signed,

			})
			search_invoice_records = request.env['account.move'].sudo().search([('partner_id','in',related_partners.ids),('state','in',['posted','draft']),'|',('name', 'ilike', po_search_name),('payment_reference','ilike', po_search_name)])
			for inv in search_invoice_records:
				search_invoice_records_list.append({
				'name': inv.name,
				'invoice_date': inv.invoice_date.strftime('%m/%d/%Y') if inv.invoice_date else inv.invoice_date,
				'payment_reference': inv.payment_reference,
				'payment_state': inv.payment_state,
				'invoice_date_due': inv.invoice_date_due.strftime('%m/%d/%Y') if inv.invoice_date_due else inv.invoice_date_due,
				'invoice_purchase_order': inv.invoice_purchase_order,
				'amount_total_signed': inv.amount_total_signed,

			})

		# Unpaid Invoice Search
		unpaidinv_search_invoice_records_billed = []
		invoice_records_billed = request.env['account.move'].sudo().search(['&',('payment_state','in',['not_paid']),'&',('partner_id','in',related_partners.ids),'|','|',('name','ilike',search_data),('invoice_purchase_order','ilike',search_data),('payment_reference','ilike', search_data)])
		unpaid_total_invoice_amount = 0.0
		for data in invoice_records_billed:
			unpaid_total_invoice_amount = unpaid_total_invoice_amount + data.amount_total_signed
		for inv in invoice_records_billed:
				unpaidinv_search_invoice_records_billed.append({
				'id': inv.id,
				'name': inv.name,
				'invoice_date': inv.invoice_date.strftime('%m/%d/%Y') if inv.invoice_date else inv.invoice_date,
				'payment_reference': inv.payment_reference,
				'invoice_date_due': inv.invoice_date_due.strftime('%m/%d/%Y') if inv.invoice_date_due else inv.invoice_date_due,
				'payment_state': inv.payment_state,
				'invoice_purchase_order': inv.invoice_purchase_order,
				'amount_total_signed': inv.amount_total_signed,

			})

		# Paid Invoice Search
		paidinv_search_invoice_records_paid = []
		search_invoice_records_paid = request.env['account.move'].sudo().search(['&',('payment_state','in',['paid']),'&',('partner_id','in',related_partners.ids),'|','|',('name','ilike',search_data),('invoice_purchase_order','ilike',search_data),('payment_reference','ilike',search_data)])
		paidinv_search_total_invoice_amount = 0.0
		for data in search_invoice_records_paid:
			paidinv_search_total_invoice_amount = paidinv_search_total_invoice_amount + data.amount_total_signed
		for inv in search_invoice_records_paid:
			paidinv_search_invoice_records_paid.append({
				'id': inv.id,
				'name': inv.name,
				'invoice_date': inv.invoice_date.strftime('%m/%d/%Y') if inv.invoice_date else inv.invoice_date,
				'payment_reference': inv.payment_reference,
				'invoice_date_due': inv.invoice_date_due.strftime('%m/%d/%Y') if inv.invoice_date_due else inv.invoice_date_due,
				'payment_state': inv.payment_state,
				'invoice_purchase_order': inv.invoice_purchase_order,
				'amount_total_signed': inv.amount_total_signed,

			})
		print("=========================22===paidinv_search_invoice_records_paid", paidinv_search_invoice_records_paid)
			
		print("search_purchase_records_list*****************************************", search_purchase_records_list)
		print("search_purchase_records_new_list*****************************************", search_purchase_records_new_list)
		print("search_invoice_records_billed_list*****************************************", search_invoice_records_billed_list)
		print("search_invoice_records_paid_list*****************************************", search_invoice_records_paid_list)
		print("search_invoice_records_list*****************************************", search_invoice_records_list)
		print("invoice_records_paid*****************************************", invoice_records_paid)

		res = {
			'total_po_orders': total_po_orders,
			'unpaid_inv_total_count': unpaid_inv_total_count,
			'paid_inv_total_count': paid_inv_total_count,
			'billed_invoice': invoice_records_billed,
			'paid_invoice': invoice_records_paid,
			'paid_invocie_total_invoice_amount': paid_invocie_total_invoice_amount,
			'total_invoice_amount': round(total_invoice_amount, 2),
			'purchase_records': po_orders,
			'invoice_records': invoice_rec,
			'unpaid_invoice_total_amount': round(total_invoice_amount1, 2),
			'user': request.env.user,
			'search_purchase_records': search_purchase_records_list,
			'search_purchase_records_new': search_purchase_records_new_list,
			'search_invoice_records_billed': search_invoice_records_billed_list,
			'search_invoice_records_paid': search_invoice_records_paid_list,
			'search_invoice_records': search_invoice_records_list,
			'unpaidinv_search_invoice_records_billed': unpaidinv_search_invoice_records_billed,
			'unpaid_total_invoice_amount': round(unpaid_total_invoice_amount, 2),
			'paidinv_search_invoice_records_paid': paidinv_search_invoice_records_paid,
			'paidinv_search_total_invoice_amount': round(paidinv_search_total_invoice_amount, 2),
			'company_name': company_id.name,
			'company_mobile': company_id.mobile,
			'company_email': company_id.email,
			'company_address': company_address,
			'email': email,
			'partner_id': vendor_id,
			'user_name': user_name,
			# 'user_image': base64.b64encode(user_image or b'').decode('utf-8') if user_image else None,
			'user_image': user_image,
		}

		_logger.info('Response data: %s', res)
		return res

	def return_default_due_date(self, po):
		today = fields.Date.context_today(request.env['purchase.order'])
		if po.payment_term_id and po.payment_term_id.due_date:
			due_date_days = po.payment_term_id.due_date.split('net_')
			return today + relativedelta(days=int(due_date_days[1]))
		else:
			payment_term = request.env['account.payment.term'].sudo().search([('default_payment_term','=',True)])
			print("====payment_term================== " , payment_term)
			due_date_days = payment_term.due_date.split('net_')
			print("=====due_date_days===========" , due_date_days)
			return today + relativedelta(days=int(due_date_days[1]))

	def remove_html_tags(self, text):
		soup = BeautifulSoup(text, "html.parser")
		return soup.get_text()

	@http.route('/api/vendor/create/invoice', type='json', auth='public', methods=['POST'], csrf=False)
	# @http.route('/api/vendor/create/invoice', type='http', auth='public', csrf=False)
	def api_create_payment_method(self):
		print("/api/vendor/create/invoice *****************")
		data = json.loads(request.httprequest.data)
		print("data ****************************", data)
		kw = data.get('kw')
		print("kw ****************************", kw)
		partner_id = data.get('partner_id')
		res_partner = request.env['res.partner'].sudo().search([('id', '=', partner_id)])
		current_user = request.env['res.users'].sudo().search([('partner_id', '=', res_partner.id)])
		print("========================================", current_user)
		print("========================================", res_partner)
		user_name = current_user.name
		user_image = current_user.image_1920
		record_id = data.get('record_id')
		print("record_id ****************************", record_id)
		purchase_status = data.get('purchase_status')
		print("purchase_status ****************************", purchase_status)
		
		payment_term = request.env['account.payment.term'].sudo().search([('default_payment_term','=',True)])
		print("payment_term ****************************", payment_term)

		record = []
		po_record = request.env['purchase.order'].sudo().search(['&',('id','=',record_id),('invoice_status','in',[purchase_status])],limit=1)
		total_amount = 0
		print("po_record *********************", po_record)
		total_amount = po_record.amount_total

		for po in po_record:
			company_address = (
				(po.company_id.street or "") + ", " + (po.company_id.street2 or "")
			).strip(", ")

			order_lines = []
			for line in po.order_line:
				order_lines.append({
					'product_name': line.product_id.name,
					'description': line.name,
					'quantity': line.product_qty,
					'unit_price': line.price_unit,
					'subtotal': line.price_subtotal,
				})

			message_ids = po.message_ids.filtered(lambda r: r.author_id == current_user.partner_id).sudo().sorted(lambda r: r.date, reverse=True)
			# message_ids = po.message_ids.filtered(lambda r: r.author_id == request.env.user.partner_id).sudo().sorted(lambda r: r.date, reverse=True)
			# message_ids = po.message_ids.filtered(lambda r: r.author_id == partner_id).sudo().sorted(lambda r: r.date, reverse=True)
			message_list = []
			for message in message_ids:
				message_list.append({
					'email_from': message.email_from,
					'date': message.date.strftime('%m/%d/%Y') if message.date else datetime.now(),
					'body': self.remove_html_tags(message.body),
				})
			record.append({
				'id': po.id,
				'name': po.name,
				'partner_name': po.partner_id.name,
				'invoice_status': po.invoice_status,
				'date_approve': po.date_approve.strftime('%m/%d/%Y'),
				'amount_total': po.amount_total,
				'amount_untaxed': po.amount_untaxed,
				'amount_tax': po.amount_tax,
				'partner_name': po.partner_id.name,
				'location': po.partner_id.city,
				'payment_term_id': payment_term.name,
				'return_default_due_date': self.return_default_due_date(po),
				'messag_ids': message_list,
				'company_name': po.company_id.name,
				'company_mobile': po.company_id.mobile,
				'company_email': po.company_id.email,
				'company_address': company_address,
				'user_name': user_name,
				'user_image': user_image,
				'partner_id': partner_id,
				'order_lines': order_lines,
			})
		print("*****************************", record)
		request.session['purchase_url'] = request.httprequest.url
		# fetch ship or bill to address
		bill_to_partner_id=None
		ship_to_partner_id=None

		return {'record': record, 'total_amount': total_amount}



	@http.route('/api/submit/payment', type='json', auth='public', methods=['POST'], csrf=False)
	# @http.route('/api/submit/payment', type='http', auth='public', csrf=False)
	def api_create_payment(self):
		print("/api/submit/payment *****************", self)
		data = json.loads(request.httprequest.data)
		print("data ****************************", data)

		partner_id = data.get('partner_id')
		record_id = data.get('record_id')
		model_name = data.get('model_name')
		bill_number = data.get('bill_number')
		total_amount = data.get('total_amount')
		calculated_amount = data.get('calculated_amount')
		total_percentage = data.get('total_percentage')
		selected_total_percentage = data.get('selected_total_percentage')
		due_date = data.get('due_date')
		payment_file_data = data.get('payment_file_data')
		selected_percentage = data.get('selected_percentage')
		payment_attachment_name = data.get('payment_attachment_name')
		payment_attachment_type = data.get('payment_attachment_type')
		payment_term_id = request.env['account.payment.term'].sudo().search([('default_payment_term', '=', True)])
		print("=========================payment_term_id", payment_term_id)
		if isinstance(payment_file_data, str):
			payment_file_data = base64.b64decode(payment_file_data)  # Decode from base64 if it's a string

		res_partner = request.env['res.partner'].sudo().search([('id', '=', partner_id)])
		current_user = request.env['res.users'].sudo().search([('partner_id', '=', res_partner.id)])

		if record_id and model_name and payment_file_data:
			record = request.env[model_name].with_user(2).sudo().search([('id','=',record_id)],limit=1)
			try:
				if payment_file_data:
					index_content = 'application'
					file_record = request.env['ir.attachment'].with_user(current_user.id).sudo().create({
					'name': payment_attachment_name,
					'type': 'binary',
					'datas': base64.b64encode(payment_file_data).decode(),
					'res_model': model_name,
					'res_id': record_id,
					'mimetype': payment_attachment_type,
					'index_content': index_content,
					})
			except Exception as e:
				_logger.error(f"Error creating ir.attachment record: {e}")
				pass
			# End here

			success_status = 0
			message = ''
			bill_id = ''
			try:
				# call create bill method
				# if payment_file_data and record.invoice_status not in ['no','invoiced'] or record.state not in ['purchase','done']:
				if payment_file_data and record:
					_logger.info("call create bill method of purchase order while action_create_invoice(): ")
					bill = record.with_user(current_user.id).sudo().action_create_invoice()
					record.sudo().write({
						# 'rest_percentage':record.rest_percentage - percentage,
						'rest_percentage':record.rest_percentage - selected_percentage,
						'create_bill_count': record.create_bill_count + 1,
						# 'vendors_bill_per': selected_total_percentage
						# 'rest_percentage':record.rest_percentage - selected_percentage,

						})
					bill_id = record.invoice_ids
					msg = "Invoice create with " + selected_total_percentage
					record.with_user(current_user.id).sudo().message_post(body=msg)
				else:
					response = json.dumps({
					'error': True,
					# 'message': 'Percentage exceed. User can create bill of percentage is :' + str(record.rest_percentage) + '%' 
					'message': 'Record Not Found.' 
					
					})
					return response

				# end create bill method 
				invoice_id = record.invoice_ids
				_logger.info("call confirm button method and lenght of invoice id is %s  and ids is %s :",len(invoice_id), invoice_id)
				_logger.info("purchase order is : %s total on purchase is  : %s  and invoice ids is : %s", record_id,record.amount_total, record.invoice_ids)
				if payment_file_data and invoice_id and len(invoice_id) ==1:
					print("================= yes inside if ===========", invoice_id)
					# update attachment on invoice line id
					create_attachment =self.create_attachment(invoice_id,bill_number,payment_attachment_name,payment_file_data,current_user)
					print("==================create_attachment", create_attachment)
					for invoice_line in invoice_id.invoice_line_ids:
						_logger.info("In updating invoice line block and current line : %s " % invoice_line)
						act_qty = invoice_line.purchase_line_id.product_qty
						invoice_line.sudo().write({
						# 'quantity':(invoice_line.quantity * percentage)/100 ,
						# 'name' : 'Payment term [' + str(percentage) + ']'
						'quantity':(act_qty * selected_percentage)/100 ,
						# 'quantity':(invoice_line.quantity * selected_percentage)/100 ,
						'name' : 'Payment term [' + str(selected_percentage) + ']'
						})
					# updating current percentage
					invoice_id.sudo().write({
						'vendors_bill_per': selected_total_percentage,
						'invoice_date_due': due_date,
						'invoice_date': date.today(),
						'invoice_payment_term_id': payment_term_id.id,
						})
					invoice_id.with_user(2).sudo().action_post()
					msg = "Invoice No:" + invoice_id.name
					record.with_user(current_user.id).sudo().message_post(body=msg)
					call_confirm_status = True
					# calling backend method bill.com
					invoice_id.send_to_bill_com()
					invoice_id.approve_on_bill_com()
					success_status = 1
				elif invoice_id and len(invoice_id)> 1:
					for rec in invoice_id:
						_logger.info("multiple_recor : %s and state is %s and move_type is : %s ", rec.id, rec.state, rec.move_type)
					
					single_record = invoice_id.filtered(lambda inv: inv.move_type  in ['in_invoice'] and inv.state == 'draft')
					_logger.info("new bill created invoice is %s ", single_record)
					create_attachment =self.create_attachment(single_record,bill_number,kw.payment_attachment_name,payment_file_data,current_user)
					for invoice_line in single_record.invoice_line_ids:
						_logger.info("In updating invoice line block and current line : ", invoice_line)
						act_qty = invoice_line.purchase_line_id.product_qty
						invoice_line.sudo().write({
						# 'quantity':(invoice_line.quantity * percentage)/100 ,
						# 'name' : 'Payment term [' + str(percentage) + ']'
						# 'quantity':(invoice_line.quantity * selected_percentage)/100 ,
						'quantity':(act_qty * selected_percentage)/100 ,
						'name' : 'Payment term [' + str(selected_percentage) + ']'
						})
					# updating current percentage
					single_record.sudo().write({
					'vendors_bill_per': selected_total_percentage,
					'invoice_date_due': due_date,
					'invoice_date': date.today(),
					'invoice_payment_term_id': payment_term_id.id,
					})
					print("=#########################single_record", single_record)
					single_record.with_user(2).sudo().action_post()
					msg = "Invoice No:" + single_record.name
					record.with_user(current_user.id).sudo().message_post(body=msg)
					call_confirm_status = True
					# calling backend method bill.com
					single_record.send_to_bill_com()
					single_record.approve_on_bill_com()
					success_status = 1
				else:
					_logger.error(f" invoice line not create due to amount is exceed.: {e}")
			
			except Exception as e:
				success_status = 0
				_logger.error(f"Error while submiting create bill : {e}")
				exception_json = False
				try:
					exception_json = json.dumps({
						'message': str(json.loads(str(e)))
					})
				except ValueError:
					exception_json = str(e)
				message = str(exception_json)
				pass
			if len(record.invoice_ids) > 1:
				max_id = record.invoice_ids.ids[0]
				for rec in record.invoice_ids.ids:
					if rec > max_id:
						max_id = rec
				bill_id = request.env['account.move'].browse(max_id)
			# response = json.dumps({
			#     'error': True,
			#     'bill_id': bill_id.id,
			#     'bill_name': bill_id.name,
			#     'payment_state': bill_id.payment_state,
			#     'message': message
			#     })
			# return response
			# record._compute_po_complete() // remove by abhishek
			if message == 'The Bill/Refund date is required to validate this document.':
				success_status = 1
			print("-====================success_status========" , success_status)
			return success_status
			
	# create attachment function
	def create_attachment(self,record,bill_number, name,payment_file_data,current_user):
		_logger.info("create attachment self is %s and record is  : %s ",self,record)
		attachment_ids = []
		print("===============================record", record.ref)
		record.sudo().write({
			'payment_reference': bill_number,
			'ref': bill_number,
			})
		print("===============================record", record.ref)
		pdf_ids = request.env['ir.attachment'].with_user(current_user.id).sudo().create({
			'name': name,
			'type': 'binary',
			'datas': base64.encodebytes(payment_file_data).decode(),
			'res_model': 'account.move',
			'res_id': record.id,
			'mimetype': 'application/pdf'
		})
		attachment_ids.append(pdf_ids.id)
		record.with_user(current_user.id).message_post(body="", attachment_ids=attachment_ids)   


	@http.route('/create/vendor/check/invoice/duplicate', type='json', auth='public', methods=['POST'], csrf=False)
	# @http.route('/create/vendor/check/invoice/duplicate', type='http', auth='public', csrf=False)
	def create_payment(self):
		print("/create/vendor/check/invoice/duplicate *****************", self)
		data = json.loads(request.httprequest.data)
		print("data ****************************", data)

		invoice_no = data.get('invoice_no')
		record_id = data.get('record_id')
		selected_per = data.get('selected_per')
		uploaded_invoice_amount = data.get('uploaded_invoice_amount')
		po_amount = data.get('po_amount')
		calculate_amount = data.get('calculate_amount')

		if record_id and invoice_no:
			# Search for the purchase order record
			po = request.env['purchase.order'].sudo().browse(int(record_id))
			if po.exists():
				# Initialize flag for duplicate check
				duplicate = False
				duplicate_invoices = False
				mismatch_amount = False
				if int(uploaded_invoice_amount) != int(calculate_amount):
					print("*********************** in iff")
					mismatch_amount = True
					duplicate = True
				else:
					for rec in po.invoice_ids:
						if rec.ref == invoice_no:
							duplicate_invoices = True
							duplicate = True
							break
				# Return response as JSON
				result = {
					'duplicate': duplicate,
					'duplicate_invoices': duplicate_invoices,
					'mismatch_amount': mismatch_amount,

					'message': "Duplicate invoice found" if duplicate_invoices else "No duplicate invoice found"
				}
				return result
		# 		# return request.make_response(json.dumps(result), headers={'Content-Type': 'application/json'})
		# 	else:
		# 		return request.make_response(json.dumps({'error': 'Purchase order not found'}), headers={'Content-Type': 'application/json'})
		# return request.make_response(json.dumps({'error': 'Invalid parameters'}), headers={'Content-Type': 'application/json'})

	# ================hitanshi==========================

	# Vendor dashboard setting controller start here 
	@http.route(['/api/vendor/setting/email'], auth='public', website=True, csrf=False)
	def api_dashboard_setting_email(self, partner_id, **kw):
		print("===========calling /api/vendor/setting/email' ================", partner_id)
		partner_id = request.env['res.partner'].sudo().browse(int(partner_id))
		res_partner = request.env['res.partner'].sudo().search([('id', '=', partner_id.id)])
		current_user = request.env['res.users'].sudo().search([('partner_id', '=', res_partner.id)])
		print("========================================", current_user)
		print("========================================", res_partner)
		print("partner_id ================================", partner_id)
		url = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
		print("url ================================", url)
		logo_url = request.env['ir.config_parameter'].sudo().get_param('client_subscription.db_logo')
		user_id = current_user
		company_name = user_id.company_id.name
		company_mobile = user_id.company_id.mobile
		company_email = user_id.company_id.email
		company_address = (
			(user_id.company_id.street or "") + ", " + (user_id.company_id.street2 or "")
		).strip(", ")

		vendor_name = partner_id.id
		print("=vendor_name=========== " ,vendor_name )
		purchase_records = request.env['purchase.order'].sudo().search([('state', '=', 'purchase'),('partner_id', '=', vendor_name),('invoice_status', '!=', 'fully_billed')])
		print("=purchase_records============== " , purchase_records)
		return http.request.render('client_vendor_dashboard.setting_template_manage_email', {
			# 'purchase_records': purchase_records,
			'purchase_record_count':request.env['purchase.order'].sudo().search_count([('state', '=', 'purchase'),('partner_id', '=', vendor_name),('invoice_status', '!=', 'fully_billed')]),
			'user': current_user,
			'partner_id': vendor_name,
			'logo_url': logo_url,
			'company_name': company_name,
			'company_mobile': company_mobile,
			'company_email': company_email,
			'company_address': company_address,
		})
		

	@http.route(['/vendor/setting/phone'], auth='public', website=True)
	def dashboard_setting_phone(self, **kw):
		print("=====/vendor/setting/phon============ " , kw)
		partner_id = kw.get('partner_id')
		logo_url = request.env['ir.config_parameter'].sudo().get_param('client_subscription.db_logo')
		partner_id = request.env['res.partner'].sudo().browse(int(partner_id))
		res_partner = request.env['res.partner'].sudo().search([('id', '=', partner_id.id)])
		user_id = request.env['res.users'].sudo().search([('partner_id', '=', res_partner.id)])
		company_name = user_id.company_id.name
		company_mobile = user_id.company_id.mobile
		company_email = user_id.company_id.email
		company_address = (
			(user_id.company_id.street or "") + ", " + (user_id.company_id.street2 or "")
		).strip(", ")
		
		vendor_name = partner_id.id
		print("vendor_name =================== "  , vendor_name)        

		# Search for purchase records based on the vendor's location and billing status
		purchase_records = request.env['purchase.order'].sudo().search([
			('state', '=', 'purchase'),
			('partner_id', '=', vendor_name),
			('invoice_status', '!=', 'fully_billed')
		])
		print("=purchase_records=============== " , purchase_records)
		# Check if the user has the correct group permissions
		# if login_success and request.env.user and request.env.user.has_group('base.group_portal') and not request.env.user.has_group('base.group_public') and not request.env.user.has_group('base.group_user'):
			# Render the phone settings template with the necessary context
		return http.request.render('client_vendor_dashboard.setting_template_manage_phone', {
			'purchase_record_count': len(purchase_records),
			'user': user_id,
			'client_db': request.env.cr.dbname,
			'partner_id': vendor_name,
			'logo_url': logo_url,
			'company_name': company_name,
			'company_mobile': company_mobile,
			'company_email': company_email,
			'company_address': company_address,
		})
		

	@http.route(['/vendor/setting/profile'], auth='public', website=True)
	def dashboard_setting_profile(self, **kw):
		print("=================dashboard_setting_profile", kw)
		partner_id = kw.get('partner_id')
		logo_url = request.env['ir.config_parameter'].sudo().get_param('client_subscription.db_logo')
		partner_id = request.env['res.partner'].sudo().browse(int(partner_id))
		res_partner = request.env['res.partner'].sudo().search([('id', '=', partner_id.id)])
		user_id = request.env['res.users'].sudo().search([('partner_id', '=', res_partner.id)])
		company_name = user_id.company_id.name
		company_mobile = user_id.company_id.mobile
		company_email = user_id.company_id.email
		company_address = (
			(user_id.company_id.street or "") + ", " + (user_id.company_id.street2 or "")
		).strip(", ")
	   
		vendor_name = partner_id.id
		print("vendor_name =================== "  , vendor_name)        

		purchase_records = request.env['purchase.order'].sudo().search([('state', '=', 'purchase'),('partner_id', '=', vendor_name),('invoice_status', '!=', 'fully_billed')])
		print("=purchase_records=========== " , purchase_records)
		return http.request.render('client_vendor_dashboard.setting_template_manage_profile', {
			'purchase_record_count':request.env['purchase.order'].sudo().search_count([('state', '=', 'purchase'),('partner_id', '=', vendor_name),('invoice_status', '!=', 'fully_billed')]),
			'user': user_id,
			'client_db': request.env.cr.dbname,
			'partner_id': vendor_name,
			'logo_url': logo_url,
			'company_name': company_name,
			'company_mobile': company_mobile,
			'company_email': company_email,
			'company_address': company_address,
		})
		

	@http.route(['/vendor/setting/resetpassword'], auth='public', website=True)
	def dashboard_setting_resetpassword(self, **kw):
		logo_url = request.env['ir.config_parameter'].sudo().get_param('client_subscription.db_logo')
		partner_id = kw.get('partner_id')
		partner_id = request.env['res.partner'].sudo().browse(int(partner_id))
		res_partner = request.env['res.partner'].sudo().search([('id', '=', partner_id.id)])
		user_id = request.env['res.users'].sudo().search([('partner_id', '=', res_partner.id)])
		company_name = user_id.company_id.name
		company_mobile = user_id.company_id.mobile
		company_email = user_id.company_id.email
		company_address = (
			(user_id.company_id.street or "") + ", " + (user_id.company_id.street2 or "")
		).strip(", ")
		
		url = request.env['ir.config_parameter'].sudo().get_param('client_subscription.host_db_url')
		print("=url============= " , url)
		print("user_id ====================== "  , user_id)        
		print("user_id ====================== "  , request.env.user)        
		vendor_name = partner_id.id
		print("vendor_name =================== "  , vendor_name)        

		purchase_records = request.env['purchase.order'].sudo().search([('state', '=', 'purchase'),('partner_id', '=', vendor_name),('invoice_status', '!=', 'fully_billed')])
		print("purchase_records ==================  " , purchase_records)
			
		return http.request.render('client_vendor_dashboard.setting_template_manage_reset_password', {
			'purchase_record_count':request.env['purchase.order'].sudo().search_count([('state', '=', 'purchase'),('partner_id', '=', vendor_name),('invoice_status', '!=', 'fully_billed')]),
			'user': user_id,
			'client_db': request.env.cr.dbname,
			'partner_id': vendor_name,
			'client_url': url,
			'logo_url': logo_url,
			'company_name': company_name,
			'company_mobile': company_mobile,
			'company_email': company_email,
			'company_address': company_address,
		})


	@http.route(['/vendor/setting/email/submit'], auth='public', website=True)
	def dashboard_setting_email_submit(self, **kw):
		logo_url = request.env['ir.config_parameter'].sudo().get_param('client_subscription.db_logo')
		print("=================/vendor/setting/email/submit", kw)
		partner_id = kw.get('partner_id')
		partner_id = request.env['res.partner'].sudo().browse(int(partner_id))
		res_partner = request.env['res.partner'].sudo().search([('id', '=', partner_id.id)])
		user_id = request.env['res.users'].sudo().search([('partner_id', '=', res_partner.id)])
		
		print("request.env.user ************ " , request.env.user)
		return http.request.render('client_vendor_dashboard.email_submit_form_template', {
			'user': user_id,
			'partner_id': partner_id.id,
			'logo_url': logo_url,
		})

	@http.route(['/vendor/setting/email/check'], type='http', auth='public', website=True, methods=['POST'], csrf=False)
	# @http.route(['/vendor/setting/email/check'], type='http', auth='public', website=True, csrf=False)
	def dashboard_setting_check_email(self, **kw):
		print("=======================vendor/setting/email/check?", kw)
		partner_id = kw.get('partner_id')
		partner_id = request.env['res.partner'].sudo().browse(int(partner_id))
		res_partner = request.env['res.partner'].sudo().search([('id', '=', partner_id.id)])
		user_id = request.env['res.users'].sudo().search([('partner_id', '=', res_partner.id)])
		contact_email = kw.get('contact_email')
		contact_name = kw.get('contact_name')
		if user_id and user_id.partner_id:
			match_user_id = False
			if user_id and user_id.partner_id:
				for rec in user_id.partner_id.child_ids:
					if rec.name == contact_name and rec.email == contact_email:
						match_user_id = rec
						break                  
				request.session['otpStatus'] = True
				request.session['addEmail'] = contact_email
				request.session['addUserName'] = contact_name
				return http.request.render('client_vendor_dashboard.email_submit_form_template', {
					'Match':True,
					'user': user_id,
					'partner_id': partner_id.id
				})

	@http.route(['/api/render'], auth='public', website=True)
	def api_render(self, menu, partner_id):
		print("==========calling /vendor/setting/email =============", menu)
		print("==========calling /vendor/setting/email =============", partner_id)
		url = request.env['ir.config_parameter'].sudo().get_param('client_subscription.host_db_url')
		client_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
		client_db = request.env.cr.dbname
		print("==========calling /vendor/setting/email =============", url)
		if menu == 'dashboard':
			redirect_url = (f'{url}/vendor?db={client_db}&partner_id={partner_id}&client_url={client_url}')
			print("==========calling /vendor/setting/email =============", redirect_url)
			return werkzeug.utils.redirect(redirect_url)
		elif menu == 'purchase':
			print("==========menu purchase =============", request.env.user.login)
			print("==========menu purchase =============", request.env.user.password)
			redirect_url = (f'{url}/vendor/purchase?loginstatus=True&client_url={client_url}&partner_id={partner_id}')
			print("==========calling /vendor/setting/email =============", redirect_url)
			return werkzeug.utils.redirect(redirect_url)
		elif menu == 'unpaidinvoice':
			redirect_url = (f'{url}/vendor/unpaidinvoice?loginstatus=True&client_url={client_url}&partner_id={partner_id}')
			print("==========calling /vendor/setting/email =============", redirect_url)
			return werkzeug.utils.redirect(redirect_url)
		elif menu == 'paidinvoice':
			redirect_url = (f'{url}/vendor/paidinvoice?loginstatus=True&client_url={client_url}&partner_id={partner_id}')
			print("==========calling /vendor/setting/email =============", redirect_url)
			return werkzeug.utils.redirect(redirect_url)
		elif menu == 'setting':
			url = request
			redirect_url = (f'{client_url}/api/vendor/setting/email?partner_id={partner_id}')
			print("==========calling /vendor/setting/email =============", redirect_url)
			return werkzeug.utils.redirect(redirect_url)
		elif menu == 'logout':
			redirect_url = (f'{url}/vendor/logout?url={client_url}')
			print("==========calling /vendor/setting/email =============", redirect_url)
			return werkzeug.utils.redirect(redirect_url)
		else:
			return request.redirect('/vendor/login')


	@http.route(['/vendor/setting/email/otp/check'], type='http', auth='public', website=True, methods=['POST'], csrf=False)
	# @http.route(['/vendor/setting/email/otp/check'], type='http', auth='public', website=True, csrf=False)
	def dashboard_setting_check_otp_email(self, **kw):
		print("====================/vendor/setting/email/otp/check", kw)
		logo_url = request.env['ir.config_parameter'].sudo().get_param('client_subscription.db_logo')
		print("==========================/vendor/setting/email/otp/check", kw)
		contact_email = kw.get('contact_email')  
		contact_name =  kw.get('contact_name') 
		partner_id =  kw.get('partner_id') 
		partner_id = request.env['res.partner'].sudo().browse(int(partner_id))
		res_partner = request.env['res.partner'].sudo().search([('id', '=', partner_id.id)])
		user_id = request.env['res.users'].sudo().search([('partner_id', '=', res_partner.id)])
		print("==========================/vendor/setting/email/otp/check", partner_id)
		print("request.env.user==============================", request.env.user)
		if user_id and user_id.partner_id:
			print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>", user_id.partner_id)
			print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>", user_id.partner_id.child_ids)
			for rec in user_id.partner_id.child_ids:
				print("=======================", rec)
				auto_generate_otp = ''.join(random.choices('0123456789', k=6))
				try:
					mail_values = {
						'subject': 'Vendor Dashboard Verify Email OTP',
						'email_to': contact_email,
						'body_html': """
							<p>Hello {name},</p>
							<p>This is in reference to your Vendor Dashboard Verify Email.</p>
							<p>Your OTP is: {otp}</p>
						""".format(
							name=contact_name,
							otp=auto_generate_otp
						),
					}
					mail = request.env['mail.mail'].sudo().create(mail_values)
					print("===============mail", mail)
					if mail:
						mail.sudo().send()
						request.session['otpStatus'] = True
						request.session['addEmail'] = contact_email
						request.session['addUserName'] = contact_name
						request.session['emailOtp'] = auto_generate_otp
						return http.request.render('client_vendor_dashboard.check_email_form_template', {
							'user': user_id,
							'partner_id': partner_id.id,
							'logo_url': logo_url,
						})
				except Exception as e:
					return """
					<script>
						alert("Failed to send OTP email. Error: {}");
					</script>
					""".format(e)

	@http.route(['/vendor/setting/email/verified/confirm'], type='http', auth='public', website=True, methods=['POST'], csrf=False)
	# @http.route(['/vendor/setting/email/verified/confirm'], auth='public', website=True, csrf=False)
	def dashboard_setting_check_email_verified_confirm(self, **kw):
		print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>/vendor/setting/email/verified/confir", kw)
		logo_url = request.env['ir.config_parameter'].sudo().get_param('client_subscription.db_logo')
		partner_id =  kw.get('partner_id') 
		partner_id = request.env['res.partner'].sudo().browse(int(partner_id))
		res_partner = request.env['res.partner'].sudo().search([('id', '=', partner_id.id)])
		user_id = request.env['res.users'].sudo().search([('partner_id', '=', res_partner.id)])
		vendor_name = partner_id
		print("======vendor_name=============== " , vendor_name)
		otp_status = request.session.get('otpStatus') 
		add_email = request.session.get('addEmail')
		add_user_name = request.session.get('addUserName')
		email_otp = request.session.get('emailOtp')
		otp_code = kw.get('otp_code')
		print("request.env.user.partner_id.child_ids ***************** " ,user_id.partner_id.child_ids)
		print("request.env.user.partner_id: ******************** " , user_id.partner_id)
		if email_otp == otp_code:
			try:
				if user_id and user_id.partner_id:
					match_user_id = False
					for rec in user_id.partner_id.child_ids:
						if rec.name == add_user_name and rec.email == add_email:
							match_user_id = rec
							print("======match_user_id===========" , match_user_id)
							break
					print("=======aagya=======")
					if match_user_id:# Check if the matched user is a portal user
						print("=match_user_id.user_ids============ " , match_user_id.user_ids)
						
						if match_user_id.user_ids and match_user_id.user_ids.has_group('base.group_portal'):
							match_user_id.is_email_verified = True
						else:# Not a portal user, create a portal user
							user = request.env['res.users'].sudo().create({
								'name': match_user_id.name,
								'login': match_user_id.email,  # Use email as login
								'partner_id': match_user_id.id,
								'groups_id': [(6, 0, [request.env.ref('base.group_portal').id])] 
							})
							match_user_id.is_email_verified = True
					else:# No match found, create a new contact
						print("========================= nhi aaya ===================")
						contact_name = kw.get('contact_name')
						contact_email = kw.get('contact_email')
						rec_id = vendor_name.child_ids.sudo().create({
							'name': contact_name,
							'email': contact_email,
							'parent_id': vendor_name.id,
							# 'is_supplier': True,
						})
						print(">>>>>>>>>>>>>>>>>>>>>rec_id", rec_id)
						# Create a portal user for the new contact
						user = request.env['res.users'].sudo().create({
							'name': rec_id.name,
							'login': rec_id.email,  # Use email as login
							'partner_id': rec_id.id,
							'groups_id': [(6, 0, [request.env.ref('base.group_portal').id])] 
						})
						print('======================user', user)
						rec_id.is_email_verified = True

				return request.render('client_vendor_dashboard.check_email_form_template', {'Match': True, 'partner_id': vendor_name.id})
			except AccessError as e:
				return request.render('client_vendor_dashboard.access_denied', {'error': str(e)})
			except Exception as e:
				return request.render('client_vendor_dashboard.access_denied', {'error': 'An unexpected error occurred.'})
		else:
			wrong_passcode_alert = 'The passcode is incorrect !.'  
			return request.render('client_vendor_dashboard.check_email_form_template', {'passcode': wrong_passcode_alert, 'login': login, 'password': password})

	@http.route('/vendor/validate/otp/phoneNumber', auth='public', methods=['POST'], website=True , csrf=False)
	# @http.route('/vendor/validate/otp/phoneNumber', auth='public', website=True , csrf=False)
	def validate_reset_otp(self, **kw):
		_logger.info("==== we are in validate otp method ")        
		sent_otp = request.session.get('sent_opt')
		otp_status = request.session.get('otp_status') 
		uid = request.session.get('newuid') 
		user_enter_opt = kw.get('otp')
		logo_url = request.env['ir.config_parameter'].sudo().get_param('client_subscription.db_logo')
		if uid:
			uid = int(uid)
		_logger.info("============data on otp validate screen via session ============")
		
		if user_enter_opt and otp_status and sent_otp and sent_otp == user_enter_opt:
			login_success = True            
			request.session['loginstatus'] = login_success
			uid = request.session.uid = uid
			request.session.session_token = security.compute_session_token(
				request.session, request.env)
			login_message = 'You have successfully logged in'
			request.session['login_message'] = login_message
			return http.request.render('client_vendor_dashboard.dashboard_reset_otp_fill_via_phone', {'Match': True})
		else: 
			wrong_passcode_alert = 'The passcode is incorrect !.'  
			return http.request.render('client_vendor_dashboard.dashboard_reset_otp_fill_via_phone', {'passcode':wrong_passcode_alert})

		
	# after otp validate for rester password call controller to reset password: 
	@http.route('/vendor/password/change/otp/validate/Phone/success', auth='public', methods=['POST'], website=True , csrf=False) 
	# @http.route('/vendor/password/change/otp/validate/Phone/success', auth='public', website=True , csrf=False) 
	def password_change_validate_phone_otp(self, **kw):
		logo_url = request.env['ir.config_parameter'].sudo().get_param('client_subscription.db_logo')
		user_enter_opt = kw.get('otp')
		sent_otp = request.session.get('sent_opt')
		if user_enter_opt == sent_otp :
			request.session['optValidateStatus'] = True
			return http.request.render('client_vendor_dashboard.reset_confirm_password', { })

		# after otp validate for rester password call controller to reset password: 
		if kw.get('screen_status_change_password')=='OLD_NEW_PASSWORD':
			if kw.get('screen_status_change_password'):
				screen_status = kw.get('screen_status_change_password').strip()
			otp_valid_status = request.session.get('optValidateStatus')

			if kw.get('newpaassword') and kw.get('confirmpassword'):
				new = kw.get('newpaassword').strip() 
				confirm = kw.get('confirmpassword').strip()

			if new != confirm:
				return http.request.render('client_vendor_dashboard.reset_confirm_password', {
					'success':'NO',
					'isEnterMatchPass': True,
				})
			if  screen_status =='OLD_NEW_PASSWORD' and otp_valid_status and new == confirm :
				user_phone = request.session['mobile_no']
				user_phone = user_phone.replace("+", "")
				# _logger.info("=======change password block start for user id is : %s and user email Is : %s :",,user_phone )
				reset_user = request.env['res.partner'].sudo().search(['|',('phone','=',user_phone),('mobile','=',user_phone)])
				user = False
				if len(reset_user) == 1: 
					user = request.env['res.users'].sudo().search([('partner_id', '=',reset_user.id )])
				_logger.info("Password changed user object is : %s ", reset_user)
				if user  and new == confirm:
					# Reset the user's password
					_logger.info(" phone no. is : %s and new password : %s  and confirm password is : %s", user_phone , new , confirm)
					user.sudo().write({'password': confirm})
					url = request.env['ir.config_parameter'].sudo().get_param('client_subscription.host_db_url')
					data = {
						'password': confirm,
						'login': user_email,
					}
					print("Sending data:", data)

					try:
						response = requests.post(
							f"{url}/api/setpassword",
							json=data,
							headers={'Content-Type': 'application/json'},
							verify=False
						)
						if response.status_code == 200:
							result = response.json()
							print("==========================", result)
							if result['result'] == True:
								print("Password Updated")
							else:
								error_message = result.get('error', 'Unknown error')
								raise UserError(f"Failed to set Update password: {error_message}")

					except requests.exceptions.RequestException as e:
						raise UserError(f"Rquest failed: {str(e)}")
						
					# crear the session related password rester process here 
					request.session['loginstatus'] = None
					request.session['user_phone'] = None
					request.session['user_enter_opt'] = None
					request.session['sent_otp']=None
					request.session['user_id']=None
					response = http.request.render('client_vendor_dashboard.reset_confirm_password', {
						'success':'YES',
						'message': 'Password reset has been successfully',
					})
					return response
				else:
					return http.request.render('client_vendor_dashboard.reset_confirm_password', {
					'success':'NO',
					'message': 'Password Mismatch : failed',
					})
			else:
				message = 'Please contact to administrator : failed'
				return http.request.render('client_vendor_dashboard.reset_confirm_password', {
					'success':'NO',
					'message': message,
				})


	@http.route('/vendor/verified/otp/setting/verified', auth='public', website=True ,csrf=False)
	def add_email_verify_setting_(self, **kw):
		print("===================add_email_verify_setting_============kw", kw)
		partner_id =  kw.get('partner_id') 
		partner_id = request.env['res.partner'].sudo().browse(int(partner_id))
		res_partner = request.env['res.partner'].sudo().search([('id', '=', partner_id.id)])
		user = request.env['res.users'].sudo().search([('partner_id', '=', res_partner.id)])
		logo_url = request.env['ir.config_parameter'].sudo().get_param('client_subscription.db_logo')
		return http.request.render('client_vendor_dashboard.email_verified_confirm_form_template', {'logo_url': logo_url, 'partner_id': partner_id.id})

	@http.route(['/vendor/setting/phone/submit'], auth='public', website=True)
	def dashboard_setting_phone_submit(self, **kw):
		partner_id =  kw.get('partner_id') 
		partner_id = request.env['res.partner'].sudo().browse(int(partner_id))
		res_partner = request.env['res.partner'].sudo().search([('id', '=', partner_id.id)])
		current_user = request.env['res.users'].sudo().search([('partner_id', '=', res_partner.id)])
		logo_url = request.env['ir.config_parameter'].sudo().get_param('client_subscription.db_logo')
		vendor_name = partner_id.id 
		# if login_success and request.env.user  and request.env.user.has_group('base.group_portal') and not current_user.has_group('base.group_public') and not request.env.user.has_group('base.group_user'):
		if current_user  and current_user.has_group('base.group_portal') and not current_user.has_group('base.group_public') and not current_user.has_group('base.group_user'):
			return http.request.render('client_vendor_dashboard.phone_submit_form_template', {
				# 'purchase_records': purchase_records,
				'user': current_user,
				# 'login_status': login_success,
				'logo_url': logo_url,
			})
		else:
			return http.request.render('client_vendor_dashboard.vendor_dashboard_not_found_page', {
				'billed_invoice': [],
				'paid_invoice': [],
				'purchase_records': [],
				'invoice_records': [],
				'user': current_user,
				'login_status': login_success,
			})

	@http.route('/vendor/setting/phone/check', type='http', auth='user', website=True, csrf=False)
	def dashboard_setting_check_phone(self, **kw):
		partner_id =  kw.get('partner_id') 
		partner_id = request.env['res.partner'].sudo().browse(int(partner_id))
		res_partner = request.env['res.partner'].sudo().search([('id', '=', partner_id.id)])
		current_user = request.env['res.users'].sudo().search([('partner_id', '=', res_partner.id)])
		# login_success = request.session.get('loginstatus')
		logo_url = request.env['ir.config_parameter'].sudo().get_param('client_subscription.db_logo')
		# if not login_success:
		# 	request.session['loginstatus'] = None
		# 	return request.redirect('/vendor/login')

		user_phone = kw.get('phone')  
		user_phone = user_phone.replace("+","") 
		user_name =  kw.get('contact_name') 
		# match_user_id = False
		
		if current_user and current_user.partner_id:
			for rec in current_user.partner_id.child_ids:
				# email_id = rec.email
				if rec.name == user_name and rec.phone == user_phone and rec.email:
					match_user_id = rec
					break     

		if match_user_id and not match_user_id.user_ids:
			user = request.env['res.users'].sudo().create({
					'name': match_user_id.name,
					'login': match_user_id.email, 
					'partner_id': match_user_id.id,
					'groups_id': [(6, 0, [request.env.ref('base.group_portal').id])]  
				})
		
		if not user_phone:
			return request.render('client_vendor_dashboard.check_phone_number_form_template', {
				'error': 'Phone number field is mandatory.',
				'user_name': user_name,
			})
				 
		if current_user and current_user.partner_id:
			for rec in current_user.partner_id.child_ids:
				if rec.name == user_name and rec.phone == user_phone and rec.email:
					otp_text = ''.join(random.choices('0123456789', k=6))
					otp_send = False
					# phone number format 
					twilio_register_number = self.format_phone_number(kw.get('phone'))
					_logger.info("twilio_register_number : %s ",twilio_register_number)
					# API to send OTP if success then set opt_send variable True and redirect to validate  otp screen 
					sid = request.env['twilio.configuraion'].sudo().search([], limit=1)
					if not sid:
						raise ValidationError('Twilio Configuratin is not setup yet.')
					account_sid = sid.account_sid
					auth_token = sid.auth_token
					twilio_phone_number = sid.from_number
					# otp_send = True
					client = Client(account_sid, auth_token)
					try:
						message = client.messages.create(
						body=f"Thank you for registering! Here's your chance to complete the registration process using an OTP: {otp_text}",
						messaging_service_sid=twilio_phone_number,
						# from=twilio_phone_number,
						to='+' + twilio_register_number
						# to='+919670425757'

						)
						if message and message.sid:
							otp_send = True
							_logger.info('=Otp send :respone from twilio %s and sid  and opt is: %s and sent otp Phone number is: %s ', message ,message.sid,otp_text,twilio_register_number)
					except Exception as e:
						_logger.error(f"twillio Exception: otp send failed: {e}")
						otp_send = False
						pass
								 
					if otp_send  :
						request.session['sent_opt'] = otp_text
						request.session['otp_status'] = otp_send
						request.session['addphone'] = kw.get('phone').strip()
						request.session['user_name'] = user_name
						return http.request.render('client_vendor_dashboard.check_phone_number_form_template',{
							
							})
					else: 
						alert_script = """
							<script>
								alert("Either you have enter invalid phone number or OTP.Please try again.");
								# window.location.href = '/vendor/password/reset';
							</script>
										"""
						return alert_script
			  


	@http.route(['/vendor/setting/phone/verified/confirm'], type='http', auth='user', website=True, methods=['POST'], csrf=False)
	# @http.route(['/vendor/setting/phone/verified/confirm'], type='http', auth='user', website=True, csrf=False)
	def dashboard_setting_check_phone_verified_confirm(self, **kw):
		_logger.info("==== we are in validate otp method ")        
		sent_otp = request.session.get('sent_opt')  
		otp_status = request.session.get('otp_status')  
		user_phone = request.session.get('addphone') 
		user_name = request.session.get('user_name')
		user_enter_opt = kw.get('otp_code')
		logo_url = request.env['ir.config_parameter'].sudo().get_param('client_subscription.db_logo')
		# passcode_error = kw.get('otp_error'
		# if uid:
		#     uid = int(uid)
		# _logger.info("============data on otp validate screen via session ============")
		
		if user_enter_opt and otp_status and sent_otp and sent_otp == user_enter_opt:
			login_success = True  
			if request.env.user and request.env.user.partner_id:
				for rec in request.env.user.partner_id.child_ids:
					email_id = rec.email
					if rec.name == user_name and rec.phone == user_phone and rec.email:
						match_user_id = rec
						match_user_id.is_phone_verified = True
						break   
			
			request.session['loginstatus'] = login_success
			# uid = request.session.uid = uid
			request.session.session_token = security.compute_session_token(
				request.session, request.env)
			login_message = 'You have successfully logged in'
			request.session['login_message'] = login_message

			return http.request.render('client_vendor_dashboard.check_phone_number_form_template', {'Match': True})
		else: 
			wrong_passcode_alert = 'The passcode is incorrect !.'  
			
			
			return http.request.render('client_vendor_dashboard.check_phone_number_form_template', {'passcode':wrong_passcode_alert})
			

	@http.route('/vendor/verified/otp/setting/phone/verified', auth='user', website=True ,csrf=False)
	def verify_add_phone_setting(self, **kw): 
		return http.request.render('client_vendor_dashboard.phone_verified_confirm_form_template', {})       

# ------------------Edit Profile----------

	@http.route('/vendor/edit/profile', auth='public', website=True, csrf=False)
	def edit_profile(self, **kw):
		_logger.info("==== we are in edit profile method ==========================", kw)
		logo_url = request.env['ir.config_parameter'].sudo().get_param('client_subscription.db_logo')
		partner_id =  kw.get('partner_id') 
		partner_id = request.env['res.partner'].sudo().browse(int(partner_id))
		res_partner = request.env['res.partner'].sudo().search([('id', '=', partner_id.id)])
		user = request.env['res.users'].sudo().search([('partner_id', '=', res_partner.id)])
		vendor_name = partner_id.id
		purchase_records = request.env['purchase.order'].sudo().search([('state', '=', 'purchase'),('partner_id', '=', vendor_name),('invoice_status', '!=', 'fully_billed')])
		base_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
		user_phone = kw.get('phone')  
		user_phone = user_phone.replace("+","")
		
		user.partner_id.sudo().write({
			'name': kw.get('name'),
			'email': kw.get('email_id'),
			'phone': user_phone,
			'zip': kw.get('zip_code'),
			'street':kw.get('address'),
		})

		state_name = kw.get('region')
		if state_name:
			state = request.env['res.country.state'].sudo().search([('name', '=', state_name)], limit=1)
			if state:
				user.partner_id.state_id = state.id
			else:
				_logger.warning("State with name %s not found", state_name)

		country_name = kw.get('country')
		if country_name:
			country = request.env['res.country'].sudo().search([('name', '=', country_name)], limit=1)
			if country:
				user.partner_id.country_id = country.id
			else:
				_logger.warning("Country with name %s not found", country_name)

		user.partner_id.sudo().write({
			'state_id': state.id if state_name and state else False,
			'country_id': country.id if country_name and country else False,
		})

		# if 'file-input' in request.httprequest.files:
		if kw.get('file-input'):
			file = request.httprequest.files['file-input']
			file_content = file.read()
			encoded_file = base64.b64encode(file_content)
			user.partner_id.sudo().write({'image_1920': encoded_file})
			user.sudo().write({'image_1920': encoded_file})


		return request.redirect(f'/vendor/setting/profile?partner_id={vendor_name}')

		return request.render('client_vendor_dashboard.setting_template_manage_email', {
			'Edit_profile': True,
			# 'purchase_records': purchase_records,
			'purchase_record_count':request.env['purchase.order'].sudo().search_count([('state', '=', 'purchase'),('partner_id', '=', vendor_name),('invoice_status', '!=', 'fully_billed')]),
			'user': user,
			'logo_url': logo_url,
			})


	@http.route('/vendor/revoke/access', auth='public', website=True, csrf=False)
	def revoke_access(self, **kw):
		_logger.info("==== We are in the revoke access method ==========================", kw)
		partner_id =  kw.get('partner_id') 
		partner_id = request.env['res.partner'].sudo().browse(int(partner_id))
		res_partner = request.env['res.partner'].sudo().search([('id', '=', partner_id.id)])
		user_id = request.env['res.users'].sudo().search([('partner_id', '=', res_partner.id)])
		logo_url = request.env['ir.config_parameter'].sudo().get_param('client_subscription.db_logo')
		company_name = user_id.company_id.name
		company_mobile = user_id.company_id.mobile
		company_email = user_id.company_id.email
		company_address = (
			(user_id.company_id.street or "") + ", " + (user_id.company_id.street2 or "")
		).strip(", ")
		
		vendor_name = partner_id.id
		purchase_records = request.env['purchase.order'].sudo().search([
			('state', '=', 'purchase'),
			('partner_id', '=', vendor_name),
			('invoice_status', '!=', 'fully_billed')
		])
		
		user_phone = kw.get('phone', '').replace("+", "")
		user_name = kw.get('contact_name', '')
	   
		port_user = request.env['res.partner'].sudo().search([
			'|',
			('phone', '=', user_phone),
			('mobile', '=', user_phone)
		])
	   
		match_user_id = False
		if user_id and user_id.partner_id:
			for rec in user_id.partner_id.child_ids:
				if rec.name == user_name and rec.phone == user_phone and rec.email:
					match_user_id = rec
					break
		
		if match_user_id and match_user_id.user_ids:
			user = match_user_id.user_ids[0]

			match_user_id.with_user(2).sudo().write({
				'is_phone_verified': False,
				'is_email_verified': False,
				'user_ids': [(3, user.id)],
				# 'user_ids': False,
			})
		
		
		
		return request.render('client_vendor_dashboard.setting_template', {
			'revoke_access': True,
			# 'purchase_records': purchase_records,
			'purchase_record_count':request.env['purchase.order'].sudo().search_count([('state', '=', 'purchase'),('partner_id', '=', vendor_name),('invoice_status', '!=', 'fully_billed')]),
			# 'user': match_user_id,
			'user': user_id,
			'company_name': company_name,
			'company_mobile': company_mobile,
			'company_email': company_email,
			'company_address': company_address,
		})


	@http.route('/vendor/password/reset', auth='public', website=True )
	def password_validate_page(self, **kw):
		logo_url = request.env['ir.config_parameter'].sudo().get_param('client_subscription.db_logo')
		response = http.request.render('client_vendor_dashboard.reset_password_template', {
			"alert_status":False,
			'logo_url': logo_url,
			})
		response.headers['Cache-Control'] = 'no-store, must-revalidate'
		response.headers['Pragma'] = 'no-cache'
		response.headers['Expires'] = '0'
		return response
		# return http.request.render('client_vendor_dashboard.reset_password_template', {
		#     "alert_status":False,
		#     })

	@http.route(['/vendor/password/change','/vendor/password/change/otp/email'], type='http', auth='public', website=True ,csrf=False , methods=['POST','GET'])
	# @http.route(['/vendor/password/change','/vendor/password/change/otp/email'], type='http', auth='public', website=True ,csrf=False)
	def password_change(self, **kw):
		logo_url = request.env['ir.config_parameter'].sudo().get_param('client_subscription.db_logo')
		is_valid_screen = kw.get('is_forget_password_email')
		user_enter_email = kw.get('reset_email')
		if is_valid_screen and user_enter_email and is_valid_screen=='YES':
			_logger.info("we are in send opt button page ============")
			reset_user = request.env['res.users'].sudo().search([('login','=',user_enter_email.strip())])
			reset_user_count = request.env['res.users'].sudo().search_count([('login','=',user_enter_email.strip())])
			if reset_user and reset_user_count == 1:
				if reset_user.has_group('base.group_portal') and not reset_user.has_group('base.group_public') and not reset_user.has_group('base.group_user'):
					# after click on Send OTP button 
					user_id = reset_user.id
					user_email = user_enter_email
					_logger.info("we are in after send otp button action block")
					user = request.env['res.users'].sudo().search([('id','=',user_id)])
					auto_generate_otp = ''.join(random.choices('0123456789', k=6))
					# start code for sending email to current user for reset password
					try:
						mail_values = {
							'subject': 'Vendor Dashboard Password Reset OTP',
							'email_to': user.login,
							'body_html': 'Hello {name},<br><br>This is the reference of regarding Vendor Dashboard Reset Password.<br><br>Your OTP is : {otp}'.format(
							name=user.name,
							otp=auto_generate_otp,)
						}
						mail = request.env['mail.mail'].sudo().create(mail_values)
						if mail:
							mail_sent = mail.sudo().send(auto_commit=True)
							opt_send_status = True
							_logger.info("===Email sent successfully!") 
						else:
							opt_send_status = False
							_logger.info("====mail send failed block: and value of send mail status is : %s  ",opt_send_status)
					except Exception as error:
						opt_send_status = False
						_logger.info("===========Exception while sending OTP  : %s and your OTP  is: %s and user email is: %s  ", error,user.login,auto_generate_otp)
						# pass
					if opt_send_status:
						_logger.info("==========otp  is %s ", auto_generate_otp)
						request.session['otpStatus'] = opt_send_status
						request.session['resetEmail'] = user_email
						request.session['resetUserId'] = user_id
						request.session['emailOtp'] = auto_generate_otp
						return http.request.render('client_vendor_dashboard.reset_password_email_otp_fill', {
							"alert_status":False,
							"logo_url" : logo_url,
						}) 
					else:
						_logger.info("we are otp failed bloc: ==================")
						request.session['otpStatus'] = None
						request.session['resetEmail'] = None
						request.session['resetUserId'] = None
						request.session['emailOtp'] = None
						return http.request.render('client_vendor_dashboard.reset_password_email_otp_button', {
						"reset_user" : user_id,
						"user_enter_email" : user_email,
						"logo_url" : logo_url,
						"validate":True,
						"email_otp_status" : False,
						"alert" : True,
						})

			else:
				response = http.request.render('client_vendor_dashboard.reset_password_template', {
					"user_email":user_enter_email,
					"logo_url":logo_url,
					"userid":reset_user,
					"alert_status":True        
				})
				response.headers['Cache-Control'] = 'no-store, must-revalidate'
				response.headers['Pragma'] = 'no-cache'
				response.headers['Expires'] = '0'
				return response
				# return http.request.render('client_vendor_dashboard.reset_password_template', {
				#     "user_email":user_enter_email,
				#     "userid":reset_user,
				#     "alert_status":True        
				# })

	@http.route(['/vendor/password/change/otp/validate/success','/vendor/password/change/otp/validate'], type='http', auth='public', website=True ,csrf=False , methods=['POST','GET'])
	# @http.route(['/vendor/password/change/otp/validate/success','/vendor/password/change/otp/validate'], type='http', auth='public', website=True ,csrf=False)
	def password_change_validate_email_otp(self, **kw):
		# fetching set session for email otp validate
		user_input_otp =''
		screen_status =''
		otp_status = request.session.get('otpStatus')  
		user_email = request.session.get('resetEmail')  
		user_id = request.session.get('resetUserId')  
		system_otp = request.session.get('emailOtp') 
		logo_url = request.env['ir.config_parameter'].sudo().get_param('client_subscription.db_logo')
		_logger.info("=================we are in validate email otp")
		if kw.get('user_enter_otp'):
			user_input_otp = kw.get('user_enter_otp').strip()

		if kw.get('screen_status_otp'):
			screen_status = kw.get('screen_status_otp').strip()
		if otp_status and user_email and user_id and system_otp and screen_status=='EMAIL_OTP_SCREEN' and user_input_otp:
			if system_otp == user_input_otp:
				request.session['autoValidate1'] = True
				return http.request.render('client_vendor_dashboard.reset_password_email_otp_fill', {
					 "autoValidate": True,
					 "logo_url": logo_url, })
			else:
				_logger.info("==========Enter wrong OTP %s ", system_otp)
				request.session['otpStatus'] = otp_status
				request.session['resetEmail'] = user_email
				request.session['resetUserId'] = user_id
				request.session['emailOtp'] = system_otp
				# request.session['isEnterWrongOTP'] = True
				request.session['autoValidate1'] = False
				return http.request.render('client_vendor_dashboard.reset_password_email_otp_fill', {
					"isEnterWrongOTP": True,
					"logo_url": logo_url,
				}) 

		# after otp validate for rester password call controller to reset password: 
		if kw.get('screen_status_change_password')=='OLD_NEW_PASSWORD':
			if kw.get('screen_status_change_password'):
				screen_status = kw.get('screen_status_change_password').strip()
			otp_valid_status = request.session.get('optValidateStatus')
			if kw.get('newpaassword') and kw.get('confirmpassword'):
				new = kw.get('newpaassword').strip() 
				confirm = kw.get('confirmpassword').strip()
			if new != confirm:
				return http.request.render('client_vendor_dashboard.change_password_with_email_validate', {
					'success':'NO',
					'isEnterMatchPass': True,
					'logo_url': logo_url,
				})
			if otp_status and user_email and user_id and system_otp and screen_status =='OLD_NEW_PASSWORD' and otp_valid_status and new == confirm :
				# user_id = int(user_id.strip())
				change_password_email = user_email
				_logger.info("=======change password block start for user id is : %s and user email Is : %s :", user_id,change_password_email )
				user = request.env['res.users'].sudo().search(['&',('id','=',user_id),('login','=',change_password_email)])
				_logger.info("Password changed user object is : %s ", user)
				if user  and new == confirm:
					# Reset the user's password
					_logger.info("changed password of user id : %s and email is : %s and new password : %s  and confirm password is : %s", )
					user.sudo().write({'password': confirm})
					url = request.env['ir.config_parameter'].sudo().get_param('client_subscription.host_db_url')
					data = {
						'password': confirm,
						'login': user_email,
					}
					print("Sending data:", data)

					# try:
					# 	response = requests.post(
					# 		f"{url}/api/setpassword",
					# 		json=data,
					# 		headers={'Content-Type': 'application/json'},
					# 		verify=False
					# 	)
					# 	if response.status_code == 200:
					# 		result = response.json()
					# 		print("==========================", result)
					# 		if result['result'] == True:
					# 			print("Password Updated")
					# 		else:
					# 			error_message = result.get('error', 'Unknown error')
					# 			raise UserError(f"Failed to set Update password: {error_message}")

					# except requests.exceptions.RequestException as e:
					# 	raise UserError(f"Rquest failed: {str(e)}")

					# crear the session related password rester process here 
					request.session['loginstatus'] = None
					request.session['otpStatus'] = None
					request.session['resetEmail'] = None
					request.session['resetUserId'] = None
					request.session['emailOtp'] = None
					request.session['optValidateStatus'] = None
					# return http.request.render('client_vendor_dashboard.change_password_with_email_validate', {
					#     'success':'YES',
					#     'message': 'Password reset has been successfully',
					# })
					response = http.request.render('client_vendor_dashboard.change_password_with_email_validate', {
						'success':'YES',
						'logo_url':logo_url,
						'message': 'Password reset has been successfully',
					})
					# response.headers['Cache-Control'] = 'no-store, must-revalidate'
					# response.headers['Pragma'] = 'no-cache'
					# response.headers['Expires'] = '0'
					return response
				else:
					return http.request.render('client_vendor_dashboard.change_password_with_email_validate', {
					'success':'NO',
					'message': 'Password Mismatch : failed',
					'logo_url': logo_url,
					})
			else:
				message = 'Please contact to administrator : failed'
				return http.request.render('client_vendor_dashboard.change_password_with_email_validate', {
					'success':'NO',
					'message': message,
					'logo_url': logo_url,
				})
		if request.session.get('autoValidate1'):
			request.session['optValidateStatus'] = True
			return http.request.render('client_vendor_dashboard.change_password_with_email_validate', {"logo_url": logo_url})

	# Start controller if user is trying to login via OTP
	@http.route('/vendor/login/otp', type='http', website=True , methods=['POST'], csrf=False ,auth="public")
	# @http.route('/vendor/login/otp', type='http', website=True, csrf=False ,auth="public")
	def login_via_opt(self,redirect=None , **kw):
		_logger.info("===========we are in /vendor/login/otp ========")
		login_via_opt = kw.get('login_with_otp')
		login_via_email = kw.get('login_with_usermail')
		logo_url = request.env['ir.config_parameter'].sudo().get_param('client_subscription.db_logo')
		_logger.info("loign via opt: %s ",login_via_opt)
		_logger.info("loign via usermail: %s",login_via_email)
		if login_via_opt and login_via_opt=='yes' and kw.get('phone'):
			user_phone = kw.get('phone')
			user_phone = user_phone.replace("+", "")
			_logger.info("after removing + sign phone number : ==%s ",user_phone)
			login_user = request.env['res.partner'].sudo().search(['|',('phone','=',user_phone),('mobile','=',user_phone)])
			login_user_count = request.env['res.partner'].sudo().search_count(['|',('phone','=',user_phone),('mobile','=',user_phone)])
			# alert if user is not found 
			if not login_user and not login_user_count:
				# alert_script = """
				# <script>
				#     alert("User is not found for Input Mobile Number.Please Enter valid Phone Number.");
				#     window.location.href = '/vendor/login';
				# </script>
				#             """
				# return alert_script
				user_not_found = 'Incorrect Mobile Number'        
				# redirect_url = '/vendor/login?usererror={}'.format(user_not_found)
				# return request.redirect(redirect_url)
				return http.request.render('client_vendor_dashboard.dashboard_login', {'wrong_phone':user_not_found})

			 # alert if user is found but multiple user exist for input phone number 
			if login_user and  login_user_count > 1:
				# alert_script = """
				# <script>
				#     alert("Multiple User found.We cant proceed further.Enter Unique Mobile Number for validate Vendor.");
				#     window.location.href = '/vendor/login';
				# </script>
				#             """
				# return alert_script
				multiple_user = 'Multiple User found for Input Mobile.'        
				redirect_url = '/vendor/login?usererror={}'.format(multiple_user)        
				return request.redirect(redirect_url)

			if login_user and login_user_count == 1:                
				portal_user = request.env['res.users'].sudo().search([('partner_id','=',login_user.id)])
				if portal_user.has_group('base.group_portal') and not portal_user.has_group('base.group_public') and not portal_user.has_group('base.group_user'):
					otp_text = ''.join(random.choices('0123456789', k=6))
					otp_send = False
					# phone number format: 
					twilio_register_number = self.format_phone_number(kw.get('phone'))
					_logger.info("twilio_register_number : %s ",twilio_register_number)
					# API to send OTP if success then set opt_send variable True and redirect to validate  otp screen 
					sid = request.env['twilio.configuraion'].sudo().search([], limit=1)
					if not sid:
						raise ValidationError('Twilio Configuratin is not setup yet.')
					account_sid = sid.account_sid
					auth_token = sid.auth_token
					twilio_phone_number = sid.from_number
					# otp_send = True
					client = Client(account_sid, auth_token)
					try:
						message = client.messages.create(
						body=f"Thank you for registering! Here's your chance to complete the registration process using an OTP: {otp_text}",
						messaging_service_sid=twilio_phone_number,
						# from=twilio_phone_number,
						to='+' + twilio_register_number
						)
						if message and message.sid:
							otp_send = True
							_logger.info('=OtP send :respone from twilio %s and sid  and opt is: %s and sent otp Phone number is: %s ', message ,message.sid,otp_text,twilio_register_number)
					except Exception as e:
						_logger.error(f"twillio Exception: otp send failed: {e}")
						otp_send = False
						pass
					# write code to send opt end here               
					if otp_send  :
						request.session['sent_opt'] = otp_text
						request.session['otp_status'] = otp_send
						request.session['mobile_no'] = kw.get('phone').strip()
						request.session['newuid'] = portal_user.id
						return http.request.render('client_vendor_dashboard.dashboard_otp_fill', { })
					else: 
						alert_script = """
							<script>
								alert("Either you have enter invalid phone number or OTP.Please try again.");
								window.location.href = '/vendor/login';
							</script>
										"""
						return alert_script
				else:
					alert_script = """
					<script>
						alert("Only Portal Vendor User can login.Please use different mobile number.");
						window.location.href = '/vendor/login';
					</script>
								"""               
	# End controller if user is trying to login via OTP

	# Start controller user login with url
	@http.route('/vendor/login/url/<int:record_id>/signup_token/<string:signup_token>', auth='public', website=True )
	def dashboard_login_via_url(self, record_id, signup_token, **kw):
		login_user = request.env['res.users'].sudo().search([('id','=',record_id),('signup_token','=',signup_token)])
		logo_url = request.env['ir.config_parameter'].sudo().get_param('client_subscription.db_logo')
		if login_user.has_group('base.group_portal'):    
			uid = login_user.id
			if uid:
				uid = int(uid)
			_logger.info("============data on otp validate screen via session ============")
			# if user_enter_opt and otp_status and sent_otp and sent_otp == user_enter_opt:
			login_success = True
			request.session['loginstatus'] = login_success
			uid = request.session.uid = uid
			request.session.session_token = security.compute_session_token(
				request.session, request.env)
			redirect = '/vendor/home'
			login_message = 'You have successfully logged in'
			request.session['login_message'] = login_message
			return request.redirect(self._login_redirect(uid, redirect=redirect))
		else:
			alert_script = """
			<script>
				alert("Only Portal Vendor User can login.Please use different User url.");
				window.location.href = '/vendor/login';
			</script>
						"""
			return alert_script

	def format_phone_number(self,p_number):
		_logger.info("phone_number formating  block : %s ",p_number)      
		if '+' in p_number:
			p_number = p_number.replace("+", "")

		if '(' in p_number:
			p_number = p_number.replace("(", "")

		if ')' in p_number:
			p_number = p_number.replace(")", "")

		if '-' in p_number:
			p_number = p_number.replace("-", "")
		return p_number
		# pattern = re.compile(r'^\+\d{2}\(\d{3}\)\d{3}-\d{4}$')
		# for US contry code 
		# pattern = re.compile(r'^\+\d{1}\(\d{3}\)\d{3}-\d{4}$')
		# Check if the phone_number matches the pattern
		# return bool(pattern.match(p_number))

	def _login_redirect(self, uid, redirect=None):
		return redirect if redirect else 'dashboard/vendor'

	# controller to validate sent OTP to user start here
	@http.route('/vendor/validate/otp', auth='public', methods=['POST'], website=True , csrf=False)
	# @http.route('/vendor/validate/otp', auth='public', website=True , csrf=False)
	def validate_otp(self, **kw):
		_logger.info("==== we are in validate otp method ")        
		sent_otp = request.session.get('sent_opt')      
		otp_status = request.session.get('otp_status')  
		uid = request.session.get('newuid')  
		user_enter_opt = kw.get('otp')
		logo_url = request.env['ir.config_parameter'].sudo().get_param('client_subscription.db_logo')
		if uid:
			uid = int(uid)
		_logger.info("============data on otp validate screen via session ============")
		
		if user_enter_opt and otp_status and sent_otp and sent_otp == user_enter_opt:
			print("*****************************************")
			login_success = True            
			request.session['loginstatus'] = login_success
			uid = request.session.uid = uid
			request.session.session_token = security.compute_session_token(
				request.session, request.env)
			login_message = 'You have successfully logged in'
			request.session['login_message'] = login_message
			return http.request.render('client_vendor_dashboard.dashboard_otp_fill', {'Match': True})
		else: 
			wrong_passcode_alert = 'The passcode is incorrect !.'  
			return http.request.render('client_vendor_dashboard.dashboard_otp_fill', {'passcode':wrong_passcode_alert})
			# alert_script = """
			#     <script>
			#         alert("Something wrong while validating OTP.Please try again.");
			#         window.location.href = '/vendor/login';
			#     </script>
			#                 """
			# return alert_script       
			# redirect_url = '/vendor/validate/otp?otp_error={}'.format(wrong_passcode)        
			# return request.redirect(redirect_url)
			return http.request.render('client_vendor_dashboard.dashboard_otp_fill', {'passcode':wrong_passcode_alert})
	
	@http.route('/vendor/change/password/phone', type='http', website=True , methods=['POST'], csrf=False ,auth="public")
	# @http.route('/vendor/change/password/phone', type='http', website=True , csrf=False ,auth="public")
	def reset_via_phone(self,redirect=None , **kw):
		_logger.info("===========we are in /vendor/change/password/phone ========")
		reset_via_phone = kw.get('is_forget_password_phone')
		reset_phone_user = kw.get('reset_phone')
		logo_url = request.env['ir.config_parameter'].sudo().get_param('client_subscription.db_logo')
		_logger.info("loign via opt: %s ",reset_via_phone)
		_logger.info("loign via phone number: %s",reset_phone_user)
		if reset_via_phone and reset_phone_user and reset_via_phone =='YES':
			user_phone = kw.get('reset_phone')
			user_phone = user_phone.replace("+", "")
			_logger.info("after removing + sign phone number : ==%s ",user_phone)
			reset_user = request.env['res.partner'].sudo().search(['|',('phone','=',user_phone),('mobile','=',user_phone)])
			reset_user_count = request.env['res.partner'].sudo().search_count(['|',('phone','=',user_phone),('mobile','=',user_phone)])
			# alert if user is not found 
			if not reset_user and not reset_user_count:
				user_not_found = 'Incorrect Mobile Number'        
				# redirect_url = '/vendor/login?usererror={}'.format(user_not_found)
				# redirect_url = '/vendor/password/reset?usererror={}'.format(user_not_found)
				return http.request.render('client_vendor_dashboard.reset_password_template', {'wrong_phone':user_not_found})

			 #  if user is found but multiple user exist for input phone number 
			if reset_user and  reset_user_count > 1:
				multiple_user = 'Multiple User found for Input Mobile.'        
				redirect_url = '/vendor/login?usererror={}'.format(multiple_user)        
				return request.redirect(redirect_url)

			if reset_user and reset_user_count == 1:                
				portal_user = request.env['res.users'].sudo().search([('partner_id','=',reset_user.id)])
				if portal_user.has_group('base.group_portal') and not portal_user.has_group('base.group_public') and not portal_user.has_group('base.group_user'):
					otp_text = ''.join(random.choices('0123456789', k=6))
					otp_send = False
					# phone number format 
					twilio_register_number = self.format_phone_number(kw.get('phone'))
					_logger.info("twilio_register_number : %s ",twilio_register_number)
					# API to send OTP if success then set opt_send variable True and redirect to validate  otp screen 
					sid = request.env['twilio.configuraion'].sudo().search([], limit=1)
					if not sid:
						raise ValidationError('Twilio Configuratin is not setup yet.')
					account_sid = sid.account_sid
					auth_token = sid.auth_token
					twilio_phone_number = sid.from_number
					# otp_send = True
					client = Client(account_sid, auth_token)
					try:
						message = client.messages.create(
						body=f"Thank you for registering! Here's your chance to complete the registration process using an OTP: {otp_text}",
						messaging_service_sid=twilio_phone_number,
						# from=twilio_phone_number,
						to='+' + twilio_register_number
						# to='+919670425757'

						)
						if message and message.sid:
							otp_send = True
							_logger.info('=OtP send :respone from twilio %s and sid  and opt is: %s and sent otp Phone number is: %s ', message ,message.sid,otp_text,twilio_register_number)
					except Exception as e:
						_logger.error(f"twillio Exception: otp send failed: {e}")
						otp_send = False
						pass
					# write code to send opt end here               
					if otp_send  :
						request.session['sent_opt'] = otp_text
						request.session['otp_status'] = otp_send
						request.session['mobile_no'] = kw.get('reset_phone').strip()
						# request.session['number']=kw.get('phone')
						request.session['newuid'] = portal_user.id

						return http.request.render('client_vendor_dashboard.dashboard_reset_otp_fill_via_phone', {})
					else: 
						alert_script = """
							<script>
								alert("Either you have enter invalid phone number or OTP.Please try again.");
								window.location.href = '/vendor/password/reset';
							</script>
										"""
						return alert_script
				else:
					alert_script = """
					<script>
						alert("Only Portal Vendor User can Reset password.Please use different mobile number.");
						window.location.href = '/vendor/password/reset';
					</script>
								"""   

	@http.route('/vendor/validate/otp/phoneNumber', auth='public', methods=['POST'], website=True , csrf=False)
	# @http.route('/vendor/validate/otp/phoneNumber', auth='public', website=True , csrf=False)
	def validate_reset_otp(self, **kw):
		_logger.info("==== we are in validate otp method ")
		logo_url = request.env['ir.config_parameter'].sudo().get_param('client_subscription.db_logo')        
		sent_otp = request.session.get('sent_opt')
		otp_status = request.session.get('otp_status') 
		uid = request.session.get('newuid') 
		user_enter_opt = kw.get('otp')
		# passcode_error = kw.get('otp_error')
		if uid:
			uid = int(uid)
		_logger.info("============data on otp validate screen via session ============")
		
		if user_enter_opt and otp_status and sent_otp and sent_otp == user_enter_opt:
			login_success = True            
			request.session['loginstatus'] = login_success
			uid = request.session.uid = uid
			request.session.session_token = security.compute_session_token(
				request.session, request.env)
			login_message = 'You have successfully logged in'
			request.session['login_message'] = login_message
			return http.request.render('client_vendor_dashboard.dashboard_reset_otp_fill_via_phone', {'Match': True})
		else: 
			wrong_passcode_alert = 'The passcode is incorrect !.'  
			return http.request.render('client_vendor_dashboard.dashboard_reset_otp_fill_via_phone', {'passcode':wrong_passcode_alert})

		
	# after otp validate for rester password call controller to reset password: 
	@http.route('/vendor/password/change/otp/validate/Phone/success', auth='public', methods=['POST'], website=True , csrf=False) 
	# @http.route('/vendor/password/change/otp/validate/Phone/success', auth='public', website=True , csrf=False) 
	def password_change_validate_phone_otp(self, **kw):
		user_enter_opt = kw.get('otp')
		sent_otp = request.session.get('sent_opt')
		if user_enter_opt == sent_otp :
			request.session['optValidateStatus'] = True
			return http.request.render('client_vendor_dashboard.reset_confirm_password', { })

		# after otp validate for rester password call controller to reset password: 
		if kw.get('screen_status_change_password')=='OLD_NEW_PASSWORD':
			if kw.get('screen_status_change_password'):
				screen_status = kw.get('screen_status_change_password').strip()
			otp_valid_status = request.session.get('optValidateStatus')

			if kw.get('newpaassword') and kw.get('confirmpassword'):
				new = kw.get('newpaassword').strip() 
				confirm = kw.get('confirmpassword').strip()

			if new != confirm:
				return http.request.render('client_vendor_dashboard.reset_confirm_password', {
					'success':'NO',
					'isEnterMatchPass': True,
				})
			if  screen_status =='OLD_NEW_PASSWORD' and otp_valid_status and new == confirm :
				user_phone = request.session['mobile_no']
				user_phone = user_phone.replace("+", "")
				# _logger.info("=======change password block start for user id is : %s and user email Is : %s :",,user_phone )
				reset_user = request.env['res.partner'].sudo().search(['|',('phone','=',user_phone),('mobile','=',user_phone)])
				user = False
				if len(reset_user) == 1: 
					user = request.env['res.users'].sudo().search([('partner_id', '=',reset_user.id )])
				_logger.info("Password changed user object is : %s ", reset_user)
				if user  and new == confirm:
					# Reset the user's password
					_logger.info(" phone no. is : %s and new password : %s  and confirm password is : %s", user_phone , new , confirm)
					user.sudo().write({'password': confirm}) 
					# crear the session related password rester process here 
					request.session['loginstatus'] = None
					request.session['user_phone'] = None
					request.session['user_enter_opt'] = None
					request.session['sent_otp']=None
					request.session['user_id']=None
					response = http.request.render('client_vendor_dashboard.reset_confirm_password', {
						'success':'YES',
						'message': 'Password reset has been successfully',
					})
					return response
				else:
					return http.request.render('client_vendor_dashboard.reset_confirm_password', {
					'success':'NO',
					'message': 'Password Mismatch : failed',
					})
			else:
				message = 'Please contact to administrator : failed'
				return http.request.render('client_vendor_dashboard.reset_confirm_password', {
					'success':'NO',
					'message': message,
				})


	@http.route('/api/message/note', type='json', auth='public', methods=['POST'], csrf=False)
	# @http.route('/api/message/note', type='http', auth='public', csrf=False)
	def update_log_note(self):
		try:
			data = json.loads(request.httprequest.data)
			_logger.info("Received data in request body:", data)

			print("================================ data", data)
			partner_id = data.get('partner_id')
			partner_id = request.env['res.partner'].sudo().browse(int(partner_id))
			res_partner = request.env['res.partner'].sudo().search([('id', '=', partner_id.id)])
			user_id = request.env['res.users'].sudo().search([('partner_id', '=', res_partner.id)])
			record_id = data.get('record_id')
			model_name = data.get('model_name')
			file_attachment = data.get('file_attachment')
			img_attachment = data.get('img_attachment')
			note = data.get('note')
			file_data = file_attachment.read() if file_attachment else None
			img_data = img_attachment.read() if img_attachment else None
			if record_id and model_name and (note or file_data or img_data) :
				record = request.env[model_name].sudo().search([('id','=',record_id)],limit=1)
				record.with_user(user_id)._message_log(body=note)
			try:
				if file_data:
					index_content = 'application'
					file_record = request.env['ir.attachment'].with_user(user_id.id).sudo().create({
					'name': kw.get('file_attachment_name').strip(),
					'type': 'binary',
					'datas': file_data,
					'res_model': model_name,
					'res_id': record_id,
					'mimetype': kw.get('file_attachment_type').strip(),
					'index_content': index_content,
					})

				if img_data:
					index_content = 'image'
					img_record = request.env['ir.attachment'].with_user(user_id.id).sudo().create({
					'name': kw.get('img_attachment_name').strip(),
					'type': 'binary',
					'datas': img_data,
					'res_model': model_name,
					'res_id': record_id,
					'mimetype': kw.get('img_attachment_type').strip(),
					'index_content': index_content,
					})
			except Exception as e:
				_logger.error(f"Error creating ir.attachment record: {e}")
				pass
				
		except json.JSONDecodeError:
			return {'error': "Invalid JSON format."}, 400
		except Exception as e:
			request.env.cr.rollback() 
			# Catch any other exceptions and return a server error response
			return {'error': str(e)}, 500

	@http.route('/api/print_invoice', auth='public', methods=['GET'], website=False)
	# @http.route('/api/print_invoice', auth='public', website=False)
	def get_invoice_report(self, **kw):
		record_id = kw.get('record_id')
		model = kw.get('model')
		bill_name = kw.get('bill_name')
		
		# Check if the required parameters are present
		if not record_id or not model:
			return "Missing record_id or model parameter."
		
		# Generate the report for 'account.move' (Invoice)
		if model == 'account.move':
			record = request.env['account.move'].sudo().browse(int(record_id))
			if not record.exists():
				return "Invoice record not found."
			
			# Render the report and generate the PDF
			try:
				report_data = request.env['ir.actions.report'].sudo()._render_qweb_pdf('account.account_invoices', [record.id])[0]
				_logger.info(f"Generated invoice report for record {record_id}.")
				
				# Return the PDF as a response
				return request.make_response(
					report_data,
					headers=[
						('Content-Type', 'application/pdf'),
						('Content-Disposition', f'attachment; filename="{bill_name}_invoice_report.pdf"')
					]
				)
			except UserError as e:
				_logger.error(f"Error generating invoice report: {e}")
				return f"Error generating invoice report: {str(e)}"

		elif model == 'purchase.order':
			record = request.env['purchase.order'].sudo().browse(int(record_id))
			if not record.exists():
				return "Purchase Order record not found."
			
			# Render the report and generate the PDF
			try:
				report_data = request.env['ir.actions.report'].sudo()._render_qweb_pdf('purchase.report_purchaseorder', [record.id])[0]
				_logger.info(f"Generated purchase order report for record {record_id}.")
				
				# Return the PDF as a response
				return request.make_response(
					report_data,
					headers=[
						('Content-Type', 'application/pdf'),
						('Content-Disposition', f'attachment; filename="{bill_name}_purchase_order_report.pdf"')
					]
				)
			except UserError as e:
				_logger.error(f"Error generating purchase order report: {e}")
				return f"Error generating purchase order report: {str(e)}"
		
		return "Invalid model or parameters."