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


class CustomerEnquiryPortal(CustomerPortal):

	def _prepare_customer_enquiry_portal_values(self, counters):
		values = super()._prepare_customer_enquiry_portal_values(counters)
		# if "customer_enquiry_count" in counters:
		# 	customer_enquiry_model = request.env["customer.enquiry"]
		# 	customer_enquiry_count = (
				# customer_enquiry_model.search_count([])
		# 		if customer_enquiry_model.check_access_rights("read", raise_exception=False)
		# 		else 0
		# 	)
		# 	values["customer_enquiry_count"] = customer_enquiry_count
		if 'customer_enquiry_count' in counters:
			customer_enquiry_count = request.env['customer.enquiry'].search_count([])
			values['customer_enquiry_count'] = customer_enquiry_count
		return values

	@http.route(['/my/customer/enquiries', '/my/customer/enquiries/<int:page>'], type='http', website=True)
	def CustomerEnquirypListView(self, page=1, sortby='id', search="", search_in="All", **kw):

		customer_enq_obj = request.env['customer.enquiry']
		total_enquries = customer_enq_obj.search_count(search_domain)
		page_detail = pager(url='/my/customer/enquiries',
							total=total_enquiries,
							page=page,
							url_args={'sortby':sortby, 'search_in': search_in, 'search':search},
							step=6)
		enquiries = customer_enq_obj.search(search_domain, order=default_order_by, limit=8, offset=page_detail['offset'])
		vals = {'enquiries': enquiries, 'page_name':'portal_customer_enquiry_list_view', 'pager':page_detail,
				# 'search_in':search_in,
				# 'searchbar_inputs':search_list,
				# 'search':search,
				# 'sortby':sortby,
				# 'searchbar_sortings':sorted_list,
				}
		return request.render("interview_task.portal_customer_enquiry_list_view", vals)

	@http.route(["/new/customer/enquiry"], type="http", methods=["POST", "GET"], website=True)
	def create_new_customer_enquiry(self, **kw):
		enquiries_list = request.env['customer.enquiry'].search([])
		return request.render("interview_task.portal_create_customer_enquiry", {'enquiries': enquiries_list, 'page_name':'create_customer_enquiry'})
