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
from odoo import api, fields, models,_

class ResConfigSettings(models.TransientModel):
	_inherit = 'res.config.settings'

	host_db_url = fields.Char(string='Host DB URL')
	db_logo = fields.Binary(string='Company Logo')

	@api.model
	def get_values(self):
		res = super(ResConfigSettings, self).get_values()
		config_parameter = self.env['ir.config_parameter'].sudo()
		host_db_url = config_parameter.get_param('client_vendor_dashboard.host_db_url')
		db_logo = config_parameter.get_param('client_vendor_dashboard.db_logo')
		res.update(host_db_url=host_db_url, db_logo=db_logo)
		return res

	def set_values(self):
		res = super(ResConfigSettings, self).set_values()
		config_parameter = self.env['ir.config_parameter'].sudo()
		config_parameter.set_param("client_vendor_dashboard.host_db_url", self.host_db_url)
		config_parameter.set_param("client_vendor_dashboard.db_logo", self.db_logo)
		return res