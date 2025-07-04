# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
import base64
import json
import re
import logging
import phonenumbers
from markupsafe import Markup
from mistralai import Mistral
import textwrap
from odoo import http
from odoo.http import request, Response
from difflib import SequenceMatcher
# from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager
from ...nalios_3cx_full.controllers.main_3cx import Main3CX

import logging
_logger = logging.getLogger(__name__)


class Main3CXCustom(Main3CX):

    def _get_message_data(self, data):
        _logger.info("=== 3CX _get_message_data Extended ===")
        details_key = data.get('type', '').lower()
        details = data.get(details_key, '')
        msg = (
            f"Subject: {data.get('subject', '')}\n"
            f"Date: {data.get('date', '')}\n"
            f"Call Type: {data.get('type', '')}\n"
            f"Entity: {data.get('entitytype', '')}\n"
            f"Agent Name: {data.get('agentname', '')}\n"
            f"Agent Phone: {data.get('agent', '')}\n"
            f"Details: {details}\n"
            f"Transcription: {data.get('transcription', '')}\n"
            f"Recording URL: {data.get('recording_url', '')}\n"
        )
        return msg

    # @http.route('/3cx/call/log', methods=["POST"], csrf=False, type="json", auth="public")
    # def _3cx_log_call(self):
    #     _logger.info("=== 3CX Call Log API Triggered Extended ===")

    #     if not self._is_3cx_authenticated():
    #         return self._unauthorized()

    #     data = self._load_json_data()
    #     _logger.info("=== 3CX Call Log data ===: %s", data)
    #     if not data:
    #         return self._bad_request()

    #     _logger.info("=== 3CX Call company ===: %s", int(data.get('company')))
    #     company_id = request.env['res.company'].sudo().browse(int(data.get('company')))
    #     _logger.info("=== 3CX Call company ===: %s", company_id)
    #     number = data.get('phone')
    #     if not number:
    #         return self._bad_request()
    #     number = self._sanitize_number(number)

    #     partner = None
    #     partner = request.env['res.partner'].sudo().search([
    #         ('company_id', '=', company_id.id),
    #         '|', '|', '|',
    #         ('mobile_format', 'ilike', str(number)),
    #         ('mobile', 'ilike', str(number)),
    #         ('phone_format', 'ilike', str(number)),
    #         ('phone', 'ilike', str(number))
    #     ], limit=1)

    #     if not partner and number and number.isdigit():
    #         partner = request.env['res.partner'].sudo().create({
    #             'name': 'New contact from number: ' + number,
    #             'phone': number,
    #             'company_id': company_id.id,
    #         })
    #         _logger.info("Step 1 Created new partner: %s", partner.id)

    #     transcription = data.get('transcription', '')
    #     recording_url = data.get('recording_url')

    #     # -- Load Mistral provider & model
    #     mistral_provider = request.env['llm.provider'].sudo().search([('service', '=', 'mistral')], limit=1)
    #     model = request.env['llm.model'].sudo().search([
    #         ('default', '=', True),
    #         ('provider_id', '=', mistral_provider.id)
    #     ], limit=1)
    #     if not mistral_provider or not model:
    #         _logger.error("Mistral provider or model not found.")
    #         return self._bad_request()
    #     client = Mistral(api_key=mistral_provider.api_key)

    #     # -- Build the prompt
    #     prompt = textwrap.dedent(f"""
    #         You are a helpdesk assistant AI integrated with an Odoo support ticketing system.
    #         A phone‐call transcription is provided below.

    #         Your job is to:
    #           1. Extract any explicit existing ticket ID (numeric) mentioned in the transcription.
    #           2. Extract any phone number (digits, +, –, spaces) mentioned in the transcription.
    #           3. Extract any email address (e.g., user@example.com) mentioned in the transcription.
    #           4. Decide whether this call matches an existing helpdesk ticket (yes/no).
    #           5. If “yes,” explain briefly what matched (ticket ID, phone, or email).
    #           6. Provide a suggested subject and full description of the issue.

    #         Transcript:
    #         \"\"\"
    #         {transcription}
    #         \"\"\"

    #         Respond strictly in JSON, with these keys:

    #         {{
    #           "match_ticket": "yes" or "no",
    #           "ticket_id": (an integer, or null if none found),
    #           "email": (the email address if found, or null),
    #           "phone": (the phone number if found, or null),
    #           "match_criteria": "short summary of what matched (e.g. ‘ID 1234’, ‘email: user@xyz.com’, ‘phone: +1 555-1234’)",
    #           "ticket_subject": "A one‐line subject for this issue",
    #           "ticket_description": "A detailed description of the issue from the call"
    #         }}
    #     """)
    #     _logger.info("***********Prompt to Mistral:\n%s", prompt)

    #     # -- Call Mistral
    #     try:
    #         chat_response = client.chat.complete(
    #             model=model.name,
    #             messages=[{"role": "user", "content": prompt}]
    #         )
    #         raw = chat_response.choices[0].message.content.strip()
    #         if raw.startswith("```"):
    #             raw = raw.strip("`").strip()
    #             if raw.lower().startswith("json"):
    #                 raw = raw[len("json"):].strip()
    #         response_data = json.loads(raw)
    #         _logger.info("***********Mistral returned: %s", response_data)
    #     except Exception as e:
    #         _logger.error("***************Mistral parsing error: %s", e)
    #         return self._bad_request()

    #     # -- Extract fields from AI response
    #     ticket_id_ai   = response_data.get("ticket_id")
    #     email_ai       = response_data.get("email")
    #     phone_ai       = response_data.get("phone")
    #     match_ticket   = (response_data.get("match_ticket") or "").lower()
    #     match_criteria = response_data.get("match_criteria", "")
    #     ticket_subject = response_data.get("ticket_subject", f"Call from {number}")
    #     ticket_desc    = response_data.get("ticket_description", transcription)

    #     Ticket = request.env['helpdesk.ticket'].sudo()

    #     # -- Attempt to find a matching ticket in Odoo
    #     matched_ticket = None

    #     # if match_ticket == "yes":
    #     # 1) If AI returned a numeric ticket_id, try that first
    #     if ticket_id_ai:
    #         try:
    #             tid = int(ticket_id_ai)
    #             # candidate = Ticket.browse(tid)
    #             candidate = Ticket.search([('ticket_ref', '=', tid)], limit=1)
    #             _logger.info("***********Matched ticket: %s", candidate)
    #             if candidate.exists():
    #                 matched_ticket = candidate
    #         except ValueError:
    #             matched_ticket = None

    #     # 2) If no direct ID, try matching by email → find partner → ticket.partner_id
    #     if not matched_ticket and email_ai:
    #         if not partner:
    #             partner = request.env['res.partner'].sudo().search([('company_id', '=', company_id.id), ('email', '=', email_ai)], limit=1)
    #         if partner:
    #             matched_ticket = Ticket.search([('company_id', '=', company_id.id), ('partner_id', '=', partner.id)], limit=1)

    #     # 3) If still no match, try matching by phone → alternate_phone or patient_phone
    #     if not matched_ticket and phone_ai:
    #         p = self._sanitize_number(phone_ai)
    #         matched_ticket = Ticket.search([
    #             ('company_id', '=', company_id.id),
    #             '|', '|', '|',
    #             ('alternate_phone', 'ilike', p),
    #             ('patient_phone',     'ilike', p),
    #             ('phone_number', 'ilike', p),
    #             ('mobile_number', 'ilike', p)
    #         ], limit=1)
            
    #     if not matched_ticket:
    #         matched_ticket = Ticket.search([
    #         ('company_id', '=', company_id.id),
    #         '|', '|', '|',
    #         ('alternate_phone', 'ilike', number),
    #         ('patient_phone',     'ilike', number),
    #         ('phone_number', 'ilike', number),
    #         ('mobile_number', 'ilike', number)
    #     ], limit=1)

    #     if matched_ticket and not matched_ticket.stage_id.is_solved:
    #         p = self._sanitize_number(phone_ai)
    #         partner = request.env['res.partner'].sudo().create({
    #             'name': 'New contact from number: ' + number,
    #             'phone': p,
    #             'email': email_ai,
    #             'company_id': company_id.id,
    #         })
    #         _logger.info("Step 2 Created new partner: %s", partner.id)
    #         _logger.info("Updating existing (unsolved) ticket ID %s", matched_ticket.id)
    #         matched_ticket.write({
    #             'description': ticket_desc,
    #             'alternate_phone': p,
    #             'partner_id': partner.id,
    #             'company_id': company_id.id,
    #         })
    #         _logger.info("Ticket Updated successfully: %s", matched_ticket.id)
    #         matched_ticket.message_post(body="Updated from 3CX call transcription.")
    #         ticket = matched_ticket

    #     else:
            
    #         if matched_ticket:
    #             _logger.info("Matched ticket ID %s is already solved; creating a new ticket instead", matched_ticket.id)
    #             matched_ticket = None

    #         _logger.info("No matching unsolved ticket found, creating a new ticket.")

    #         # --- Before creating, try to find an existing partner by email or phone
    #         if email_ai and not partner:
    #             partner = request.env['res.partner'].sudo().search([('company_id', '=', company_id.id), ('email', '=', email_ai)], limit=1)
    #         if not partner and phone_ai:
    #             p = self._sanitize_number(phone_ai)
    #             partner = request.env['res.partner'].sudo().search([
    #                 ('company_id', '=', company_id.id),
    #                 '|',
    #                 ('mobile', 'ilike', p),
    #                 ('phone',  'ilike', p),
    #             ], limit=1)

    #         p = self._sanitize_number(phone_ai)
    #         if not partner:
    #             partner = request.env['res.partner'].sudo().create({
    #                 'name': 'New contact from number: ' + number,
    #                 'phone': p,
    #                 'email': email_ai,
    #                 'company_id': company_id.id,
    #             })
    #             _logger.info("Step 3 Created new partner: %s", partner.id)

    #         team = request.env['helpdesk.team'].sudo().search([
    #             ('company_id', '=', company_id.id)
    #         ], limit=1)
    #         _logger.info("Team: %s", team.id)

    #         new_vals = {
    #             'name':        ticket_subject,
    #             'description': ticket_desc,
    #             'alternate_phone': p,
    #             'company_id': company_id.id,
    #             'team_id': team.id,
    #             # 'audio_url': recording_url,    # uncomment if you store audio_url
    #         }
    #         if partner:
    #             new_vals['partner_id'] = partner.id

    #         ticket = Ticket.create(new_vals)

    #     # -- Finally, post a call‐log note and return success
    #     # ticket.message_post(
    #     #     body=self._get_message_data(data),
    #     #     message_type='comment',
    #     #     subtype_xmlid='mail.mt_note'
    #     # )
    #     ticket.write({'call_description': self._get_message_data(data)})
    #     self._create_call_log(data, ticket)

    #     _logger.info("Ticket processed successfully: %s", ticket.id)
    #     return self._success_with_data()

    @http.route('/3cx/search/email/<string:email>', methods=["GET"], csrf=False, type="http", auth="public")
    def search_3cx_email(self, email):
        """Search an Odoo partner with the given email from 3CX"""
        if not self._is_3cx_authenticated():
            return self._unauthorized()

        _logger.info('3CX Search Email called with email %s' % email)
        if not email:
            return self._bad_request()

        partner = request.env['res.partner'].sudo().search([('email', '=', email)], limit=1)
        if not partner:
            _logger.info("No partner found for email: %s", email)
            # return self._success_with_data({})  # Or return a 404-style response if preferred
            return self._success_with_data({
                "id": "unknown",
                "name": "Unknown",
                "phone": sanitized_number,
                "email": "",
                "company": "Unknown",
                "show_url": "",
                "entitytype": "Contacts"
            })
        return self._success_with_data(self._partner_data_json(partner))

    @http.route('/3cx/search/number/<string:number>/<string:ttype>', methods=["GET"], csrf=False, type="http", auth="public")
    def search_3cx_number(self, number, ttype):
        """Search an Odoo partner with the given number from 3CX.
           The ttype is not used anymore, kept for compatibility with 3CX Template Generator"""
        if not self._is_3cx_authenticated():
            return self._unauthorized()

        if not number:
            return self._bad_request()

        sanitized_number = self._sanitize_number(number)
        _logger.info('Got sanitized number: %s' % sanitized_number)

        partner = request.env['res.partner'].sudo().search([
            '|', '|', '|',
            ('mobile_format', 'ilike', str(sanitized_number)),
            ('mobile_1_format', 'ilike', str(sanitized_number)),
            ('phone_format', 'ilike', str(sanitized_number)),
            ('phone_1_format', 'ilike', str(sanitized_number)),
        ], limit=1)

        if not partner:
            _logger.info("No partner found for number: %s", sanitized_number)
            # return self._success_with_data({})
            return self._success_with_data({
                "id": "unknown",
                "name": "Unknown",
                "phone": sanitized_number,
                "email": "",
                "company": "Unknown",
                "show_url": "",
                "entitytype": "Contacts"
            })
        return self._success_with_data(self._partner_data_json(partner))

    @http.route('/3cx/chat/create', methods=["POST"], csrf=False, type="json", auth="public")
    def _3cx_create_chat(self):
        """Chat log received from 3CX when a Chat is ticked as 'Dealt With'"""
        if not self._is_3cx_authenticated():
            return self._unauthorized()

        data = self._load_json_data()
        _logger.info('3CX Chat Create called with data %s' % data)

        if not data:
            return self._bad_request()

        email = data.get('email')
        if not email:
            return self._bad_request()

        partner = request.env['res.partner'].sudo().search([('email', '=', email)], limit=1)
        if not partner:
            _logger.warning("No matching partner found for email: %s", email)
            # return self._success_with_data()  # Or return a warning response if you prefer
            return self._success_with_data({
                "id": "unknown",
                "name": "Unknown",
                "phone": sanitized_number,
                "email": "",
                "company": "Unknown",
                "show_url": "",
                "entitytype": "Contacts"
            })

        livechat_body = self._get_livechat_data(data)
        partner.message_post(body=livechat_body, message_type='comment', subtype_xmlid='mail.mt_note')

        return self._success_with_data()

    @http.route('/3cx/call/log', methods=["POST"], csrf=False, type="json", auth="public")
    def _3cx_log_call(self):
        _logger.info("=== 3CX Call Log API Triggered ===")

        if not self._is_3cx_authenticated():
            return self._unauthorized()

        data = self._load_json_data()
        _logger.info("=== 3CX Call Log data ===: %s", data)
        if not data:
            return self._bad_request()

        company_id = request.env['res.company'].sudo().browse(int(data.get('company')))
        number = data.get('phone')
        if not number:
            return self._bad_request()
        number = self._sanitize_number(number)

        transcription = data.get('transcription', '')
        recording_url = data.get('recording_url')

        # -- Load Mistral provider & model
        mistral_provider = request.env['llm.provider'].sudo().search([('service', '=', 'mistral')], limit=1)
        model = request.env['llm.model'].sudo().search([
            ('default', '=', True),
            ('provider_id', '=', mistral_provider.id)
        ], limit=1)
        if not mistral_provider or not model:
            _logger.error("Mistral provider or model not found.")
            return self._bad_request()
        client = Mistral(api_key=mistral_provider.api_key)

        # -- Build the prompt
        prompt = textwrap.dedent(f"""
            You are a helpdesk assistant AI integrated with an Odoo support ticketing system.
            A phone‐call transcription is provided below.

            Your job is to:
              1. Extract any explicit existing ticket ID (numeric) mentioned in the transcription.
              2. Extract any phone number (digits, +, –, spaces) mentioned in the transcription.
              3. Extract any email address (e.g., user@example.com) mentioned in the transcription.
              4. Extract the caller's name if mentioned.
              5. Decide whether this call matches an existing helpdesk ticket (yes/no).
              6. If “yes,” explain briefly what matched (ticket ID, phone, or email).
              7. Provide a suggested subject and full description of the issue.

            Transcript:
            \"\"\"
            {transcription}
            \"\"\"

            Respond strictly in JSON, with these keys:

            {{
              "match_ticket": "yes" or "no",
              "ticket_id": (an integer, or null if none found),
              "name": (caller’s name if found, or null),
              "email": (the email address if found, or null),
              "phone": (the phone number if found, or null),
              "match_criteria": "short summary of what matched (e.g. ‘ID 1234’, ‘email: user@xyz.com’, ‘phone: +1 555-1234’)",
              "ticket_subject": "A one‐line subject for this issue",
              "ticket_description": "A detailed description of the issue from the call"
            }}
        """)
        _logger.info("***********Prompt to Mistral:\n%s", prompt)

        # -- Call Mistral
        try:
            chat_response = client.chat.complete(
                model=model.name,
                messages=[{"role": "user", "content": prompt}]
            )
            raw = chat_response.choices[0].message.content.strip()
            if raw.startswith("```"):
                raw = raw.strip("`").strip()
                if raw.lower().startswith("json"):
                    raw = raw[len("json"):].strip()
            response_data = json.loads(raw)
            _logger.info("***********Mistral returned: %s", response_data)
        except Exception as e:
            _logger.error("***************Mistral parsing error: %s", e)
            return self._bad_request()

        # -- Extract fields from AI response
        ticket_id_ai   = response_data.get("ticket_id")
        _logger.info("***********ticket_id_ai: %s", ticket_id_ai)
        email_ai       = response_data.get("email")
        _logger.info("***********email_ai: %s", email_ai)
        phone_ai       = response_data.get("phone")
        _logger.info("***********phone_ai: %s", phone_ai)
        partner_name_ai= response_data.get("name")
        _logger.info("***********partner_name_ai: %s", partner_name_ai)
        match_ticket   = (response_data.get("match_ticket") or "").lower()
        match_criteria = response_data.get("match_criteria", "")
        ticket_subject = response_data.get("ticket_subject", f"Call from {number}")
        _logger.info("***********ticket_subject: %s", ticket_subject)
        ticket_desc    = response_data.get("ticket_description", transcription)
        _logger.info("***********ticket_desc: %s", ticket_desc)

        call_description = self._get_message_data(data)
        _logger.info("call_description: %s", call_description)
        data.update({
            'ticket_id_ai': ticket_id_ai,
            'email_ai': email_ai,
            'phone_ai': phone_ai,
            'description': ticket_desc,
            'call_description': call_description,
            'number': number,
            'partner_name_ai': partner_name_ai,
        })
        _logger.info("Call log data: %s", data)
        log_id = self._create_call_log(data)
        _logger.info("Call log id: %s", log_id)
        return self._success_with_data()


    def _create_call_log(self, data, partner=None):
        _logger.info("============_create_call_log : %s" % data)
        company_id = request.env['res.company'].sudo().browse(int(data.get('company')))
        _logger.info("============company_id : %s" % company_id)
        res = request.env['res.call.log'].sudo().create({
            'name': data.get('subject', ''),
            'date': data.get('date', ''),
            'ttype': data.get('type', ''),
            'entitytype': data.get('entitytype', ''),
            'agentname': data.get('agentname', ''),
            'agent': data.get('agent', ''),
            'call_start': data.get('callstart', ''),
            'call_established': data.get('callestablished', ''),
            'call_end': data.get('callend', ''),
            # 'partner_id': partner.id,
            # 'ticket_id': partner.id,
            'duration': data.get('duration', ''),
            'details': data.get(data.get('type', 'no').lower(), ''),
            'transcription': data.get('transcription', ''),
            'audio_url': data.get('recording_url', ''),
            'company_id': company_id.id,
            'call_ticket': data.get('ticket_id_ai', ''),
            'call_email': data.get('email_ai', ''),
            'call_phone': data.get('phone_ai', ''),
            'description': data.get('description', ''),
            'call_description': data.get('call_description', ''),
            'number': data.get('number', ''),
            'partner_name_ai': data.get('partner_name_ai', ''),
            # Added
            
            # 'missed_call_test': data.get('missed', ''),
            # 'callid': data.get('callid', ''),
            # 'historyid': data.get('historyid', ''),
            # 'reason_terminated': data.get('reason_terminated', ''),
            # 'from_dn': data.get('from_dn', ''),
            # 'dial_no': data.get('dial_no', ''),
            # 'reason_changed': data.get('reason_changed', ''),
            # 'final_number': data.get('final_number', ''),
            # 'final_dn': data.get('final_dn', ''),
            # 'bill_code': data.get('bill_code', ''),
            # 'bill_rate': data.get('bill_rate', ''),
            # 'bill_cost': data.get('bill_cost', ''),
            # 'bill_name': data.get('bill_name', ''),
            # 'chain': data.get('chain', ''),
            # 'missed_queue_calls': data.get('missed_queue_calls', ''),
            # 'from_type': data.get('from_type', ''),
            # 'to_type': data.get('to_type', ''),
            # 'final_type': data.get('final_type', ''),
            # 'final_dispname': data.get('final_dispname', ''),
            # 'from_dispname': data.get('from_dispname', ''),
            # 'to_dispname': data.get('to_dispname', ''),
            # 'to_dn': data.get('to_dn', ''),
            # 'created_at': data.get('created_at', ''),
        })
        return res
