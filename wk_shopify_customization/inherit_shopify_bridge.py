# -*- coding: utf-8 -*-
##############################################################################
# Copyright (c) 2015-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
# See LICENSE file for full copyright and licensing details.
# License URL : <https://store.webkul.com/license.html/>
##############################################################################
from ..shopify_odoo_bridge.shopify_bridge import Bridge
from re import sub
import logging

class InheritBridge(Bridge):
	
	def get_products(self,**kw):
		product_data_list = []
		if kw.get('object_id'):
				options={'ids':kw.get('object_id')}
				products = self.ensure_response('Product','find',**options)
				for product in products:
					data_list = self.process_product(product)
					if data_list:
						if isinstance(data_list, list):
							product_data_list.extend(data_list)
						else:
							product_data_list.append(data_list)
		else:
			options = self.pre_get(kw)
			if options.get('limit'):
				products = self.ensure_response('Product','find',**options)
				for product in products:
					data_list = self.process_product(product)
					if data_list:
						if isinstance(data_list, list):
							product_data_list.extend(data_list)
						else:
							product_data_list.append(data_list)
				if products.has_next_page():
					kw['next_url'] = products.next_page_url
				if products:
					kw['last_updated'] = product.updated_at
				kw['fetch_completed'] = False if products.has_next_page() else True
		return product_data_list,self.post_get(kw)
    
	def process_product(self,product):
		if len(product.variants) != 1:
			products_data = []
			shared_product_data = {
                'name': product.title,
            }
			if product.body_html:
				shared_product_data['description_sale'] = sub('<.*?>','',product.body_html)
			attributes = self.process_attribute(product.options)
			image_data = self.prepare_image_data(product.images)
			collections = self.ensure_response('CustomCollection','find',product_id=product.id)
			extra_category_ids = ','.join(map(lambda x:str(x.id),collections))
			for variant in product.variants:
				product_data = {}
				if not variant.sku:
					continue
				product_data.update(self.process_variant(variant,attributes) | shared_product_data)
				product_data.update({
					'image_url':image_data.get(variant.image_id),
					'extra_categ_ids':extra_category_ids
					})
				if product_data:
					products_data.append(product_data)
			return products_data
		else:
			return super(InheritBridge, self).process_product(product)

	def pre_get(self,kw):
		res = super(InheritBridge, self).pre_get(kw)
		if not kw.get('object_id') and res:
			res.update({'status':'active'})
		return res
	
	def prepare_image_data(self, image_data):
		return  {img.id:img.src for img in image_data}
	
