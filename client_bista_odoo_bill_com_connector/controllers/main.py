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
from odoo import http
from odoo.http import request
import json
import logging

_logger = logging.getLogger(__name__)

class SubscriptionAPI(http.Controller):
	@http.route('/api/bill/subscription/state', type='json', auth='public', methods=['POST'], csrf=False)
	def get_bill_subscription_state(self):
		"""API to fetch subscription state by subscription_id."""
		try:
			data = json.loads(request.httprequest.data)
			state = data.get('state')
			username = data.get('user')
			if not state:
				return {'error': 'State is required.'}

			# Search for the subscription
			bill_com = request.env['bill.com.config'].sudo().search([('bill_com_user_name', '=', username)], limit=1)
			if bill_com:
				bill_com.write({'state': state})
				return {'statu': 'success'}
			else:
				return {'error': f'Bill.Com config of user {username} not found'}
		except Exception as e:
			return {'error': str(e), 'message': 'Unexpected server error'}
