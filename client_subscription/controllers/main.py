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
from odoo import http, tools
from odoo.http import request, route
import json
import logging

_logger = logging.getLogger(__name__)

class ClientSystemParameterController(http.Controller):

	# @http.route('/api/update_system_parameter', type='json', auth='public', methods=['POST'], csrf=False)
	@http.route('/api/update_system_parameter', type='http', auth='public', csrf=False)
	def update_system_parameter(self):
		try:
			data = json.loads(request.httprequest.data)
			value = data.get('value')
			url = data.get('url')
			_logger.info("Subscription ID: %s" % value)
			_logger.info("Host URL: %s" % url)
			if url:
				param_key = 'client_subscription.host_db_url'
				request.env['ir.config_parameter'].sudo().set_param(param_key, url)

			if value:
				request.env['ir.config_parameter'].sudo().create({
					'key': f'subscription_id - {value}',
					'value': value
				})
			return json.dumps({"success": True, "message": "System Parameter updated successfully."})
		except Exception as e:
			return json.dumps({"success": False, "message": f"Error: {str(e)}"})
