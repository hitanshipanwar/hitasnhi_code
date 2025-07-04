# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import http
from odoo.addons.web.controllers.main import Home
from odoo.http import request

class Home(Home):

	def _login_redirect(self, uid, redirect=None):
		""" Redirect regular users (employees) to the backend) and others to
		the frontend
		"""
		if not redirect and request.params.get('login_success'):
			if request.env['res.users'].browse(uid).has_group('base.group_user'):
				redirect = b'/web?' + request.httprequest.query_string
			else:
				if request.env.user.is_supplier == 'customer':
					redirect = '/dashboard'
				else:
					redirect = '/supplier/dashboard'
		return super()._login_redirect(uid, redirect=redirect)    

