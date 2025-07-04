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
from odoo import models, fields, api
import json
import logging

_logger = logging.getLogger(__name__)

class ProviderWebhookController(http.Controller):

	@http.route('/create_statements', type='json', auth='public', methods=['POST'], csrf=False)
	def create_statements(self):
		try:
			data = json.loads(request.httprequest.data)
			authorize_login = data.get('authorize_login')
			# _logger.info("Received data in request body:", data)
			
			bank_statement_id = request.env['authorize.bank.statement.config'].sudo().search([('provider', '=', 'authorize'),('authorize_login', '=', authorize_login)], limit=1)
			if bank_statement_id:
				bank_statement_id.last_update = data.get('last_update')
				bank_statement_id.next_update = data.get('next_update')
			journal = bank_statement_id.journal_id
			
			partner_name = f"{data.get('first_name')} {data.get('last_name')}"
			existing_line = request.env['account.bank.statement.line'].sudo().search([
				('authorize_transaction_identifier', '=', data.get('transaction_id'))
			], limit=1)
			
			if not existing_line and float(data.get('amount')) != 0:
				request.env['account.bank.statement.line'].sudo().create({
					'payment_ref': partner_name,
					'date': data.get('date'),
					'ref': data.get('ref'),
					'name': data.get('payment_ref'),
					'amount': float(data.get('amount')),
					'journal_id': journal.id,
					'company_id': bank_statement_id.company_id.id,
					'authorize_transaction_identifier': data.get('transaction_id')
				})
				return {'status': 'success'}, 200
			elif not existing_line.is_reconciled and not existing_line.to_check and float(data.get('amount')) != 0:
				request.env['account.bank.statement.line'].sudo().write({
					'payment_ref': partner_name,
					'date': data.get('date'),
					'ref': data.get('ref'),
					'name': data.get('payment_ref'),
					'amount': float(data.get('amount')),
					'journal_id': journal.id,
					'company_id': bank_statement_id.company_id.id,
					'authorize_transaction_identifier': data.get('transaction_id')
				})
				return {'status': 'success'}, 200

		except json.JSONDecodeError:
			return {'error': "Invalid JSON format."}, 400
		except Exception as e:
			request.env.cr.rollback() 
			# Catch any other exceptions and return a server error response
			return {'error': str(e)}, 500