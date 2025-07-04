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
from odoo import api, models, tools
from odoo.tools import ormcache, make_index_name, create_index

DELAY_KEY = "inactive_session_time_out_delay"
IGNORED_PATH_KEY = "inactive_session_time_out_ignored_url"


class IrConfigParameter(models.Model):
	_inherit = "ir.config_parameter"


	@api.model
	@tools.ormcache("self.env.cr.dbname")
	def _auth_timeout_get_parameter_delay(self):
		return self.env["ir.config_parameter"].sudo()

	@api.model
	@tools.ormcache("self.env.cr.dbname")
	def _auth_timeout_get_parameter_ignored_urls(self):
		return self.env["ir.config_parameter"].sudo()

	def write(self, vals):
		res = super(IrConfigParameter, self).write(vals)

		DELAY_KEY = 'inactive_session_time_out_delay'
		IGNORED_PATH_KEY = 'inactive_session_time_out_ignored_url'

		delay_record = self._auth_timeout_get_parameter_delay()
		delay_path = self._auth_timeout_get_parameter_ignored_urls()
		if delay_record:
			delay_record.clear_cache(self.filtered(lambda r: r.key == DELAY_KEY))

		if delay_path:
			delay_path.clear_cache(self.filtered(lambda r: r.key == IGNORED_PATH_KEY))

		return res


	# @api.model
	# @tools.ormcache("self.env.cr.dbname")
	# def _auth_timeout_get_parameter_delay(self):
	#     return int(
	#         self.env["ir.config_parameter"]
	#         .sudo()
	#         .get_param(
	#             DELAY_KEY,
	#             7200,
	#         )
	#     )

	# @api.model
	# @tools.ormcache("self.env.cr.dbname")
	# def _auth_timeout_get_parameter_ignored_urls(self):
	#     urls = (
	#         self.env["ir.config_parameter"]
	#         .sudo()
	#         .get_param(
	#             IGNORED_PATH_KEY,
	#             "",
	#         )
	#     )
	#     return urls.split(",")

	
	# def write(self, vals):
	#     res = super(IrConfigParameter, self).write(vals)
	#     self._auth_timeout_get_parameter_delay.clear_cache(
	#         self.filtered(lambda r: r.key == DELAY_KEY),
	#     )
	#     self._auth_timeout_get_parameter_ignored_urls.clear_cache(
	#         self.filtered(lambda r: r.key == IGNORED_PATH_KEY),
	#     )
	#     return res
