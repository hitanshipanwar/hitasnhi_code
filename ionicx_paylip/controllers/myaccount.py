# -*- coding: utf-8 -*-

from collections import OrderedDict
from operator import itemgetter
import werkzeug
from odoo import _, http
from odoo.exceptions import AccessError, MissingError
from odoo.http import request
from odoo.osv.expression import AND, OR
from odoo.tools import groupby as groupbyelem
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager, pager
import json
import logging
import PyPDF2
import io
from io import BytesIO
from PyPDF2 import PdfFileWriter, PdfFileReader

_logger = logging.getLogger(__name__)


class CustomerPortalHelpdesk(CustomerPortal):

	def _prepare_home_portal_values(self, counters):
		values = super()._prepare_home_portal_values(counters)
		if "payslip_count" in counters:
			payslip_model = request.env["payslip.payslip"]
			payslip_count = (
				payslip_model.search_count([])
				if payslip_model.check_access_rights("read", raise_exception=False)
				else 0
			)
			values["payslip_count"] = payslip_count
		return values

	@http.route(['/my/payslips', '/my/payslips/page/<int:page>'], type='http', website=True)
	def payslipListView(self, page=1, sortby='id', search="", search_in="All", **kw):

		sorted_list = {
			'id':{'label':'ID', 'order':'id desc'},
			'name':{'label':'Name', 'order':'employee_id'},
			'designation':{'label':'Designation', 'order':'designation'},
			'emp_id':{'label':'Employee ID', 'order':'emp_id'},
			'month':{'label':'Month', 'order':'months asc'},
		}
		default_order_by = sorted_list[sortby]['order']

		search_list = {
			'All':{'label':'All', 'input':'All', 'domain':[]},
			'Name':{'label':'Employee Name', 'input':'Name', 'domain':[('employee_id.name', 'ilike', search)]},
			'Months':{'label':'Month', 'input':'Months', 'domain':[('months', 'ilike', search)]},
		}

		search_domain = search_list[search_in]['domain']

		payslip_obj = request.env['payslip.payslip']
		total_payslips = payslip_obj.search_count(search_domain)
		page_detail = pager(url='/my/payslips',
							total=total_payslips,
							page=page,
							url_args={'sortby':sortby, 'search_in': search_in, 'search':search},
							step=6)
		payslips = payslip_obj.search(search_domain, order=default_order_by, limit=8, offset=page_detail['offset'])
		vals = {'payslips': payslips, 'page_name':'payslips_list_view', 'pager':page_detail,
				'search_in':search_in,
				'searchbar_inputs':search_list,
				'search':search,
				'sortby':sortby,
				'searchbar_sortings':sorted_list,
				}
		return request.render("ionicx_paylip.portal_payslip_list_view", vals)

	@http.route(['/my/payslip/<model("payslip.payslip"):payslip_id>'], type='http', website=True)
	def payslipFormView(self, payslip_id, **kw):
		vals = {"payslip": payslip_id, 'page_name': 'payslips_form_view'}
		payslip_records = request.env['payslip.payslip'].search([])
		payslip_ids = payslip_records.ids
		payslip_index = payslip_ids.index(payslip_id.id)

		if payslip_index > 0:
			vals['prev_record'] = '/my/payslip/{}'.format(payslip_ids[payslip_index - 1])

		if payslip_index < len(payslip_ids) - 1:
			vals['next_record'] = '/my/payslip/{}'.format(payslip_ids[payslip_index + 1])

		return request.render("ionicx_paylip.portal_payslips_form_view", vals)

	def _get_employees(self):
		return (
			http.request.env["res.users"]
			.sudo()
			.search([("active", "=", True)])
		)

	@http.route(["/new/payslip"], type="http", methods=["POST", "GET"], website=True)
	def create_new_payslip(self, **kw):
		payslip_list = request.env['payslip.payslip'].search([])
		months_selection = {
			'jan': 'January',
			'feb': 'February',
			'mar': 'March',
			'april': 'April',
			'may': 'May',
			'june': 'June',
			'july': 'July',
			'aug': 'August',
			'sep': 'September',
			'oct': 'October',
			'nov': 'November',
			'dec': 'December',
		}

		return request.render("ionicx_paylip.portal_create_payslip", {'payslips': payslip_list, "employees": self._get_employees(), "months": months_selection, 'page_name':'create_payslip'})
   

	def _prepare_submit_payslip_vals(self, **kw):
		basic_salary = int(kw.get("basic_salary", 0))
		hra = int(kw.get("hra", 0))
		conveyance = int(kw.get("conveyance", 0))
		medical = int(kw.get("medical", 0))
		special_allowance = int(kw.get("special_allowance", 0))
		earning_epf = int(kw.get("earning_epf", 0))
		others = int(kw.get("others", 0))
		deduct_employer_pf = int(kw.get("deduct_employer_pf", 0))
		deduct_employee_pf = int(kw.get("deduct_employee_pf", 0))
		esi = int(kw.get("esi", 0))
		professional_tax = int(kw.get("professional_tax", 0))
		tds = int(kw.get("tds", 0))
		advance = int(kw.get("advance", 0))
		leave_deduct = int(kw.get("leave_deduct", 0))

		if (kw.get("deduct_total")):
			deduct_total = int(kw.get("deduct_total", 0))
		if (kw.get("total_earning")):
			earning_total = int(kw.get("total_earning", 0))

		total_earning = basic_salary + hra + conveyance + medical + special_allowance + earning_epf + others
		total_deduct = deduct_employer_pf + deduct_employee_pf + esi + professional_tax + tds + advance + leave_deduct
		
		vals = {
			"name": kw.get("name"),
			"months": kw.get("months"),
			"year": kw.get("year"),
			"department": kw.get("department"),
			"designation": kw.get("designation"),
			"basic_salary": kw.get("basic_salary"),
			"hra": kw.get("hra"),
			"conveyance": kw.get("conveyance"),
			"medical": kw.get("medical"),
			"special_allowance": kw.get("special_allowance"),
			"earning_epf": kw.get("earning_epf"),
			"others": kw.get("others"),
			"deduct_employer_pf": kw.get("deduct_employer_pf"),
			"deduct_employee_pf": kw.get("deduct_employee_pf"),
			"esi": kw.get("esi"),
			"professional_tax": kw.get("professional_tax"),
			"tds": kw.get("tds"),
			"advance": kw.get("advance"),
			"leave_deduct": kw.get("leave_deduct"),
			"deduct_total":  kw.get("deduct_total") if kw.get("deduct_total") else total_deduct,
			"total_earning":  kw.get("total_earning") if kw.get("total_earning") else total_earning,
			"net_pay": kw.get("net_pay") if kw.get("net_pay") else ((earning_total - deduct_total)if kw.get("total_earning") and kw.get("total_earning") else (total_earning - total_deduct)),
			"emp_id": kw.get("emp_id"),
			# "employees": self._get_employees(),
		}
		employee_user = (
			http.request.env["res.users"]
			.sudo()
			.search(
				[("id", "=", kw.get("employee"))]
			)
		)
		hr_employee = (
			http.request.env["hr.employee"]
			.sudo()
			.search(
				[("user_id.id", "=", kw.get("employee"))]
			)
		)
		vals.update({
			"employee_id": employee_user.id,
			"password_name": hr_employee.password_name,
			"password": hr_employee.password,
			"company_id": hr_employee.company_id.id,
			"hr_employee": hr_employee.id,
			})
		return vals

	@http.route("/submitted/payslip", type="http", auth="user", website=True, csrf=True)
	def submit_ticket(self, **kw):
		vals = self._prepare_submit_payslip_vals(**kw)
		new_payslip = request.env["payslip.payslip"].sudo().create(vals)
		return werkzeug.utils.redirect("/my/payslip/%s" % new_payslip.id)


	# @http.route("/my/payslip/print/<model('payslip.payslip'):payslip_id>", auth="user", type="http", website=True)
	# def payslip_pdf_report(self, payslip_id, **kw):
	# 	print('=============================', payslip_id)
	# 	return self._show_report(model=payslip_id, report_type='pdf', report_ref="ionicx_paylip.action_payslip_report", download=True)

	@http.route("/my/payslip/print/<model('payslip.payslip'):payslip_id>", auth="user", type="http", website=True)
	def payslip_pdf_report(self, payslip_id, **kw):
		# payslip = request.env['payslip.payslip'].browse(payslip_id.id)
		payslip = request.env['payslip.payslip'].search([('id', '=', payslip_id.id)])
		if not payslip:
			return request.not_found()
		report = request.env.ref('ionicx_paylip.action_payslip_report')
		if not report:
			return request.not_found()
		hr_employee = request.env['hr.employee'].sudo().search([("user_id.id", "=", payslip.employee_id.id)])
		password = hr_employee.password_name
		payslip_report = self._generate_pdf_report(payslip, report.report_name, password)
		return payslip_report

	def _generate_pdf_report(self, payslip, reportname, password=None):
		name = request.env['payslip.payslip'].search([])
		report = request.env['ir.actions.report']._get_report_from_name(reportname)
		context = dict(request.env.context)
		pdf = report.with_context(context)._render_qweb_pdf(reportname, payslip.id)[0]
		pdf_reader = PyPDF2.PdfFileReader(io.BytesIO(pdf))
		pdf_writer = PyPDF2.PdfFileWriter()
		for page_num in range(pdf_reader.numPages):
			page = pdf_reader.getPage(page_num)
			pdf_writer.addPage(page)
		if password:
			pdf_writer.encrypt(password, use_128bit=True)
		pdf_buffer = io.BytesIO()
		pdf_writer.write(pdf_buffer)
		pdf_buffer.seek(0)
		pdf_data = pdf_buffer.read()
		pdfhttpheaders = [
			('Content-Type', 'application/pdf'),
			# ('Content-Disposition', f'attachment; filename=payslip_{payslip.id}.pdf')
			('Content-Disposition', f'attachment; filename={payslip.employee_id.name} payslip of month {payslip.months}.pdf')
		]
		return http.request.make_response(pdf_data, headers=pdfhttpheaders)