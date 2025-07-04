# -*- coding: utf-8 -*-
import odoo
from odoo import http, _
from odoo import models, fields, api
from odoo.http import request
from datetime import datetime, date, time
from dateutil.relativedelta import relativedelta
from odoo.exceptions import ValidationError, UserError, AccessError
from werkzeug.wrappers import Response
import json
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
import mimetypes
import requests
_logger = logging.getLogger(__name__)
import base64
try:
	from base64 import encodebytes
except ImportError:
	from base64 import encodestring as encodebytes

import io 
import pytesseract
from pdf2image import convert_from_bytes
from PyPDF2 import PdfFileReader as PdfReader
from PyPDF2 import PdfFileReader
import textract
import os
import tempfile
from werkzeug.security import check_password_hash, generate_password_hash


class CustomVendorDashboard(http.Controller):

	# @http.route('/api/db/subscription/state', type='json', auth='public', methods=['POST'], csrf=False)
	@http.route('/api/db/subscription/state', type='http', auth='public', csrf=False)
	def get_subscription_state(self):
		_logger.info("========================== ")
		"""API to fetch subscription state by subscription_id."""
		try:
			data = json.loads(request.httprequest.data)
			url = data.get('url')
			if not url:
				return json.dumps({'error': 'URL ID is required.'})
			subscription_id = False
			_logger.info("==================== url %s" % url)
			subscription_ids = request.env['subscription.master'].sudo().search([('client_id.url', '=', url)])
			print('=======================subscription_ids=', subscription_ids)
			for subscription in subscription_ids:
				for service in subscription.subscription_plan_id.service_ids:
					if 'app' in (service.service_product_id.name or '').lower():
						subscription_id = subscription
						_logger.info("Subscription ID %s has a service with 'vendor' in its name." % subscription)

			_logger.info("===================subscription: %s" % subscription_id)
			_logger.info("===================subscription: %s" % subscription_id.state)
			if subscription_id:
				return json.dumps({'status':'success' ,'state': subscription_id.state})
			else:
				return json.dumps({'status':'failed', 'error': f'Subscription with ID {subscription_id} not found'})
		except Exception as e:
			return json.dumps({'error': str(e), 'message': 'Unexpected server error'})

	@http.route('/vendor/logout', auth='public', website=True)
	def dashboard_logout(self, url):
		_logger.info(" Client URL: %s" % url)
		request.session.logout()
		if 'logout_message' in request.session:
			del request.session['logout_message']
		
		response = werkzeug.utils.redirect(f'{url}/vendor/login')
		# response = werkzeug.utils.redirect(url)
		response.set_cookie('session_id', '', expires=0)
		response.set_cookie('csrf_token', '', expires=0)
		response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
		response.headers['Pragma'] = 'no-cache'
		response.headers['Expires'] = '0'
		
		# Set logout message in session (if needed)
		request.session['logout_message'] = 'You are successfully logged out'
		
		return response


	@http.route('/vendor', auth='public', website=True, csrf=False)
	def vendor_dashboard(self, db, partner_id, **kw):
		print("/vendor ----------------------------", kw)
		print("/vendor ----------------------------", partner_id)
		print("/vendor ----------------------------", db)

		base_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
		session_info = request.env['ir.http'].session_info()
		session_user_id = session_info.get('uid')
		session_token = kw.get('session_token')
		print("===============session_token", session_token)
		client_url = kw.get('client_url')
		client_id = request.env['res.client'].sudo().search([('url', '=', client_url)], limit=1)
		print("=====================================sahi hai yeah ================================", session_user_id)
		print("=====================================sahi hai yeah ================================", session_info)
		vendor_name = partner_id
		print("========vendor_name============",vendor_name)
		print("========client_url============",client_url)
		client_logo = client_id.client_logo
		_logger.info("client_id.url : %s" % client_url)
		
		result = []
		data = {
		'db': db,
		'session_token': session_token,
		'partner_id': partner_id,
		'kw': kw
		}
		response = requests.post(
			f"{client_url}/vendor/home", 
			json=data,
			headers={'Content-Type': 'application/json'}
		)
		_logger.error(f"Request failed with status code: {response.status_code}")
		_logger.error(f"Response text: {response.text}")
		result = response.json()
		_logger.error(f"Result: {result}")
			
		if result:
			# company_name = result.get('result', {}).get('company_name', [])
			company_name = result.get('result', {}).get('company_name', [])
			company_mobile = result.get('result', {}).get('company_mobile', [])
			company_email = result.get('result', {}).get('company_email', [])
			company_address = result.get('result', {}).get('company_address', [])
			email = result.get('result', {}).get('email', [])
			user_name = result.get('result', {}).get('user_name', [])
			user_image = result.get('result', {}).get('user_image', [])
			print("company_name **********************************", email)
			print("company_name **********************************", company_name)
			print("company_mobile **********************************", company_mobile)
			print("company_email **********************************", company_email)
			print("company_address **********************************", company_address)

			purchase_records = result.get('result', {}).get('purchase_records', [])
			print("purchase_records -----------------------", purchase_records)
			invoice_records = result.get('result', {}).get('invoice_records', [])
			print("invoice_records -----------------------", invoice_records)
			paid_invoice = result.get('result', {}).get('paid_invoice', [])
			print("paid_invoice -----------------------", paid_invoice)

			print("db **********************************", db)
			print("db **********************************", client_id.url)
			print("db **********************************", partner_id)

			return http.request.render('custom_vendor_dashboard.vendor_dashboard_home', {
				'billed_invoice': invoice_records,
				'paid_invoice': paid_invoice,
				'purchase_records': purchase_records,
				'invoice_records': invoice_records,
				'user': request.env.user,
				'base_url': base_url,
				'client_db': db,
				'partner_id': partner_id,
				'client_url': client_url,
				'client_logo': client_logo,
				'company_name': company_name,
				'company_mobile': company_mobile,
				'company_email': company_email,
				'company_address': company_address,
				'user_name': user_name,
				'user_image': user_image,
				'user_email': email,
			})
		else:
			return http.request.render('custom_vendor_dashboard.vendor_dashboard_not_found_page', {
				'billed_invoice': [],
				'paid_invoice': [],
				'purchase_records': [],
				'invoice_records': [],
				'user_name': user_name,
				'user_image': user_image,
				'user_email': email,
				'user': request.env.user,
				'partner_id': partner_id,
				'client_logo': client_logo,
				'company_name': company_name,
				'company_mobile': company_mobile,
				'company_email': company_email,
				'company_address': company_address,
			})

	# Vendor dashboard purchase controller start here 
	@http.route(['/vendor/purchase','/vendor/purchase/page/<int:page>','/vendor/purchase/fillter'], auth='public', website=True )
	def dashboard_purchase(self, page=1, per_page=50, loginstatus=None, **kw):
		print("/vendor/purchase ==========================", kw)
		print("/vendor/purchase ==========================", loginstatus)
		client_url = kw.get('client_url')
		partner_id = kw.get('partner_id')
		_logger.info(" Vendor Purchase login page client_url %s" % client_url)
		_logger.info(" Vendor Purchase login page partner_id %s" % partner_id)
		
		client_id = request.env['res.client'].sudo().search([('url', '=', client_url)])
		client_logo = client_id.client_logo
		
		if kw.get('page_no'):
			per_page = int(kw.get('page_no')) or 50
			
		data = {
		'db': False,
		'partner_id': partner_id,
		'login_success': True,
		'login_message': "You have successfully logged in",
		'per_page': per_page,
		'page': page,
		'kw': kw
		}
		print("data ============================", data)
		response = requests.post(
			f"{client_url}/vendor/home", 
			json=data,
			headers={'Content-Type': 'application/json'},
		)
		print("client_url =========================", client_url)
		print("response =========================", response)
		result = response.json()
		print("result =========================", result)
		if result:
			company_name = result.get('result', {}).get('company_name', [])
			company_mobile = result.get('result', {}).get('company_mobile', [])
			company_email = result.get('result', {}).get('company_email', [])
			company_address = result.get('result', {}).get('company_address', [])
			user_email = result.get('result', {}).get('email', "")
			user_name = result.get('result', {}).get('user_name', "")
			user_image = result.get('result', {}).get('user_image', "")
			if user_image and user_image.startswith("b'"):
				user_image = user_image[2:-1]

			purchase_records = result.get('result', {}).get('purchase_records', [])
			total_count = result.get('result', {}).get('total_po_orders', 0)
			print("total_count -----------------------", total_count)
			print("page -----------------------", page)
			print("per_page -----------------------", per_page)
			print("purchase_records -----------------------", purchase_records)
			pager = request.website.pager(url='/vendor/purchase', total=total_count, page=page, step=per_page, scope=5)
			print("pager ============================", pager)
			
			print("user_email ***********************", client_url)
			print("user_email ***********************", user_email)
			print("user_name ***********************", user_name)
			print("user_image ***********************", user_image)

			# # end sorting and filter logic
			return http.request.render('custom_vendor_dashboard.vendor_dashboard_purchase', {
				'purchase_records': purchase_records,
				'user': request.env.user,
				'login_status': True,
				'pager': pager,
				'page': page,
				'record_count': per_page,
				'client_db': request.env.cr.dbname,
				'partner_id': partner_id,
				'purchase_record_count': total_count,
				'client_url': client_url,
				'user_email': user_email,
				'client_logo': client_logo,
				'company_name': company_name,
				'company_mobile': company_mobile,
				'company_email': company_email,
				'company_address': company_address,
				'user_name': user_name,
				'user_image': user_image.replace(" ", "+") if user_image else "",
				# 'purchase_record_count':request.env['purchase.order'].sudo().search_count([('state', '=', 'purchase'),('partner_id', '=', vendor_name),('invoice_status', '!=', 'fully_billed')])
				# 'purchase_record_count':request.env['purchase.order'].sudo().search_count([('vendor_location', '=',vendor_name),('invoice_status','=','to invoice')])
			})
		else:
			return http.request.render('custom_vendor_dashboard.vendor_dashboard_not_found_page', {
				'billed_invoice': [],
				'paid_invoice': [],
				'purchase_records': [],
				'invoice_records': [],
				'user': request.env.user,
				'login_status': login_success,
				'client_logo': client_logo,
				'company_name': company_name,
				'company_mobile': company_mobile,
				'company_email': company_email,
				'company_address': company_address,
			})

	# vendor dashboard unpaid invoice controller start here
	@http.route(['/vendor/unpaidinvoice','/vendor/unpaidinvoice/page/<int:page>','/vendor/unpaidinvoice/fillter'], auth='public', website=True )
	def dashboard_unpaid_invoice(self, page=1, per_page=50, **kw):
		url = kw.get('client_url')
		partner_id = kw.get('partner_id')
		_logger.info(" Vendor Unpaid INV login page kw %s" % kw)
		_logger.info(" Vendor Unpaid INV login page client_url %s" % url)
		_logger.info(" Vendor Unpaid INV login page partner_id %s" % partner_id)
		
		client_id = request.env['res.client'].sudo().search([('url', '=', url)])
		client_logo = client_id.client_logo
		
		if kw.get('page_no'):
			per_page = int(kw.get('page_no')) or 50  

		result = []
		data = {
		'db': False,
		'partner_id': partner_id,
		'login_success': True,
		'login_message': "You have successfully logged in",
		'per_page': per_page,
		'page': page,
		'kw': kw
		}
		print("data ============================", data)
		response = requests.post(
			f"{url}/vendor/home", 
			json=data,
			headers={'Content-Type': 'application/json'},
			verify=False
		)
		print("url =========================", url)
		print("response =========================", response)
		result = response.json()
		print("result =========================", result)

		if result:

			company_name = result.get('result', {}).get('company_name', [])
			company_mobile = result.get('result', {}).get('company_mobile', [])
			company_email = result.get('result', {}).get('company_email', [])
			company_address = result.get('result', {}).get('company_address', [])
			user_email = result.get('result', {}).get('email', "")
			user_image = result.get('result', {}).get('user_image', "")
			user_name = result.get('result', {}).get('user_name', "")
			if user_image and user_image.startswith("b'"):
				user_image = user_image[2:-1]
			

			invoice_records = result.get('result', {}).get('invoice_records', [])
			print("invoice_records -----------------------", invoice_records)
			total_invoice_amount = result.get('result', {}).get('unpaid_invoice_total_amount', 0)
			total_count = result.get('result', {}).get('unpaid_inv_total_count', 0)
			print("total_count -----------------------", total_count)
			pager = request.website.pager(url='/vendor/unpaidinvoice', total=total_count, page=page, step=per_page, scope=5)
			print("pager ============================", pager)
			total_po_count = result.get('result', {}).get('total_po_orders', [])
		
			return http.request.render('custom_vendor_dashboard.vendor_dashboard_unpaid_invoice', {
				'billed_invoice': invoice_records,
				'user': request.env.user,
				'total_amount': total_invoice_amount,
				'pager': pager,
				'page':page,
				'record_count': per_page,
				'client_db': request.env.cr.dbname,
				'partner_id': partner_id,
				'purchase_record_count':total_po_count,
				'client_url': url,
				'user_email': user_email,
				'client_logo': client_logo,
				'company_name': company_name,
				'company_mobile': company_mobile,
				'company_email': company_email,
				'company_address': company_address,
				'user_name': user_name,
				'user_image': user_image.replace(" ", "+") if user_image else "",
				# 'purchase_record_count':request.env['purchase.order'].sudo().search_count([('vendor_location', '=',vendor_name),('invoice_status','=','to invoice')])
			})
		else:
			return http.request.render('custom_vendor_dashboard.vendor_dashboard_not_found_page', {
				'billed_invoice': [],
				'paid_invoice': [],
				'purchase_records': [],
				'invoice_records': [],
				'user': request.env.user,
				'login': user_email,
				'client_logo': client_logo,
				'company_name': company_name,
				'company_mobile': company_mobile,
				'company_email': company_email,
				'company_address': company_address,
			})

	# vendor dashboard paid invoice controller start here
	@http.route(['/vendor/paidinvoice','/vendor/paidinvoice/page/<int:page>','/vendor/paidinvoice/fillter'], auth='public', website=True )
	# def dashboard_paid_invoice(self, page=1, per_page=50, loginstatus=None, email=None, password=None, partner_id=None, client_url=None, user_name=None, user_image=None, **kw):
	def dashboard_paid_invoice(self, page=1, per_page=50, **kw):
		url = kw.get('client_url')
		partner_id = kw.get('partner_id')
		_logger.info(" Vendor Paid INV login page kw %s" % kw)
		_logger.info(" Vendor Paid INV login page client_url %s" % url)
		_logger.info(" Vendor Paid INV login page partner_id %s" % partner_id)
		
		client_id = request.env['res.client'].sudo().search([('url', '=', url)])
		client_logo = client_id.client_logo
		
		if kw.get('page_no'):
			per_page = int(kw.get('page_no')) or 50

		print("per_page >>>>>>>>>>>>>>>>>>>>>>>>>>>>", per_page)
		print("page >>>>>>>>>>>>>>>>>>>>>>>>>>>>", page)

		data = {
		'db': False,
		'partner_id': partner_id,
		'login_success': True,
		'login_message': "You have successfully logged in",
		'per_page': per_page,
		'page': page,
		'kw': kw
		}
		print("data ============================", data)
		response = requests.post(
			f"{url}/vendor/home", 
			json=data,
			headers={'Content-Type': 'application/json'},
			verify=False
		)
		result = response.json()

		if result:

			company_name = result.get('result', {}).get('company_name', [])
			company_mobile = result.get('result', {}).get('company_mobile', [])
			company_email = result.get('result', {}).get('company_email', [])
			company_address = result.get('result', {}).get('company_address', [])
			user_email = result.get('result', {}).get('email', "")
			user_image = result.get('result', {}).get('user_image', "")
			user_name = result.get('result', {}).get('user_name', "")
			if user_image and user_image.startswith("b'"):
				user_image = user_image[2:-1]

			paid_invoice = result.get('result', {}).get('paid_invoice', [])
			total_invoice_amount = result.get('result', {}).get('paid_invocie_total_invoice_amount', 0)
			print("paid_invoice -----------------------", paid_invoice)
			total_count = result.get('result', {}).get('paid_inv_total_count', 0)
			total_po_count = result.get('result', {}).get('total_po_orders', 0)
			pager = request.website.pager(url='/vendor/paidinvoice', total=total_count, page=page, step=per_page, scope=5)
			
			return http.request.render('custom_vendor_dashboard.vendor_dashboard_paid_invoice', {
				# 'paid_invoice': invoice_records_paid,
				'paid_invoice': paid_invoice,
				'total_amount': total_invoice_amount,
				'user': request.env.user,
				'pager': pager,
				'page': page, 
				'record_count': per_page,
				'client_db': request.env.cr.dbname,
				'partner_id': partner_id,
				'purchase_record_count': total_po_count,
				'client_url': url,
				'user_email': user_email,
				'client_logo': client_logo,
				'company_name': company_name,
				'company_mobile': company_mobile,
				'company_email': company_email,
				'company_address': company_address,
				'user_name': user_name,
				'user_image': user_image.replace(" ", "+") if user_image else "",
				# 'purchase_record_count':request.env['purchase.order'].sudo().search_count([('state', '=', 'purchase'),('partner_id', '=', vendor_name),('invoice_status', '!=', 'fully_billed')])
				# 'purchase_record_count':request.env['purchase.order'].sudo().search_count([('vendor_location', '=',vendor_name),('invoice_status','=','to invoice')])
			})
		else:
			return http.request.render('custom_vendor_dashboard.vendor_dashboard_not_found_page', {
				'billed_invoice': [],
				'paid_invoice': [],
				'purchase_records': [],
				'invoice_records': [],
				'user': request.env.user,
				'login': user_email,
				'client_logo': client_logo,
				'company_name': company_name,
				'company_mobile': company_mobile,
				'company_email': company_email,
				'company_address': company_address,
			})

	# vendor dashboard search home Vendor Dashboard controller start here
	@http.route('/vendor/search', auth='public',csrf=False , website=True)
	def dashboard_search_invoice_purchase(self, partner_id=None, client_url=None, **kw):
		
		client_id = request.env['res.client'].sudo().search([('url', '=', client_url)])
		client_logo = client_id.client_logo
		url = client_url
		name = request.httprequest.form.get('query')
		if name:
			name = name.strip()
		
		result = []
		data = {
		'db': False,
		'partner_id': partner_id,
		'login_success': True,
		'login_message': "You have successfully logged in",
		'kw': kw,
		'name': name
		}
		print("data ******************", data)
		response = requests.post(
			f"{url}/vendor/home", 
			json=data,
			headers={'Content-Type': 'application/json'},
			verify=False
		)
		print("url *******************", url)
		print("response **********************", response)
		result = response.json()
		print("result ***********************", result)

		if result:
			company_name = result.get('result', {}).get('company_name', [])
			company_mobile = result.get('result', {}).get('company_mobile', [])
			company_email = result.get('result', {}).get('company_email', [])
			company_address = result.get('result', {}).get('company_address', [])
			user_email = result.get('result', {}).get('email', "")
			user_image = result.get('result', {}).get('user_image', "")
			user_name = result.get('result', {}).get('user_name', "")
			if user_image and user_image.startswith("b'"):
				user_image = user_image[2:-1]

			invoice_records_billed = result.get('result', {}).get('search_invoice_records_billed', [])
			invoice_records_paid = result.get('result', {}).get('search_invoice_records_paid', [])
			purchase_records = result.get('result', {}).get('search_purchase_records', [])
			purchase_records_new = result.get('result', {}).get('search_purchase_records_new', [])
			invoice_records = result.get('result', {}).get('search_invoice_records', [])

			print("invoice_records_billed *****************************", invoice_records_billed)
			print("invoice_records_paid *************************", invoice_records_paid)
			print("purchase_records ***********************************", purchase_records)
			print("purchase_records_new *****************************", purchase_records_new)
			print("invoice_records ********************************", invoice_records)

			return http.request.render('custom_vendor_dashboard.vendor_dashboard_home_search_template', {
				'billed_invoice': invoice_records_billed,
				'paid_invoice': invoice_records_paid,
				'purchase_records': purchase_records,
				'purchase_records_new': purchase_records_new,
				'invoice_records': invoice_records,
				'user': request.env.user,
				'name': name,
				'client_db': request.env.cr.dbname,
				'partner_id': partner_id,
				'client_url': client_url,
				'user_email': user_email,
				'client_logo': client_logo,
				'company_name': company_name,
				'company_mobile': company_mobile,
				'company_email': company_email,
				'company_address': company_address,
				'user_name': user_name,
				'user_image': user_image.replace(" ", "+") if user_image else "",
			})
		else:
			return http.request.render('custom_vendor_dashboard.vendor_dashboard_not_found_page', {
				'billed_invoice': [],
				'paid_invoice': [],
				'purchase_records': [],
				'invoice_records': [],
				'user': request.env.user,
				'login': user_email,
				'client_logo': client_logo,
				'company_name': company_name,
				'company_mobile': company_mobile,
				'company_email': company_email,
				'company_address': company_address,
			})

	# Vendor dashboard purchase order search controller start here 
	@http.route('/vendor/purchase/search', auth='public' , csrf=False  , website=True)
	def dashboard_purchase_search(self, partner_id=None, client_url=None, **kw):
		client_id = request.env['res.client'].sudo().search([('url', '=', client_url)])
		client_logo = client_id.client_logo
		url = client_url
		name = request.httprequest.form.get('query')
		if name:
			name = name.strip()

		purchase_records = []
		result = []
		data = {
		'db': False,
		'partner_id': partner_id,
		'login_success': True,
		'login_message': "You have successfully logged in",
		'kw': kw,
		'name': name
		}
		print("data ******************", data)
		response = requests.post(
			f"{url}/vendor/home", 
			json=data,
			headers={'Content-Type': 'application/json'}
		)
		print("url *******************", url)
		print("response **********************", response)
		result = response.json()
		print("result ***********************", result)

		if result:
			company_name = result.get('result', {}).get('company_name', [])
			company_mobile = result.get('result', {}).get('company_mobile', [])
			company_email = result.get('result', {}).get('company_email', [])
			company_address = result.get('result', {}).get('company_address', [])
			user_email = result.get('result', {}).get('email', "")
			user_image = result.get('result', {}).get('user_image', "")
			user_name = result.get('result', {}).get('user_name', "")
			if user_image and user_image.startswith("b'"):
				user_image = user_image[2:-1]

			purchase_records = result.get('result', {}).get('search_purchase_records', [])

			return http.request.render('custom_vendor_dashboard.vendor_dashboard_purchase_search_template', {
				'purchase_records': purchase_records,
				'user': request.env.user,
				'name': name,
				'client_db': request.env.cr.dbname,
				'partner_id': partner_id,
				'client_url': client_url,
				'user_email': user_email,
				'client_logo': client_logo,
				'company_name': company_name,
				'company_mobile': company_mobile,
				'company_email': company_email,
				'company_address': company_address,
				'user_name': user_name,
				'user_image': user_image.replace(" ", "+") if user_image else "",
			})
		else:
			return http.request.render('custom_vendor_dashboard.vendor_dashboard_not_found_page', {
				'billed_invoice': [],
				'paid_invoice': [],
				'purchase_records': [],
				'invoice_records': [],
				'user': request.env.user,
				'password': user_password,
				'client_logo': client_logo,
				'company_name': company_name,
				'company_mobile': company_mobile,
				'company_email': company_email,
				'company_address': company_address,
			})


	# vendor dashboard search unpaid invoice controller start here
	@http.route('/vendor/unpaidinvoice/search', auth='public' , csrf=False  , website=True)
	def dashboard_unpaid_invoice_search(self, partner_id=None, client_url=None, **kw):
		client_id = request.env['res.client'].sudo().search([('url', '=', client_url)])
		client_logo = client_id.client_logo
		url = client_url
		search_data = request.httprequest.form.get('query')
		if search_data:
			search_data = search_data.strip()     

		result = []
		data = {
		'db': False,
		'partner_id': partner_id,
		'login_success': True,
		'login_message': "You have successfully logged in",
		'kw': kw,
		'search_data': search_data
		}
		print("data ******************", data)
		response = requests.post(
			f"{url}/vendor/home", 
			json=data,
			headers={'Content-Type': 'application/json'},
			verify=False
		)
		print("url *******************", url)
		print("response **********************", response)
		result = response.json()
		print("result ***********************", result)


		if result:
			company_name = result.get('result', {}).get('company_name', [])
			company_mobile = result.get('result', {}).get('company_mobile', [])
			company_email = result.get('result', {}).get('company_email', [])
			company_address = result.get('result', {}).get('company_address', [])
			user_email = result.get('result', {}).get('email', "")
			user_image = result.get('result', {}).get('user_image', "")
			user_name = result.get('result', {}).get('user_name', "")
			if user_image and user_image.startswith("b'"):
				user_image = user_image[2:-1]

			invoice_records_billed = result.get('result', {}).get('unpaidinv_search_invoice_records_billed', [])
			total_invoice_amount = result.get('result', {}).get('unpaid_total_invoice_amount', 0)
			total_po_orders = result.get('result', {}).get('total_po_orders', [])

			return http.request.render('custom_vendor_dashboard.vendor_dashboard_unpaid_invoice_search', {
				'billed_invoice': invoice_records_billed,
				'total_invoice_amount': total_invoice_amount,
				'user': request.env.user,
				'search_data': search_data,
				'client_db': request.env.cr.dbname,
				'partner_id': partner_id,
				'client_url': client_url,
				'purchase_record_count': total_po_orders,
				'user_email': user_email,
				'client_logo': client_logo,
				'company_name': company_name,
				'company_mobile': company_mobile,
				'company_email': company_email,
				'company_address': company_address,
				'user_name': user_name,
				'user_image': user_image.replace(" ", "+") if user_image else "",
				# 'purchase_record_count':request.env['purchase.order'].sudo().search_count([('vendor_location', '=',vendor_name),('invoice_status','=','to invoice')])
			})
		else:
			return http.request.render('custom_vendor_dashboard.vendor_dashboard_not_found_page', {
				'billed_invoice': [],
				'paid_invoice': [],
				'purchase_records': [],
				'invoice_records': [],
				'user': request.env.user,
				'login': user_email,
				'client_logo': client_logo,
				'company_name': company_name,
				'company_mobile': company_mobile,
				'company_email': company_email,
				'company_address': company_address,
			})


	# vendor dashboard paid invoice search controller start here
	@http.route('/vendor/paidinvoice/search', auth='public', csrf=False  , website=True)
	def dashboard_paid_invoice_search(self, partner_id=None, client_url=None, **kw):
		client_id = request.env['res.client'].sudo().search([('url', '=', client_url)])
		client_logo = client_id.client_logo
		url = client_url
		search_data = request.httprequest.form.get('query')
		if search_data:
			search_data = search_data.strip()
		
		result = []
		data = {
		'db': False,
		'partner_id': partner_id,
		'login_success': True,
		'login_message': "You have successfully logged in",
		'kw': kw,
		'search_data': search_data
		}
		print("data ******************", data)
		response = requests.post(
			f"{url}/vendor/home", 
			json=data,
			headers={'Content-Type': 'application/json'},
			verify=False
		)
		print("url *******************", url)
		print("response **********************", response)
		result = response.json()
		print("result ***********************", result)

		if result:
			company_name = result.get('result', {}).get('company_name', [])
			company_mobile = result.get('result', {}).get('company_mobile', [])
			company_email = result.get('result', {}).get('company_email', [])
			company_address = result.get('result', {}).get('company_address', [])
			user_email = result.get('result', {}).get('email', "")
			user_image = result.get('result', {}).get('user_image', "")
			user_name = result.get('result', {}).get('user_name', "")
			if user_image and user_image.startswith("b'"):
				user_image = user_image[2:-1]
			
			invoice_records_paid = result.get('result', {}).get('paidinv_search_invoice_records_paid', [])
			total_invoice_amount = result.get('result', {}).get('paidinv_search_total_invoice_amount', [])
			total_po_orders = result.get('result', {}).get('total_po_orders', [])


			return http.request.render('custom_vendor_dashboard.vendor_dashboard_paid_invoice_search', {
				'paid_invoice': invoice_records_paid,
				'total_amount': total_invoice_amount,
				'user': request.env.user,
				'search_data': search_data,
				'purchase_record_count': total_po_orders,
				'client_db': request.env.cr.dbname,
				'partner_id': partner_id,
				'client_url': client_url,
				'user_email': user_email,
				'client_logo': client_logo,
				'company_name': company_name,
				'company_mobile': company_mobile,
				'company_email': company_email,
				'company_address': company_address,
				'user_name': user_name,
				'user_image': user_image.replace(" ", "+") if user_image else "",
				# 'purchase_record_count':request.env['purchase.order'].sudo().search_count([('state', '=', 'purchase'),('partner_id', '=', vendor_name),('invoice_status', '!=', 'fully_billed')])
				# 'purchase_record_count':request.env['purchase.order'].sudo().search_count([('vendor_location', '=',vendor_name),('invoice_status','=','to invoice')])
			})
		else:
			return http.request.render('custom_vendor_dashboard.vendor_dashboard_not_found_page', {
				'billed_invoice': [],
				'paid_invoice': [],
				'purchase_records': [],
				'invoice_records': [],
				'user': request.env.user,
				'login': user_email,
				'client_logo': client_logo,
				'company_name': company_name,
				'company_mobile': company_mobile,
				'company_email': company_email,
				'company_address': company_address,
			})

	# If user enter incorrect URL then render not found page
	@http.route('/<path:route>', type='http', auth="user", website=True ,csrf=False )
	def catchall(self, route, **kwargs):
		partner_id = kwargs.get('partner_id')
		client_url = kwargs.get('client_url')
		vendor_name = partner_id
		client_id = request.env['res.client'].sudo().search([('url', '=', client_url)])
		client_logo = client_id.client_logo
		data = {
		'db': False,
		'partner_id': partner_id,
		'login_success': True,
		'login_message': "You have successfully logged in",
		'kw': kwargs,
		}
		print("data ******************", data)
		response = requests.post(
			f"{client_url}/vendor/home", 
			json=data,
			headers={'Content-Type': 'application/json'},
			verify=False
		)
		print("url *******************", client_url)
		print("response **********************", response)
		result = response.json()
		print("result ***********************", result)

		company_name = result.get('result', {}).get('company_name', [])
		company_mobile = result.get('result', {}).get('company_mobile', [])
		company_email = result.get('result', {}).get('company_email', [])
		company_address = result.get('result', {}).get('company_address', [])
		user_email = result.get('result', {}).get('email', "")

		# if login_success and request.env.user  and request.env.user.has_group('base.group_portal') and not request.env.user.has_group('base.group_public') and not request.env.user.has_group('base.group_user'):
		purchase_records = request.env['purchase.order'].sudo().search([('state', '=', 'purchase'),('partner_id', '=', vendor_name),('invoice_status', '!=', 'fully_billed')])
		invoice_records_billed = request.env['account.move'].sudo().search(['&',('partner_id','=',vendor_name),('payment_state','in',['not_paid']),('state','in',['posted'])])
		invoice_records_paid = request.env['account.move'].sudo().search(['&',('partner_id','=',vendor_name),('payment_state','in',['paid','in_payment']),('state','in',['posted'])])
		invoice_records = request.env['account.move'].sudo().search(['&',('partner_id','=',vendor_name),('state','in',['posted','draft'])])
		return http.request.render('custom_vendor_dashboard.vendor_dashboard_not_found_page', {
			'billed_invoice': invoice_records_billed,
			'paid_invoice': invoice_records_paid,
			'purchase_records': purchase_records,
			'invoice_records': invoice_records,
			'user': request.env.user,
			'client_logo': client_logo,
			'company_name': company_name,
			'company_mobile': company_mobile,
			'company_email': company_email,
			'company_address': company_address,
		})
		

	# create invoice template start here
	@http.route(['/vendor/create/invoice', '/vendor/create/invoice/page/<int:page>'], auth='public', methods=['GET'], website=True)
	def create_invoice(self, partner_id=None, client_url=None, **kw):
		_logger.info(" ===============called /vendor/create/invoice: %s", kw)
		_logger.info(" ===============called /vendor/create/invoice: %s", partner_id)
		_logger.info(" ===============called /vendor/create/invoice: %s", client_url)
		vendor_name = partner_id
		client_id = request.env['res.client'].sudo().search([('url', '=', client_url)])
		client_logo = client_id.client_logo
		
		url = client_url
		_logger.info("========================= url: %s", url)
		record_id = kw.get('purchase_id')
		_logger.info("===record_id=========== %s" , record_id)
		purchase_name = kw.get('purchase_name')
		_logger.info("=purchase_name======== %s" , purchase_name)
		purchase_status = kw.get('purchase_status')
		_logger.info("=purchase_status============= %s" , purchase_status)
		
		result = []
		data = {
		'db': False,
		'partner_id': partner_id,
		'kw': kw,
		'record_id': record_id,
		'purchase_name': purchase_name,
		'purchase_status': purchase_status,
		}
		_logger.info("data ****************** %s", data)
		_logger.info("url ******************* %s", url)
		response = requests.post(
			f"{url}/api/vendor/create/invoice", 
			json=data,
			headers={'Content-Type': 'application/json'},
			verify=False
		)
		_logger.info("response ********************** %s", response)
		result = response.json()
		_logger.info("result *********************** %s", result)

		if result:

			record_data = result.get('result', {}).get('record', [])
			record = record_data[0]

			company_name = record.get('result', {}).get('company_name', [])
			print("=======================company_name", company_name)
			company_mobile = record.get('company_mobile', [])
			company_email = record.get('company_email', [])
			company_address = record.get('company_address', [])
			user_image = record.get('user_image', "")
			user_name = record.get('user_name', "")
			user_email = record.get('user_email', "")
			if user_image and user_image.startswith("b'"):
				user_image = user_image[2:-1]

			total_amount = result.get('result', {}).get('total_amount', 0)
			payment_term = result.get('result', {}).get('payment_term_id', [])
			order_lines = record.get('order_lines', [])
			_logger.info("order_lines =========================== %s", order_lines)
			_logger.info("record =========================== %s", record)
			_logger.info("total_amount =========================== %s", total_amount)
			_logger.info("record =========================== %s", record['id'])
			_logger.info("record =========================== %s", record['return_default_due_date'])
			_logger.info("record =========================== %s", record['messag_ids'])
			print("===========================partner_id", partner_id)
			print("===========================partner_id", url)
			return http.request.render('custom_vendor_dashboard.create_invoice_template', {
				'record': record,
				'amount': round(total_amount,2),
				'message_ids': record['messag_ids'],
				'user': request.env.user,
				'payment_term' : payment_term,
				'created_from': kw.get('created_from'),
				'client_db': request.env.cr.dbname,
				'partner_id': partner_id,
				'client_url': url,
				'user_email': user_email,
				'client_logo': client_logo,
				'company_name': company_name,
				'company_mobile': company_mobile,
				'company_email': company_email,
				'company_address': company_address,
				'order_lines': order_lines,
				'user_image': user_image.replace(" ", "+") if user_image else "",
				'user_name': user_name,
			})
		else:
			return http.request.render('custom_vendor_dashboard.vendor_dashboard_not_found_page', {
				'billed_invoice': [],
				'paid_invoice': [],
				'purchase_records': [],
				'invoice_records': [],
				'user': request.env.user,
				'login': user_email,
				'client_logo': client_logo,
				'company_name': company_name,
				'company_mobile': company_mobile,
				'company_email': company_email,
				'company_address': company_address,
			})


	#Cancel draft payment controller.
	# @http.route('/cancel/payment/draft', auth='public', website=True, csrf=False)
	@http.route('/cancel/payment/draft', auth='public', methods=['POST'], website=True, csrf=False)
	def cancel_vendor_payment_draft(self, **kw):
		_logger.info("We are in cancel draft payment controller.")
		record_id = kw.get('invoiceId')
		_logger.info(f"Received record ID: {record_id}")
		success_status = 0
		message = "Error occurred"  # Default error message

		if record_id:
			record = http.request.env['account.move'].with_user(2).sudo().search([('id', '=', int(record_id))], limit=1)
			try:
				if record:
					record.unlink()
					success_status = 1
					message = "Bill cancel successfully."
				else:
					message = "Invoice record not found."
			except Exception as e:
				_logger.error(f"Error while cancel bill: {e}")
				message = f"Error while cancel bill: {str(e)}"

		response = {
			'error': not success_status,
			'message': message
		}
		return http.request.make_response(json.dumps(response), headers={'Content-Type': 'application/json'})


	# open existing invoice
	@http.route('/vendor/open/invoice', auth='public', methods=['GET'], website=True)
	def open_invoice(self, **kw):
		vendor_name = kw.get('partner_id')
		partner_id = kw.get('partner_id')
		login_success = request.session.get('loginstatus')

		client_id = request.env['res.client'].sudo().search([('user_id', '=', request.env.uid)])
		url = client_id.url
		client_logo = client_id.client_logo

		response = request.env['ir.http'].session_info()
		session_user_id = response.get('uid')
		result = []
		if session_user_id:
			data = {
			'db': False,
			'partner_id': partner_id,
			'login_success': True,
			'login_message': "You have successfully logged in",
			'kw': kw,
			}
			print("data ******************", data)
			response = requests.post(
				f"{url}/vendor/home", 
				json=data,
				headers={'Content-Type': 'application/json'},
				verify=False
			)
			print("url *******************", url)
			print("response **********************", response)
			result = response.json()
			print("result ***********************", result)

		company_name = result.get('result', {}).get('company_name', [])
		company_mobile = result.get('result', {}).get('company_mobile', [])
		company_email = result.get('result', {}).get('company_email', [])
		company_address = result.get('result', {}).get('company_address', [])
		user_email = result.get('result', {}).get('user_email', [])

		# fetching url parameter
		invoice_id = kw.get('invoice_id')
		bill_name = kw.get('bill_name')
		invoice_status = kw.get('invoice_status')
		if login_success and request.env.user  and request.env.user.has_group('base.group_portal') and not request.env.user.has_group('base.group_public') and not request.env.user.has_group('base.group_user'):
			record = request.env['account.move'].sudo().search(['&',('id','=',invoice_id),('payment_state','in',[invoice_status])],limit=1)

			total_amount = 0
			for amount in record.invoice_line_ids:
				total_amount = total_amount + amount.price_subtotal
		
			request.session['invoice_url'] = request.httprequest.url

			# fetch ship or bill to address
			bill_to_partner_id=None
			ship_to_partner_id=None
			if record.invoice_purchase_order:
				purchase_record = request.env['purchase.order'].sudo().search([('name','=',record.invoice_purchase_order)],limit=1)
				if purchase_record.dest_address_id:
					ship_to_partner_id = purchase_record.dest_address_id
				elif not purchase_record.dest_address_id and purchase_record.partner_id.same_ship_add:
					ship_to_partner_id = record.partner_id
				else:
					ship_to_partner_id = None

			if record.partner_id:
				bill_to_partner_id = record.partner_id
			else:
				bill_to_partner_id = None

			return http.request.render('custom_vendor_dashboard.open_invoice_template', {
				'record': record,
				'partner_id': partner_id,
				'amount': round(total_amount,2),
				'message_ids': record.message_ids.filtered(lambda r: r.author_id == request.env.user.partner_id).sorted(lambda r: r.date, reverse=True),
				'user': request.env.user,
				'purchase_record_count':request.env['purchase.order'].sudo().search_count([('state', '=', 'purchase'),('partner_id', '=', vendor_name),('invoice_status', '!=', 'fully_billed')]),
				'bill_address' : bill_to_partner_id,
				'ship_address' : ship_to_partner_id,
				'company_name': company_name,
				'company_mobile': company_mobile,
				'company_email': company_email,
				'company_address': company_address,
			})
		else:
			return http.request.render('custom_vendor_dashboard.vendor_dashboard_not_found_page', {
				'billed_invoice': [],
				'paid_invoice': [],
				'purchase_records': [],
				'invoice_records': [],
				'user': request.env.user,
				'partner_id': partner_id,
				'company_name': company_name,
				'company_mobile': company_mobile,
				'company_email': company_email,
				'company_address': company_address,
			})

	# start work on open invoice (Print invoice or upload log message and file upload controller)
	@http.route('/message/note', auth='public', website=True , csrf=False)
	def update_log_note(self, **kw):
		print("----------------------------------------", kw)
		_logger.info(" we are in message not controller =============.")
		try:
			req = request.params
			record_id = kw.get('record_id')
			if record_id:
				record_id = int(record_id)
			model_name = kw.get('model')
			note = kw.get('note')
			file_attachment = request.httprequest.files.get('file_attachment')
			img_attachment = request.httprequest.files.get('img_attachment')
			client_url = kw.get('client_url')
			partner_id = kw.get('partner_id')
			print("======================", client_url)
			
			data = {
				'record_id': record_id,
				'model_name': model_name,
				'note': note,
				'client_url': client_url,
				'partner_id': partner_id,
				'file_attachment': file_attachment,
				'img_attachment': img_attachment,
			}
			print("data ******************", data)
			response = requests.post(
				f"{client_url}/api/message/note", 
				json=data,
				headers={'Content-Type': 'application/json'},
				verify=False
			)
			print("url *******************", url)
			print("response **********************", response)
			result = response.json()
			print("result ***********************", result)
			if response.status_code == 200:
				result = {
					"success": "Note API controller hit, and log note written successfully.",
					"model": model_name,
				}
				# Returning the response with success message and note
				json_data = json.dumps(result)
				return Response(json_data, content_type='application/json;charset=utf-8')
			else:
				return Response(
					json.dumps({"success": False, "message": "Failed to post note data"}),
					content_type="application/json;charset=utf-8"
				)
		except Exception as e:
			_logger.error(f"Error in updating log note: {e}")
			return Response(
				json.dumps({"success": False, "message": f"Error: {str(e)}"}),
				content_type="application/json;charset=utf-8"
			)

	@http.route('/print_invoice', auth='public', methods=['GET'], website=True)
	def print_invoice(self, **kw):
		_logger.error("We are in the report download section of the invoice.")
		
		# Retrieve parameters from the GET request
		record_id = kw.get('record_id')
		bill_name = kw.get('bill_name')
		model = kw.get('model').strip()
		client_db_url = kw.get('client_url').strip()
		url = ''
		url = f"{client_db_url}/api/print_invoice"
		try:
			response = requests.get(url, params={
				'record_id': record_id,
				'model': model,
				'bill_name': bill_name
			}, verify=False)
			print("==================response", response)
			if response.status_code == 200:
				report_data = response.content
				_logger.info("Received report data successfully from the client DB.")
				
				return request.make_response(
					report_data,
					headers=[
						('Content-Type', 'application/pdf'),
						('Content-Disposition', f'attachment; filename="{bill_name}_report.pdf"')
					]
				)
			else:
				_logger.error(f"Failed to retrieve report from client DB. Status code: {response.status_code}")
				return "Failed to download the report from client database."
		
		except Exception as e:
			_logger.error(f"Error while fetching report from client DB: {e}")
			return "Error while downloading the report."



	# change password after login controller start here 
	@http.route(['/vendor/password/current/change','/vendor/password/current/changed'], auth='public', website=True, csrf=False)
	# @http.route(['/vendor/password/current/change','/vendor/password/current/changed'], auth='public', website=True, csrf=False , methods=['POST','GET'] )
	def password_change_after_login(self, **kw):
		vendor_name = kw.get('partner_id')
		partner_id = kw.get('partner_id')

		client_id = request.env['res.client'].sudo().search([('user_id', '=', request.env.uid)])
		url = client_id.url
		client_logo = client_id.client_logo

		result = []
		# if session_user_id:
		data = {
		'db': False,
		'partner_id': partner_id,
		'login_success': True,
		'login_message': "You have successfully logged in",
		'kw': kw,
		}
		print("data ******************", data)
		response = requests.post(
			f"{url}/vendor/home", 
			json=data,
			headers={'Content-Type': 'application/json'},
			verify=False
		)
		print("url *******************", url)
		print("response **********************", response)
		result = response.json()
		print("result ***********************", result)

		company_name = result.get('result', {}).get('company_name', [])
		company_mobile = result.get('result', {}).get('company_mobile', [])
		company_email = result.get('result', {}).get('company_email', [])
		company_address = result.get('result', {}).get('company_address', [])
		user_email = result.get('result', {}).get('user_email', [])

		purchase_records = request.env['purchase.order'].sudo().search([('state', '=', 'purchase'),('partner_id', '=', vendor_name),('invoice_status', '!=', 'fully_billed')])
		# purchase_records = request.env['purchase.order'].sudo().search([('vendor_location', '=',vendor_name),('invoice_status','=','to invoice')])
		message = ""       
		if kw.get('reset_password') is not None:
			_logger.info("======current user enter password is : %s : ", kw.get('reset_password'))
			# after changed password
			message = 'Password has been changed successfully.'
			if request.env.user  and request.env.user.has_group('base.group_portal') and not request.env.user.has_group('base.group_public') and not request.env.user.has_group('base.group_user'):
				user = request.env['res.users'].sudo().browse(request.env.user.id)
				if user and kw.get('reset_password') is not None and kw.get('reset_password'):
					changed_password = kw.get('reset_password')
					# Reset the user's password
					user.sudo().write({'password': changed_password}) 
					message = 'Password has been changed successfully.'
					# crear the login status session 
					request.session['loginstatus'] = None
					return http.request.render('custom_vendor_dashboard.change_password_template', {
						'user': request.env.user,
						'success':'YES',
						'message': message,
						'purchase_records': purchase_records,
						'company_name': company_name,
						'company_mobile': company_mobile,
						'company_email': company_email,
						'company_address': company_address,
					})
				else:
					message = 'Password has been not changed due to some reason.'
					return http.request.render('custom_vendor_dashboard.change_password_template', {
						'user': request.env.user,
						'success':'NO',
						'message': message,
						'purchase_records': purchase_records,
						'company_name': company_name,
						'company_mobile': company_mobile,
						'company_email': company_email,
						'company_address': company_address,
					})
		if kw.get('reset_password') is None:
			_logger.info("======is none user enter password is : %s : ", kw.get('reset_password'))
			if request.env.user  and request.env.user.has_group('base.group_portal') and not request.env.user.has_group('base.group_public') and not request.env.user.has_group('base.group_user'):
				return http.request.render('custom_vendor_dashboard.change_password_template', {
					'user': request.env.user,
					'purchase_records': purchase_records,
					'company_name': company_name,
					'company_mobile': company_mobile,
					'company_email': company_email,
					'company_address': company_address,
				})
			else:
				return http.request.render('custom_vendor_dashboard.vendor_dashboard_not_found_page', {
					'billed_invoice': [],
					'paid_invoice': [],
					'purchase_records': [],
					'invoice_records': [],
					'user': request.env.user,
					'company_name': company_name,
					'company_mobile': company_mobile,
					'company_email': company_email,
					'company_address': company_address,
					
				})
	# change password after login controller end here 

	# start controller for manage email address
	@http.route('/vendor/manage/email', type='http', website=True , csrf=False ,auth="public")
	# @http.route('/vendor/manage/email', type='http', website=True ,methods=['POST','GET'], csrf=False ,auth="public")
	def manage_email_address(self,redirect=None , **kw):
		_logger.info("===========we are in manage email addess controller ========")
	   
		alert_script = """
		<script>
			alert("Manage email address functionality work in Progress.");
			window.location.href = '/vendor/login';
		</script>
		"""
		return alert_script

	# start submit draft payment bill or invoice controller
	@http.route('/submit/payment/draft', auth='public', website=True, csrf=False)
	# @http.route('/submit/payment/draft', auth='public', methods=['POST'], website=True, csrf=False)
	def submit_vendor_payment_draft(self, **kw):
		_logger.info("We are in submit draft payment controller.")
		record_id = kw.get('invoiceId')
		_logger.info(f"Received record ID: {record_id}")
		success_status = 0
		message = "Error occurred"  # Default error message

		if record_id:
			record = http.request.env['account.move'].with_user(2).sudo().search([('id', '=', int(record_id))], limit=1)
			try:
				# Search for the record and post the invoice
				if record:
					record.action_post()
					record.send_to_bill_com()
					success_status = 1
					message = "Bill created successfully."
				else:
					message = "Invoice record not found."
			except Exception as e:
				_logger.error(f"Error while submitting create bill: {e}")
				message = f"Error while submitting create bill: {str(e)}"

		response = {
			'error': not success_status,
			'message': message
		}
		return http.request.make_response(json.dumps(response), headers={'Content-Type': 'application/json'})


	# start submit payment bill or invoice controller
	@http.route('/submit/payment', auth='public', website=True , csrf=False)
	# @http.route('/submit/payment', auth='public', methods=['POST'], website=True , csrf=False)
	def submit_vendor_payment(self, **kw):
		_logger.info(" we are in submit payment controller =============.%s" % kw)
		url = kw.get('client_url')
		partner_id = kw.get('partner_id')
		client_id = request.env['res.client'].sudo().search([('url', '=', url)])
		db = request.env.cr.dbname

		req = request.params
		record_id = kw.get('record_id')
		if record_id:
			record_id = int(record_id)
		model_name = kw.get('model')
		bill_number = kw.get('bill_number')
		total_amount = kw.get('initial_amount')
		calculated_amount = kw.get('calculate_amount')
		total_percentage = kw.get('percentage')
		# selected_total_percentage = kw.get('selectedPercentage')
		selected_total_percentage = kw.get('percentage')
		due_date = kw.get('dueDate')
		payment_attachment_name = kw.get('payment_attachment_name').strip()
		payment_attachment_type = kw.get('payment_attachment_type').strip()
		print("===========due_date--------------------------- " , due_date)

		_logger.info("current id: %s : name : %s bill : %s and  percentage : %s and initial amount : %s : calcuate amount : %s ",record_id,model_name,bill_number,total_percentage, total_amount, calculated_amount)
		if total_percentage:
			percentage = int(total_percentage.replace("%", ""))

		if selected_total_percentage:
			selected_percentage = int(selected_total_percentage.replace("%", ""))
		payment_attachment = request.httprequest.files.get('payment_attachment')
		payment_file_data = payment_attachment.read() if payment_attachment else None
		if payment_file_data:
			payment_file_data = base64.b64encode(payment_file_data).decode('utf-8')

	   
		result = []
		data = {
		'db': False,
		'partner_id': partner_id,
		'record_id': record_id,
		'model_name': model_name,
		'bill_number': bill_number,
		'total_amount': total_amount,
		'calculated_amount': calculated_amount,
		'total_percentage': total_percentage,
		'selected_total_percentage': selected_total_percentage,
		'due_date': due_date,
		'payment_file_data': payment_file_data,
		'selected_percentage': selected_percentage,
		'payment_attachment_type': payment_attachment_type,
		'payment_attachment_name': payment_attachment_name,
		}
		print("data ******************", data)
		print("url *******************", url)
		response = requests.post(
			f"{url}/api/submit/payment", 
			json=data,
			headers={'Content-Type': 'application/json'},
			verify=False
		)
		print("response **********************", response)
		result = response.json()
		print("result ***********************", result)
		if result:
			response = json.dumps({
			'error': False,
			'message': 'Bill Create Successfully.',
			'client_db': request.env.cr.dbname,
			'partner_id': partner_id,
			'client_url': url,
			})
			print("===============response========iffff==========" , response)
			return response
		else:
			response = json.dumps({
			'error': True,
			'message': message
			})
			print("===============response=======elseee===========" , response)
			return response

	# Vendor dashboard setting controller start here 
	@http.route(['/vendor/setting/email'], auth='public', website=True)
	def dashboard_setting_email(self, url, partner_id):
		print("==========calling /vendor/setting/email =============", url)
		print("==========calling /vendor/setting/email =============", partner_id)
		
		redirect_url = f'{url}/api/vendor/setting/email?partner_id={partner_id}'
		print("==========calling /vendor/setting/email =============", redirect_url)
		return werkzeug.utils.redirect(redirect_url)
		

	# @http.route('/vendor/check/invoice/duplicate', type='http', auth='public', website=True, csrf=False)
	@http.route('/vendor/check/invoice/duplicate', type='http', auth='public', website=True, methods=['POST'], csrf=False)
	def check_invoice_duplicate(self, **kw):
		print("/vendor/check/invoice/duplicate **********************************", kw)

		url = kw.get('client_url')
		partner_id = kw.get('partner_id')
		client_id = request.env['res.client'].sudo().search([('url', '=', url)])
		db = request.env.cr.dbname
		base_url = client_id.url

		invoice_no = kw.get('invoice_no')
		record_id = kw.get('record_id')
		selected_per = kw.get('percentage')
		uploaded_invoice_amount = kw.get('invoice_amount')
		po_amount = kw.get('po_amount')
		calculate_amount = kw.get('calculate_amount')

		result = []
		data = {
		'db': False,
		'partner_id': partner_id,
		'kw': kw,
		'invoice_no': invoice_no,
		'record_id': record_id,
		'selected_per': selected_per,
		'uploaded_invoice_amount': uploaded_invoice_amount,
		'po_amount': po_amount,
		'calculate_amount': calculate_amount,
		}
		print("data ******************", data)
		response = requests.post(
			f"{url}/create/vendor/check/invoice/duplicate", 
			json=data,
			headers={'Content-Type': 'application/json'},
			verify=False
		)
		print("url *******************", url)
		print("response **********************", response)
		result = response.json()
		print("result ***********************", result['result'])
		if result:
			return request.make_response(json.dumps(result['result']), headers={'Content-Type': 'application/json'})
		else:
			return request.make_response(json.dumps({'error': 'Purchase order not found'}), headers={'Content-Type': 'application/json'})
		return request.make_response(json.dumps({'error': 'Invalid parameters'}), headers={'Content-Type': 'application/json'})

	# @http.route('/ocr/upload', type='http', auth='public', website=True , methods=['POST'], csrf=False)
	# def ocr_upload(self, **kwargs):
	# 	file = request.httprequest.files.get('file')
	# 	if file:
	# 		try:
	# 			# Read file bytes
	# 			file_bytes = file.read()
	# 			# Check if the file is a valid PDF
	# 			file_stream = io.BytesIO(file_bytes)
	# 			pdf_bytes = file_bytes
	# 			# pdf = PdfFileReader(file_stream)
	# 			pdf = PdfReader(file_stream)
	# 			if pdf.isEncrypted:
	# 				return 'The uploaded PDF is encrypted and cannot be processed.'
	# 			if pdf.getNumPages() == 0:
	# 				return 'The uploaded PDF has no pages.'
				
	# 			# Convert the uploaded PDF to images
	# 			images = convert_from_bytes(file_bytes)
	# 			temp_dir = tempfile.mkdtemp()
	# 			# Create a temporary file to save the PDF bytes
	# 			with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_pdf:
	# 				temp_pdf.write(pdf_bytes)
	# 				temp_pdf_path = temp_pdf.name
	# 			text = ''
	# 			invoice_no = ''
	# 			amount = ''
	# 			for i, image in enumerate(images):
	# 				filename = 'temp.png'
	# 				file_path = os.path.join(temp_dir, filename)
	# 				# image_name = f"{temp_dir}_{i + 1}.png"  # Temporary image file name
	# 				image.save(file_path, 'PNG')
	# 				# Perform OCR on each image
	# 				# text += pytesseract.image_to_string(image)
	# 				text += textract.process(temp_pdf_path).decode('utf-8')
	# 				_logger.info("================text===============text : %s : ", text)
	# 				invoice_no = self.extract_invoice_number(text)
	# 				_logger.info("===============================invoice_no1: %s : ", invoice_no)
	# 				amount =  self.extract_total_amount(text)
	# 				_logger.info("===============================amount: %s : ", amount)
	
	# 				if not invoice_no:
	# 					text += pytesseract.image_to_string(image)
	# 					invoice_no = self.extract_invoice_number(text)
	# 					_logger.info("===============================invoice_no1: %s : ", invoice_no)

	# 				if not amount:
	# 					text += pytesseract.image_to_string(image)
	# 					amount =  self.extract_total_amount(text)
	# 			# return invoice_no,amount
	# 			return json.dumps({'invoice_no': invoice_no, 'amount': amount})

	# 		except Exception as e:
	# 			return f"Error during OCR processing: {str(e)}"
	# 	return 'No file uploaded'

	# @http.route('/ocr/upload', type='http', auth='public', website=True, csrf=False)
	@http.route('/ocr/upload', type='http', auth='public', website=True, methods=['POST'], csrf=False)
	def ocr_upload(self, **kwargs):
		_logger.info("####################ocr_upload")
		file = request.httprequest.files.get('file')
		_logger.info("Uploaded file: %s", file)

		if file:
			try:
				# Read file bytes
				file_bytes = file.read()
				# Check if the file is a valid PDF
				file_stream = io.BytesIO(file_bytes)
				pdf = PdfReader(file_stream)  # Update for new PyPDF2 API
				_logger.info("====================== PDF Object: %s", pdf)

				# Check for encryption and page count
				if pdf.isEncrypted:  # Use is_encrypted instead of isEncrypted
					_logger.warning("The uploaded PDF is encrypted and cannot be processed.")
					return json.dumps({'error': 'The uploaded PDF is encrypted and cannot be processed.'})

				if len(pdf.pages) == 0:  # Check for number of pages using pdf.pages
					_logger.warning("The uploaded PDF has no pages.")
					return json.dumps({'error': 'The uploaded PDF has no pages.'})

				_logger.info("PDF has %d pages", len(pdf.pages))

				# Convert the uploaded PDF to images
				images = convert_from_bytes(file_bytes)
				_logger.info("Number of images generated from PDF: %d", len(images))

				temp_dir = tempfile.mkdtemp()
				_logger.info("Temporary directory created: %s", temp_dir)

				# Create a temporary file to save the PDF bytes
				with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_pdf:
					temp_pdf.write(file_bytes)
					temp_pdf_path = temp_pdf.name

				text = ''
				invoice_no = ''
				amount = ''
				
				for i, image in enumerate(images):
					_logger.info("Processing image %d", i)
					filename = f'temp_{i + 1}.png'  # Use a unique name for each image
					file_path = os.path.join(temp_dir, filename)
					image.save(file_path, 'PNG')

					# Perform OCR on the image and the PDF text
					text += textract.process(temp_pdf_path).decode('utf-8')
					_logger.info("Extracted text from PDF: %s", text)

					# Extract invoice number and amount
					invoice_no = self.extract_invoice_number(text)
					amount = self.extract_total_amount(text)

					_logger.info("Extracted invoice number: %s", invoice_no)
					_logger.info("Extracted amount: %s", amount)

					if not invoice_no:
						print("zzzzzzzzzzzzzzzzzzzzzzzzz", invoice_no)
						text += pytesseract.image_to_string(image)
						print("zzzzzzzzzzzzzzzzzzzzzzzzz", text)
						invoice_no = self.extract_invoice_number(text)
						_logger.info("Attempted to extract invoice number from image: %s", invoice_no)

					if not amount:
						text += pytesseract.image_to_string(image)
						amount = self.extract_total_amount(text)

				return json.dumps({'invoice_no': invoice_no, 'amount': amount})

			except Exception as e:
				_logger.error("Error during OCR processing: %s", str(e))
				return json.dumps({'error': f"Error during OCR processing: {str(e)}"})

		return json.dumps({'error': 'No file uploaded'})

	
	def extract_total_amount(self,text):
		# Define the regex patterns        
		amount1 = re.compile(r'BALANCE DUE\s*[:\s]*\$?(\d{1,3}(?:,\d{3})*\.\d{2})', re.IGNORECASE)
		amount2 = re.compile(r'You paid CA\$(\d{1,3}(?:,\d{3})*\.\d{2})', re.IGNORECASE)
		amount3 = re.compile(r'Invoice amount\s*[:\s]*CA\$(\d{1,3}(?:,\d{3})*\.\d{2})', re.IGNORECASE)
		amount4 = re.compile(r'Total\s*[:\s]*CA\$(\d{1,3}(?:,\d{3})*\.\d{2})', re.IGNORECASE)
		amount5A = re.compile(r'Total(?:\s+[\d,]+\.\d{2})*\s+([\d,]+\.\d{2})', re.IGNORECASE | re.DOTALL)
		amount5B = re.compile(r'Total\s*[\s\S]*?Unit\s+price\s*\d+\.\d{2}\s*[\s\S]*?Total\s+price\s*\d+\.\d{2}\s*[\s\S]*?(\d{1,3}(?:,\d{3})*\.\d{2})\s*$', re.IGNORECASE)
		amount5 = re.compile(r'Total\s*[:\s]*([\d,]+\.\d{2})', re.IGNORECASE) # Matches "Total 172.20"
		amount6 = re.compile(r'Total\s*USD\s*[:\s]*([\d,]+\.\d{2})', re.IGNORECASE) # Matches "TOTAL USD 10,000.00"
		amount7 = re.compile(r'Total\s*:\s*([\d,]+\.\d{2})', re.IGNORECASE) # Matches "Total: 301.70"
		amount8 = re.compile(r'Total\s*[:\s]*\$\s*(\d{1,3}(?:,\d{3})*\.\d{2})', re.IGNORECASE)
		amount9 = re.compile(r'\*\*\* INVOICE TOTAL \*\*\*\s*([\d,]+\.\d{2})', re.IGNORECASE)
		amount10 = re.compile(r'\$\d+\.\d{2}', re.IGNORECASE | re.DOTALL)
		amount11 = re.compile(r'\$([\d,]+\.\d{2})', re.IGNORECASE)
		amount12 = re.compile(r'Grand Total(?:\s+[\d,]+\.\d{2})*\s+([\d,]+\.\d{2})', re.IGNORECASE | re.DOTALL)

		# Try matching each pattern
		for pattern in [amount12,amount1,amount2,amount3,amount4,amount5A,amount5B,amount5,amount6,amount7,amount8,amount9,amount11]:
			match = pattern.search(text)
			try:
				if match and match.group(1):
					return match.group(1)
				elif match:
					return match.group()
			except:
				return match.group()
		last_match = None
		for match in amount10.finditer(text):
			last_match = match.group()
		if last_match:
			return last_match.lstrip('$')
		return None

	def extract_invoice_number(self,text):
		# Define the regex patterns
		invoice_pattern = re.compile(r'\bINVOICE\s*Invoice\s*Date\s*Page\s*1\s*(\d+)\s*\d{1,2}/\d{1,2}/\d{4}', re.IGNORECASE)
		pattern1 = re.compile(r'Invoice\s+number\s+(\w+-\w+)', re.IGNORECASE)  # Matches "Invoice number E719C39C-0002"
		pattern2 = re.compile(r'Invoice\s*no\.?\s*:\s*(\w+-\w+)', re.IGNORECASE)  # Matches "Invoice no.: E719C39C-0002"
		pattern3 = re.compile(r'INVOICE\s+NUMBER:\s+(\w+-\w+)', re.IGNORECASE)  # Matches "INVOICE NUMBER: E719C39C-0002"
		pattern4 = re.compile(r'INV/\d{4}/\d{5}')  # Matches "INV/2024/12345"
		pattern5 = re.compile(r'INVOICE\s+(\d+)', re.IGNORECASE)  # Matches "INVOICE 12345"
		pattern6 = re.compile(r'INVOICE NUMBER:\s*(\S+)', re.IGNORECASE)  # Matches "INVOICE NUMBER: SC26754401"
		pattern_generic = re.compile(r'(?:Invoice\s*number|INVOICE\s*NO:|Invoice\s*no\.|INVOICE\s*no\.|INVOICE\s*#:)\s*([^\s]+)', re.IGNORECASE)
		pattern_generic = re.compile(r'(?:Invoice\snumber|INVOICE\sNO:|Invoice\sno.|INVOICE\sno.|INVOICE\s#:)\s([^\s]+)', re.IGNORECASE)
		pattern7 = re.compile(r'Invoice no.\s*\n(\d+)', re.IGNORECASE)
		pattern8 = re.compile(r'\d{1,2}/\d{1,2}/\d{4}\s*[\w\s]*Invoice\s*#\s*(\d+)', re.IGNORECASE)
		pattern9 = re.compile(r'SI\d+', re.IGNORECASE)
		
		# Try matching each pattern
		for pattern in [pattern9, invoice_pattern, pattern1, pattern2, pattern3, pattern4, pattern5, pattern6, pattern_generic, pattern7, pattern8]:
			match = pattern.search(text)
			try:
				if match and match.group(1):
					return match.group(1)
				elif match:
					return match.group()
			except:
				return match.group()
		return None

	@http.route(['/api/render/client'], auth='public', website=True)
	def api_render_client(self, menu, url, partner_id):
		if menu == 'reset_password':
			redirect_url = (f'{url}/vendor/setting/resetpassword?partner_id={partner_id}')
			return werkzeug.utils.redirect(redirect_url)