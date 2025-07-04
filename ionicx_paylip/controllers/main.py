# -*- coding: utf-8 -*-
import json
import logging
import werkzeug
from odoo import http
from odoo.http import request
from odoo.addons.web.controllers.report import ReportController

_logger = logging.getLogger(__name__)


class ReportControllerInherit(ReportController):
	@http.route([
		'/report/<converter>/<reportname>',
		'/report/<converter>/<reportname>/<docids>',
	], type='http', auth='user', website=True)
	def report_routes(self, reportname, docids=None, converter=None, **data):
		if reportname == 'ionicx_paylip.payslip_report':
			payslip = request.env['payslip.payslip'].search([('id', '=', docids)])
		report = request.env['ir.actions.report']._get_report_from_name(reportname)
		context = dict(request.env.context)

		if docids:
			docids = [int(i) for i in docids.split(',') if i.isdigit()]
		if data.get('options'):
			data.update(json.loads(data.pop('options')))
		if data.get('context'):
			data['context'] = json.loads(data['context'])
			context.update(data['context'])
		if converter == 'html':
			html = report.with_context(context)._render_qweb_html(reportname, docids, data=data)[0]
			return request.make_response(html)
		elif converter == 'pdf':
			if reportname == 'ionicx_paylip.payslip_report':
				pdf = report.with_context(context)._render_qweb_pdf(reportname, docids, data=data)[0]
				pdf_data = report.encrypt_pdf(pdf, payslip.password_name)
				pdfhttpheaders = [('Content-Type', 'application/pdf'), ('Content-Length', len(pdf_data))]
			else:
				pdf = report.with_context(context)._render_qweb_pdf(reportname, docids, data=data)[0]
				pdf_data = report.encrypt_pdf(pdf, report.password_name)
				pdfhttpheaders = [('Content-Type', 'application/pdf'), ('Content-Length', len(pdf_data))]
			return request.make_response(pdf_data, headers=pdfhttpheaders)
		elif converter == 'text':
			text = report.with_context(context)._render_qweb_text(reportname, docids, data=data)[0]
			texthttpheaders = [('Content-Type', 'text/plain'), ('Content-Length', len(text))]
			return request.make_response(text, headers=texthttpheaders)
		else:
			raise werkzeug.exceptions.HTTPException(description='Converter %s not implemented.' % converter)
