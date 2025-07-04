# -*- coding: utf-8 -*-
##############################################################################
# Copyright (c) 2015-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
# See LICENSE file for full copyright and licensing details.
# License URL : <https://store.webkul.com/license.html/>
##############################################################################

from odoo import api,fields,models
from ..inherit_shopify_bridge import InheritBridge


class MultiChannelSale(models.Model):
	_inherit = 'multi.channel.sale'
 

	barcode_postfix = fields.Selection([('EU', 'EU'),('CA', 'CA')])
	
	def import_shopify(self,object,**kw):
		def reformat_barcode(data_list):
			for data in data_list:
				if data.get('barcode'):
					data['barcode'] += self.barcode_postfix
				if data.get('variants') and data['variants'][0]['barcode']:
					data['variants'][0]['barcode'] += self.barcode_postfix
			return data_list

		if object == 'product.template':
			with InheritBridge(self.url,self.email,self.api_key,self.id,**kw) as bridge:
				data_list, kw = bridge.get_products(**kw)
				if self.barcode_postfix in ['EU', 'CA']:
					data_list = reformat_barcode(data_list)
				return data_list, kw
		else:
			return super(MultiChannelSale, self).import_shopify(object, **kw)
		
