from odoo.addons.shopify_odoo_bridge.shopify_bridge import Bridge
from re import sub
from odoo.http import request
import logging

_logger = logging.getLogger(__name__)


def process_order(self,order):
		order_data = {
			'channel_id'       : self.id,
			'store_id'         : order.id,
			'name'             : order.name,
			'currency'         : order.currency,
			'date_order'       : order.created_at,
			'confirmation_date': order.updated_at,
			'line_type'        : 'multi',
			'order_tag' 	   : order.tags,
			'note'			   : order.note,
		}
		customer_vat=''

		if order.fulfillment_status == 'fulfilled':
			order_data['order_state'] = 'Done'
		elif order.cancelled_at:
			order_data['order_state'] = 'Cancelled'
		elif order.financial_status == 'paid':
			order_data['order_state'] = 'Paid'
		else:
			order_data['order_state'] = 'Sale'

		# ===================================== PARTIALLY REFUNDED CUSTOMIZATION =================================================
		if order.financial_status == 'partially_refunded' and order.fulfillment_status == 'fulfilled':
			order_data['order_state'] = 'Refunded'

		if order.cancelled_at and order.financial_status == 'voided':
			order_data['order_state'] = 'Canceled'

		if order.refunds:
			order_data['refund_json'] = [refund.to_dict() for refund in order.refunds]
		# =====================================================================================================

		if order.payment_gateway_names:
			order_data.update(payment_method = order.payment_gateway_names[0])
		elif order.financial_status == 'paid':
			order_data.update(payment_method = 'Paid by Customer')

		if order.shipping_lines:
			order_data.update(carrier_id = order.shipping_lines[0].title)
		#****************Rahul customization*************
		note_attributes = order.note_attributes
		crowdship_email =''
		for item in note_attributes:
				if item.name == 'Crowdship Email':
					crowdship_email = item.value
		#**************************************************************
		if order.attributes.get('customer'):
			if hasattr(order.customer, 'metafields'):
				metafields= order.customer.metafields()
				for metafield in metafields:
					if metafield.key == 'tax_id':
						customer_vat = metafield.value
						pass

			#============Task id [212229] ==============================	
			order_data.update(
				{
					'customer_tag'     : order.customer.tags,
					'partner_id'       : order.customer.id or 'missing',
					'customer_name'    : (order.customer.first_name or '') + ' ' + (order.customer.last_name or ''),
					'customer_email'   : order.customer.email if order.customer.email else (crowdship_email if crowdship_email else '') ,
					'customer_mobile'  : order.customer.phone,
					'customer_phone'   : order.customer.attributes.get('default_address') and order.customer.default_address.phone,
				
				}
			)
		   #==========================================================================
			try:
				if order.billing_address:
					invoice_address = self.process_address(order.billing_address,type='order')
				else:
					invoice_address = {
								'name'        : order.customer.first_name + ' ' + order.customer.last_name or False,
								'phone'       : order.customer.phone or False,
							}
			except AttributeError:
				invoice_address= None

			try:
				shipping_address = self.process_address(order.shipping_address,type='order')
			except AttributeError:
				shipping_address = None

			same_address = invoice_address == shipping_address
			if invoice_address:
				
				invoice_address.update(
					{
						'partner_id': order.customer.id,
						'email'     : order.email if order.email else (crowdship_email if crowdship_email else '') ,
						
					}
				)
				order_data.update({'invoice_'+k:v for k,v in invoice_address.items()})
				order_data.update({	'company_name': order.billing_address.company if order.billing_address else '','customer_vat':customer_vat})
			if shipping_address and not same_address:
				shipping_address.update(
					{
						'partner_id': order.customer.id,
						'email'     : order.email if order.email else (crowdship_email if crowdship_email else '')
					}
				)
				order_data.update({'shipping_'+k:v for k,v in shipping_address.items()})
			if invoice_address and shipping_address:
				order_data.update(same_shipping_billing = same_address)
		#=============Task id [212229] =========
		else:
			same_address = True
			order_data.update({
				'partner_id'       :  'missing',
				'customer_name'    :  'missing',
				'invoice_partner_id': 'missing'

			})
			order_data.update(same_shipping_billing = same_address)

		#========================================		#Abhishek
		order_lines = [(5,0)]
		for line in order.line_items:
			tax_lines = [t.to_dict() for t in getattr(line, 'tax_lines', [])]
			order_line_data = {
				'line_name'                : line.title,
				'line_product_id'          : line.product_id,
				'line_variant_ids'         : line.variant_id,
				'line_price_unit'          : line.price,
				'line_product_uom_qty'     : line.quantity,
				'line_product_default_code': line.sku,
				'line_taxes': [] if all(t.get('price') in ["0", "0.00", 0, 0.0] for t in tax_lines) else self.process_tax(line, order.taxes_included),
			}
			order_lines.append((0,0,order_line_data))

		for line in order.shipping_lines:
			tax_lines = [t.to_dict() for t in getattr(line, 'tax_lines', [])]
			delivery_line_data = {
				'line_name'                : 'Delivery: {}'.format(line.title),
				'line_product_id'          : line.id,
				'line_price_unit'          : line.price,
				'line_product_uom_qty'     : 1,
				'line_product_default_code': line.code,
				'line_taxes'               : [] if all(t.get('price') in ["0", "0.00", 0, 0.0] for t in tax_lines) else self.process_tax(line, order.taxes_included),
				'line_source'              : 'delivery',
			}
			order_lines.append((0,0,delivery_line_data))
			
		## ========= Discount Tax Collection Logic ========= #Abhishek
		discount_tax_lines = []
		seen_tax_keys = set()

		for item in order.line_items:
			has_discount = item.discount_allocations and any(float(d.amount) > 0 for d in item.discount_allocations)
			has_tax = item.tax_lines and any(float(t.price) > 0 for t in item.tax_lines)

			if has_discount and has_tax:
				for tax in item.tax_lines:
					tax_key = f"{tax.title}_{tax.rate}"
					if tax_key not in seen_tax_keys:
						seen_tax_keys.add(tax_key)
						discount_tax_lines.extend(self.process_tax(item, order.taxes_included))

		# ========= Discount Lines ========= #Abhishek
		discount_sum = 0
		for line in order.discount_codes:
			discount_line_data = {
				'line_name': f"Discount: {line.code}",
				'line_product_id': line.code,
				'line_price_unit': line.amount,
				'line_product_uom_qty': 1,
				'line_product_default_code': line.code,
				'line_taxes': discount_tax_lines,
				'line_source': 'discount',
			}
			if line.amount:
				discount_sum += float(line.amount)
			order_lines.append((0, 0, discount_line_data))

		# ========= Remaining Discount Adjustment ========= #Abhishek
		current_total_discounts = float(order.current_total_discounts)
		remaining_discount = current_total_discounts - discount_sum
		if current_total_discounts and remaining_discount:
			discount_line_data = {
				'line_name': 'Discount',
				'line_product_id': 'Discount',
				'line_price_unit': round(remaining_discount, 3),
				'line_product_uom_qty': 1,
				'line_product_default_code': '',
				'line_taxes': discount_tax_lines,
				'line_source': 'discount',
			}
			order_lines.append((0, 0, discount_line_data))

		# #========================================
		# if order.total_tax and float(order.total_tax) > 0:
		# 	tax_total_line = {
		# 		'line_name'                : 'Tax Total Amount',
		# 		'line_product_id'          : 'Tax',
		# 		'line_price_unit'          : float(order.total_tax),
		# 		'line_product_uom_qty'     : 1,
		# 		'line_product_default_code': 'TAX',
		# 		'line_taxes'               : [],
		# 		'line_source'              : 'tax',
		# 	}
		# 	order_lines.append((0, 0, tax_total_line))

		order_data['line_ids'] = order_lines
		return order_data


Bridge.process_order = process_order


def process_customer(self,customer):
		name = customer.first_name or ''
		customer_vat=''
		if name:
			name = name + ' '
		name += customer.last_name or ''
		if hasattr(customer, 'metafields'):
				metafields= customer.metafields()
				for metafield in metafields:
					if metafield.key == 'tax_id':
						customer_vat = metafield.value
						pass
		customer_data = {
			'channel_id': self.id,
			'store_id'  : customer.id,
			'name'      : name or customer.email,
			'email'     : customer.email,
			'mobile'    : customer.phone,
			'vat'        : customer_vat,
			'customer_tag' : customer.tags
			
		}
		
		
		if customer.addresses:
			address_data_list = []
			if hasattr(customer, 'default_address'):
				temp_address = self.process_address(customer.default_address,type='customer')
				address_data_list = [temp_address]
			company=''
			for address in customer.addresses:
				if not company:
					company = address.company
				if hasattr(customer, 'default_address') and  address.id != customer.default_address.id:
					temp_address = self.process_address(address,type='customer')
					temp_address.update(
						{
							'channel_id': self.id,
							'parent_id' : address.customer_id,
							'store_id'  : address.id,
						}
					)
					address_data_list.append(temp_address)
					
				
			customer_data['company_name'] = company

			customer_data['contacts'] = address_data_list
			
		return customer_data

Bridge.process_customer = process_customer

def pre_get(self,kw):
	options = {}
	if kw.get('filter_type') == 'data_range':
		created_at_min = kw.get('created_at_min')
		created_at_max = kw.get('created_at_max')
		updated_at_min = kw.get('updated_at_min')
		updated_at_max = kw.get('updated_at_max')
		if created_at_min:
			options['created_at_min'] = created_at_min
		if created_at_max:
			options['created_at_max'] = created_at_max
		if updated_at_min:
			options['updated_at_min'] = updated_at_min
		if updated_at_max:
			options['updated_at_max'] = updated_at_max
		options['order']="created_at asc"
	elif kw.get('filter_type') == 'since_id':
		options['since_id'] = kw.get('last_id') or kw.get('since_id') or 0
	if 'limit' in kw:
		options['limit'] = min(kw['limit'],kw['page_size'])
	else:
		options['limit'] = kw['page_size']
	if 'next_url' in kw:
		options['next_url'] = kw['next_url']
	return options

Bridge.pre_get = pre_get
