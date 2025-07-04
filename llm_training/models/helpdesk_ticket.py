from odoo import models, api, fields
import json
import os
import base64
from tempfile import NamedTemporaryFile
from datetime import datetime, date
import requests
import logging
import time

_logger = logging.getLogger(__name__)

class HelpdeskExportLLM(models.Model):
	_inherit = "helpdesk.ticket"

	def export_selected_tickets(self):
		examples = []

		instructions = {
			"user_id": {
				"instruction": "Who was assigned to ticket #{id}?",
				"output_template": "The ticket was assigned to {value}."
			},
			"assign_date": {
				"instruction": "When was ticket #{id} assigned?",
				"output_template": "The ticket was assigned on {value}."
			},
			"alternate_phone": {
				"instruction": "What is the alternate phone number for ticket #{id}?",
				"output_template": "The alternate phone number is {value}."
			},
			# "cra_call_center_info": {
			# 	"instruction": "What is the CRA call center info for ticket #{id}?",
			# 	"output_template": "CRA Call Center Info: {value}."
			# },
			# "datetime_appointment": {
			# 	"instruction": "When is the appointment scheduled for ticket #{id}?",
			# 	"output_template": "Appointment is scheduled on {value}."
			# },
			"email_cc": {
				"instruction": "What is the CC email for ticket #{id}?",
				"output_template": "CC Email: {value}."
			},
			"email": {
				"instruction": "What is the email for ticket #{id}?",
				"output_template": "Email: {value}."
			},
			# "sim_register_info": {
			# 	"instruction": "What is the SIM register info for ticket #{id}?",
			# 	"output_template": "SIM Register Info: {value}."
			# },
			"phone_lost": {
				"instruction": "What is the lost phone number for ticket #{id}?",
				"output_template": "Lost Phone Number: {value}."
			},
			"team_id": {
				"instruction": "Which team is handling ticket #{id}?",
				"output_template": "The ticket is handled by the team {value}."
			},
			"partner_id": {
				"instruction": "For which partner was ticket #{id} created?",
				"output_template": "The ticket was created for partner {value}."
			},
		}

		for ticket in self:
			for field, templates in instructions.items():
				value = getattr(ticket, field)
				if not value:
					continue
				if hasattr(value, 'name'):
					value = value.name
				if isinstance(value, (datetime, date)):
					value = value.strftime('%Y-%m-%d %H:%M:%S')

				examples.append([
					{"role": "user", "content": templates["instruction"].format(id=ticket.id)},
					{"role": "assistant", "content": templates["output_template"].format(value=value)}
				])

			examples.append([
				{"role": "user", "content": f"Summarize ticket #{ticket.id}."},
				{"role": "assistant", "content": f"Ticket Summary: {ticket.name}. Resolution: {ticket.description or 'Not resolved.'}"}
			])

		_logger.info("===============examples : %s" % examples)
		# Save to JSONL file
		with NamedTemporaryFile(delete=False, suffix='.jsonl', mode='w', encoding='utf-8') as temp_file:
			for example in examples:
				temp_file.write(json.dumps(example) + '\n')
			jsonl_path = temp_file.name

		# Read content for Odoo attachment
		with open(jsonl_path, 'rb') as f:
			file_content = base64.b64encode(f.read())

		# Create Odoo attachment
		attachment = self.env['ir.attachment'].create({
			'name': 'helpdesk_llm_data.jsonl',
			'type': 'binary',
			'datas': file_content,
			'mimetype': 'application/jsonl',
			'res_model': 'helpdesk.ticket',
			'res_id': self[0].id,
		})

		provider_id = self.env['llm.provider'].sudo().search([('service', '=', 'mistral')])
		API_KEY = provider_id.api_key
		headers = {
			"Authorization": f"Bearer {API_KEY}"
		}
		files = {
			"file": open(jsonl_path, 'rb')
		}
		data = {
			"name": f"helpdesk-data-{datetime.now().strftime('%Y%m%d%H%M')}",
			"task": "text-instruction"
		}

		response = requests.post("https://api.mistral.ai/v1/files", headers=headers, files=files, data=data)
		_logger.info("###response : %s" % response)
		_logger.info("###response: %s" % response.text)
		# Clean up
		os.unlink(jsonl_path)

		# Handle response
		if response.status_code == 200:
			res_json = response.json()
			file_id = res_json.get("id")
			_logger.info(f"File uploaded successfully to Mistral: {file_id}")

			model_id = self.env['llm.model'].sudo().search([('provider_id', '=', provider_id.id), ('default', '=', True)])
			fine_tune_data = {
				"training_files": [file_id],
				"model": model_id.name,
				"hyperparameters": {
				    "training_steps": 10,
				    "learning_rate": 0.0001
				},
			}
			_logger.info("======fine_tune_data: %s" % fine_tune_data)
			fine_tune_response = requests.post(
				"https://api.mistral.ai/v1/fine_tuning/jobs",
				headers=headers,
				json=fine_tune_data
			)
			_logger.info("=======fine_tune_response: %s" % fine_tune_response)
			_logger.info("========fine_tune_response.text: %s" % fine_tune_response.text)
			if fine_tune_response.status_code == 200:
				fine_tune_id = fine_tune_response.json().get("id")

				response = requests.get(f"https://api.mistral.ai/v1/fine_tuning/jobs/{fine_tune_id}", headers=headers)
				_logger.info("*****response******: %s" % response.json())


				_logger.info(f"Fine-tuning started. Job ID: {fine_tune_id}")
			else:
				_logger.warning(f"Fine-tune start failed: {fine_tune_response.text}")


			_logger.info(f"File uploaded successfully to Mistral: {res_json.get('id')}")
		else:
			_logger.info(f"Failed to upload to Mistral: {response.text}")

		return {
			'type': 'ir.actions.act_url',
			'url': f'/web/content/{attachment.id}?download=true',
			'target': 'self',
		}