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

class ResConfigSettings(models.TransientModel):
	_inherit = 'res.config.settings'

	shipping_max_value = fields.Float(string='Max. Shipping Cost')

	@api.model
	def get_values(self):
		res = super(ResConfigSettings, self).get_values()
		params = self.env['ir.config_parameter'].sudo()
		shipping_max_value = params.get_param('shipping_max_value',
												 default=False)
		res.update(shipping_max_value=shipping_max_value)
		return res

	def set_values(self):
		super(ResConfigSettings, self).set_values()
		self.env['ir.config_parameter'].sudo().set_param(
			"shipping_max_value",
			self.shipping_max_value)