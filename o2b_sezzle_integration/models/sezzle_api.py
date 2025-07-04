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

from odoo import models, fields, api
from odoo.addons.o2b_sezzle_integration import utils as sezzle_utils
from datetime import datetime, timedelta
from odoo.exceptions import UserError, ValidationError
import requests
import csv
import io
import logging
_logger = logging.getLogger(__name__)


# Inheriting bank statement line for sezzle id field
class BankStatementLineInherit(models.Model):
    _inherit = 'account.bank.statement.line'

    sezzle_order_id = fields.Char("Sezzle Order Id")

class SezzleConnect(models.Model):
    _name = 'sezzle.settings'
    _description = 'Sezzle'

    name = fields.Char("Name")
    provider = fields.Selection(string="Provider", selection=[('sezzle', 'Sezzle')], default='sezzle')
    company_id = fields.Many2one("res.company", string="Company",  default=lambda self: self.env.company, required=True)
    payment_journal_id = fields.Many2one("account.journal", string="Payment Journal", required=True)
    public_key = fields.Char("Public Key")
    private_key = fields.Char("Private Key")
    access_token = fields.Char("Access Token")
    environment = fields.Selection([
        ('sandbox', 'Sandbox'),
        ('production', 'Production')
    ], default='production')
    start_date = fields.Date(string="From Date")
    end_date = fields.Date(string="To Date")
    offset = fields.Char(string="Offset")
    currency_code = fields.Char(string="Currency Code")
    access_token_create_date = fields.Datetime("Token Created At")
    access_token_expire_date = fields.Datetime("Token Expire At")
    is_token_expired = fields.Boolean("Is Token Expired", compute="_compute_is_token_expired", default=True)
    
    def _compute_is_token_expired(self):
        for rec in self:
            if rec.access_token_expire_date and rec.access_token_expire_date < datetime.now():
                rec.is_token_expired = True
            else:
                rec.is_token_expired = False


    def set_access_token(self):
        result = self._generate_access_token(self.public_key, self.private_key, self.environment)
        if result:
            self.access_token = result.get("token")
            self.access_token_create_date = datetime.now()
            raw_date = result.get("expiration_date")
            if raw_date:
                cleaned_date = raw_date.rstrip('Z')
                if '.' in cleaned_date:
                    date_part, micro = cleaned_date.split('.')
                    micro = micro[:6]  # truncate to 6 digits
                    cleaned_date = f"{date_part}.{micro}"
                    fmt = "%Y-%m-%dT%H:%M:%S.%f"
                else:
                    fmt = "%Y-%m-%dT%H:%M:%S"
                self.access_token_expire_date = datetime.strptime(cleaned_date, fmt)

    def _generate_access_token(self, public_key=None, private_key=None, environment=None):
        """
        Generates Sezzle access token using provided public and private keys.
        """
        base_url = sezzle_utils.get_base_url(environment if environment else self.environment)
        api_version = sezzle_utils.get_api_version()
        url = f"{base_url}/{api_version}/authentication"
        payload = {
            "private_key": private_key if private_key else self.private_key,
            "public_key": public_key if public_key else self.public_key
        }
        headers = {
            "Content-Type": "application/json"
        }

        try:
            response = requests.post(url, json=payload, headers=headers)
            response.raise_for_status()
            result = response.json()

            token = result.get("token")
            if token:
                _logger.info("Sezzle access token generated successfully.")
                return result
            else:
                _logger.error("Sezzle token missing in response: %s", result)
                return False

        except requests.exceptions.RequestException as e:
            _logger.error("Sezzle token generation failed: %s", e)
            return False
    
    @api.model
    def get_sezzle_config_detail(self, sezzle_config_name):
        domain = []
        if sezzle_config_name:
            domain = [('name', '=', sezzle_config_name)]
        return self.env['sezzle.settings'].search(domain, limit=1)
    
    @api.model
    def _prepare_sezzle_token_vals(self, data):
            sezzle_update_vals = {}
            if data:
                sezzle_update_vals['access_token'] = data.get("token")
                sezzle_update_vals['access_token_create_date'] = datetime.now()
                raw_date = data.get("expiration_date")
                if raw_date:
                    cleaned_date = raw_date.rstrip('Z')
                    if '.' in cleaned_date:
                        date_part, micro = cleaned_date.split('.')
                        micro = micro[:6]
                        cleaned_date = f"{date_part}.{micro}"
                        fmt = "%Y-%m-%dT%H:%M:%S.%f"
                    else:
                        fmt = "%Y-%m-%dT%H:%M:%S"
                    sezzle_update_vals['access_token_expire_date'] = datetime.strptime(cleaned_date, fmt)
            return sezzle_update_vals
        

    def get_sezzle_settlement_uuids(self, start_date, end_date, offset, currency_code, sezzle_config_name, retry=True):
        """
        Fetch settlement summaries from Sezzle and return a list of UUIDs.

        :param start_date: Start date (YYYY-MM-DD)
        :param end_date: End date (YYYY-MM-DD)
        :param offset: Offset max limit 20
        :param currency_code: ISO-4217 currency code
        :return: List of UUID strings
        """
        base_url = sezzle_utils.get_base_url(self.environment)
        api_version = sezzle_utils.get_api_version()
        url = f"{base_url}/{api_version}/settlements/summaries?start-date={start_date}"
        if end_date:
            url += f"&end-date={end_date}"
        if offset:
            url += f"&end-date={offset}"
        if currency_code:
            url += f"&end-date={currency_code}"
        
        sezzle_config = self.get_sezzle_config_detail(sezzle_config_name)
        if sezzle_config and sezzle_config.access_token_expire_date and sezzle_config.access_token_expire_date < datetime.now():
            result = sezzle_config._generate_access_token(sezzle_config.public_key, sezzle_config.private_key, sezzle_config.environment)
            sezzle_update_vals = self._prepare_sezzle_token_vals(result)
            sezzle_config.write(sezzle_update_vals)

        headers = {
            'Authorization': sezzle_config.access_token if sezzle_config else '',
            'Content-Type': 'application/json',
        }

        try:
            response = requests.get(url, headers=headers, timeout=30)
            if response.status_code == 401 and retry:
                _logger.warning("Access token expired. Regenerating token...")
                result = sezzle_config._generate_access_token(sezzle_config.public_key, sezzle_config.private_key, sezzle_config.environment)
                sezzle_update_vals = self._prepare_sezzle_token_vals(result)
                sezzle_config.write(sezzle_update_vals)
                return self.get_sezzle_settlement_uuids(start_date, end_date, offset, currency_code, sezzle_config_name, retry=False)
            if response.status_code != 200:
                raise UserError("Failed to fetch Sezzle settlements.")
            
            response.raise_for_status()
            data = response.json()

            # Extract UUIDs
            uuids = [entry.get("uuid") for entry in data if entry.get("uuid")]
            return uuids

        except requests.exceptions.RequestException as e:
            _logger.error(f"Sezzle API error while fetching settlements: {e}")
            return []

    def fetch_transaction_details(self, settlement_id, sezzle_config_name, retry=True):
        if not settlement_id:
            raise UserError("Failed to fetch Sezzle settlement id.")
        
        base_url = sezzle_utils.get_base_url(self.environment)
        api_version = sezzle_utils.get_api_version()
        url = f"{base_url}/{api_version}/settlements/details/{settlement_id}"
        sezzle_config = self.get_sezzle_config_detail(sezzle_config_name)
        if sezzle_config and sezzle_config.access_token_expire_date and sezzle_config.access_token_expire_date < datetime.now():
            result = sezzle_config._generate_access_token(sezzle_config.public_key, sezzle_config.private_key, sezzle_config.environment)
            sezzle_update_vals = self._prepare_sezzle_token_vals(result)
            sezzle_config.write(sezzle_update_vals)
        headers = {
            'Authorization': sezzle_config.access_token if sezzle_config else ''
        }

        response = requests.get(url, headers=headers)
        if response.status_code == 401 and retry:
            _logger.warning("Access token expired. Regenerating token...")
            result = sezzle_config._generate_access_token(sezzle_config.public_key, sezzle_config.private_key, sezzle_config.environment)
            sezzle_update_vals = self._prepare_sezzle_token_vals(result)
            sezzle_config.write(sezzle_update_vals)
            return self.fetch_transaction_details(settlement_id, sezzle_config_name, retry=False)
        if response.status_code != 200:
            raise UserError("Failed to fetch Sezzle settlement details.")

        csv_data = response.text
        csv_lines = list(csv.reader(io.StringIO(csv_data)))
        summary_line = csv_lines[1]
        transaction_lines = csv_lines[3:]
        result = []

        for row in transaction_lines:
            tx_type = row[0]
            if tx_type not in ["CAPTURE", "REFUND"]:
                continue

            order_uuid = row[4]
            customer_order_id = row[5]
            external_ref = row[6]
            sezzle_order_id = row[12]

            amount = float(row[8] or row[9] or 0.0)
            if amount == 0.0:
                continue

            event_date = row[3][:10] if row[3] else fields.Date.today().isoformat()

            vals = {
                'payment_ref': f"{order_uuid}",
                'amount': amount,
                'date': event_date,
                'ref': external_ref,
                'sezzle_order_id': sezzle_order_id,
                'company_id': sezzle_config.company_id.id,
                'journal_id': sezzle_config.payment_journal_id.id,
            }
            result.append(vals)

        return result

    def create_bank_statement_line_via_settlement(self):
        if self.start_date and self.end_date:
            days_in_selected_date = (self.end_date - self.start_date).days + 1
            if days_in_selected_date > 31:
                raise ValidationError("You can import data for a maximum range of 31 days. Please adjust the selected dates.")

        settlement_ids = self.get_sezzle_settlement_uuids(self.start_date, self.end_date, self.offset, self.currency_code, self.name)
        statement_line = self.env['account.bank.statement.line']
        for settlement_id in settlement_ids:
            if settlement_id:
                transactions = self.fetch_transaction_details(settlement_id, self.name)
                for line in transactions:
                    existing_rec = statement_line.search([('sezzle_order_id', '=', line.get('sezzle_order_id'))])
                    for rec in existing_rec:
                        if not rec or rec.amount != line.get('amount'):
                            statement_line_ids = self.env['account.bank.statement.line'].create(line)
        return True
    
    def get_date_range(self):
        end_date = fields.Date.today()
        start_date = end_date - timedelta(days=3)
        return {
            'start_date': start_date,
            'end_date': end_date,
        }

    @api.model
    def sezzle_transaction_create_via_cron(self, start_date=None, end_date=None, offset=None, currency_code=None):
        if not start_date or not end_date:
            start_end_date = self.get_date_range()
            start_date = start_end_date.get('start_date')
            end_date = start_end_date.get('end_date')
        
        sezzle_config_ids = self.env['sezzle.settings'].search([])
        for sezzle_config in sezzle_config_ids:
            if not sezzle_config:
                return
            
            settlement_ids = self.get_sezzle_settlement_uuids(start_date, end_date, offset, currency_code, sezzle_config.name)
            statement_line = self.env['account.bank.statement.line']
            for settlement_id in settlement_ids:
                if settlement_id:
                    transactions = self.fetch_transaction_details(settlement_id, sezzle_config.name)
                    for line in transactions:
                        for rec in existing_rec:
                            if not rec or rec.amount != line.get('amount'):
                                statement_line_ids = self.env['account.bank.statement.line'].create(line)
        return True