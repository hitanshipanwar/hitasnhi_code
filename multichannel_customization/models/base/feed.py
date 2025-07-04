# -*- coding: utf-8 -*-
#################################################################################
#
#   Copyright (c) 2016-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#    See LICENSE file for full copyright and licensing details.
#################################################################################
from odoo import api, fields, models, _
from odoo.addons.odoo_multi_channel_sale.tools import parse_float, extract_list as EL
import requests
import logging

_logger = logging.getLogger(__name__)


class WkFeed(models.Model):
    _inherit = 'wk.feed'


    @api.model
    def get_order_partner_id(self, store_partner_id, channel_id):
        
       
        if channel_id.channel != 'shopify' or not channel_id.import_company_with_order:
            return super(WkFeed,self).get_order_partner_id(store_partner_id, channel_id)
        partner_obj = self.env['res.partner']
        message = ''
        partner_id = None
        company_id = None
        partner_invoice_id = None
        partner_shipping_id = None
        context = dict(self._context)
        context['no_mapping'] = self.customer_is_guest
        try:
            #===============Ref.Ticket: 569841 (Company Contact Customization)===========
            company_id = self.with_context(context).create_company_contact_id(channel_id)
            partner_id = self.with_context(context).create_partner_contact_id(
                company_id, channel_id, store_partner_id)
            
            #==================
            partner_invoice_id = self.with_context(context).create_partner_invoice_id(
                partner_id, channel_id, self.invoice_partner_id)
            if self.same_shipping_billing:
                partner_shipping_id = partner_invoice_id
            else:
                partner_shipping_id = self.with_context(context).create_partner_shipping_id(
                    partner_id, channel_id, self.shipping_partner_id)
            
        except Exception as e:
            message += e.args[0]
        return dict(
            partner_id=partner_id,
            partner_shipping_id=partner_shipping_id,
            partner_invoice_id=partner_invoice_id,
            message=message
        )

   

   
    @api.model
    def get_company_contact_vals(self, channel_id):
       
        name = self.company_name
        tags=self.customer_tag
        list_tag=[]
        if tags:
            tags = [item.strip() for item in tags.split(',')]
            for rec in tags:
                tag=self.env['res.partner.category'].search([('name','ilike',rec)],limit=1)
                if not tag:
                    tag=self.env['res.partner.category'].create({'name':rec})
                list_tag.append(tag.id)
        
        vals = dict(
            name=name,
            email=self.customer_email,
            phone=self.customer_phone,
            mobile=self.customer_mobile,
            vat=self.customer_vat,
            is_company=True,
        )
        if list_tag:
            vals['category_id']=[(6,0,list_tag)]
        if not self.customer_vat:
            vals.pop("vat")
        return vals
    
    @api.model
    def create_company_contact_id(self, channel_id):
        match = None
        erp_id=None
        partner_obj = self.env['res.partner']
    
        if self.company_name:
            vals=self
            vals =self.get_company_contact_vals(channel_id)
            domain=[('name','=',self.company_name),('is_company','=',True)]
            if self.customer_vat:
                domain.append(('vat','=',self.customer_vat))
            match=partner_obj.search(domain, limit=1)
            if match:
                match.write(vals)
                erp_id = match
            else:
                erp_id = partner_obj.create(vals)
        return erp_id


    
    @api.model
    def get_partner_contact_vals(self, partner_id, channel_id):
        vals=super(WkFeed,self).get_partner_contact_vals(partner_id, channel_id)
        if channel_id.channel == 'shopify' and  channel_id.import_company_with_order :
            if vals and partner_id:
                vals['parent_id']=partner_id.id
        return vals

   
class OrderFeed(models.Model):
    _inherit = 'order.feed'

    def import_order(self, channel_id):
        if channel_id.channel != 'shopify':
            return super(OrderFeed,self).import_order(channel_id)
        message = ""
        update_id = None
        create_id = None
        self.ensure_one()
        vals = EL(self.read(self.get_order_fields()))
        _logger.info(vals)
        
        if vals.get('name'):                                ###### Store name in source document ######
            vals['origin'] = vals.get('name')
            
        store_id = vals.pop('store_id')
        access_token = channel_id.api_key
        if access_token and store_id:
            shop_url = channel_id.url.replace("http://", "https://")
            endpoint = f"{shop_url}/admin/api/2025-04/orders/{store_id}/transactions.json"
            headers = {
                "Content-Type": "application/json",
                "X-Shopify-Access-Token": access_token,
            }

            response = requests.get(endpoint, headers=headers)
            _logger.info("response *********** %s", response)

            if response.status_code != 200:
                _logger.info(f"Error fetching transactions: {response.status_code} - {response.text}")

            transactions = response.json().get('transactions', [])
            _logger.info("transactions ********* %s", transactions)

            if not transactions:
                _logger.info("No transactions found for this order.")

            # transaction_data = False
            # if len(transactions) == 1:
            #     txn = transactions[0]
            #     if not txn.get('parent_id'):
            #         transaction_data = txn
            # else:
            #     for txn in transactions:
            #         if not txn.get('parent_id') and txn.get('status') == 'success':
            #             transaction_data = txn
            #             break

            # Authorization
            transaction_data = next(
                (txn for txn in transactions
                 if not txn.get('parent_id') and (len(transactions) == 1 or txn.get('status') == 'success') 
                 and txn.get('kind') == 'authorization'),
                False
            ) # Abhishek

            # Sale transaction
            if not transaction_data:
                transaction_data = next(
                    (txn for txn in transactions
                     if not txn.get('parent_id') and (len(transactions) == 1 or txn.get('status') == 'success') 
                     and txn.get('kind') == 'sale'),
                    False
                ) # Abhishek

            if transaction_data:
                payment_id = transaction_data.get('payment_id')
                gateway = transaction_data.get('gateway')
                payment_id_trimmed = False
                if payment_id and gateway and gateway.startswith('authorize'):
                    payment_id_trimmed = payment_id[:-5] if payment_id else ''
                else:
                    payment_id_trimmed = payment_id
                txn_amount = transaction_data.get('amount')
                txn_status = transaction_data.get('status')
                vals['shopify_payment_id'] = payment_id_trimmed
                vals['txn_amount_shopify'] = txn_amount
                vals['txn_status'] = txn_status

            # Capture
            transaction_data_capture = next(
                (txn for txn in transactions
                 if (len(transactions) == 1 or txn.get('status') == 'success')
                 and txn.get('kind') == 'capture'),
                False
            ) #Abhishek

            if transaction_data_capture:
                gateway_capture = transaction_data_capture.get('gateway')
                payment_id_capture = False
                if gateway_capture and gateway_capture.startswith('authorize'):
                    payment_id_capture = transaction_data_capture.get('payment_id')
                txn_amount_capture = transaction_data_capture.get('amount')
                txn_status_capture = transaction_data_capture.get('status')
                vals['shopify_payment_id_capture'] = payment_id_capture 
                vals['txn_amount_shopify_capture'] = txn_amount_capture
                vals['txn_status_capture'] = txn_status_capture

            # Refund
            transaction_data_refund = next(
                (txn for txn in transactions
                 if (len(transactions) == 1 or txn.get('status') == 'success')
                 and txn.get('kind') == 'refund'),
                False
            ) #Abhishek

            if transaction_data_refund:
                gateway_refund = transaction_data_refund.get('gateway')
                payment_id_refund = False
                if gateway_refund and gateway_refund.startswith('authorize'):
                    payment_id_refund = transaction_data_refund.get('receipt', {}).get('network_trans_id')
                txn_amount_refund = transaction_data_refund.get('amount')
                txn_status_refund = transaction_data_refund.get('status')
                vals['shopify_payment_id_refund'] = payment_id_refund 
                vals['txn_amount_shopify_refund'] = txn_amount_refund
                vals['txn_status_refund'] = txn_status_refund

        store_source = vals.pop('store_source')
        match = self._context.get('order_mappings').get(channel_id.id, {}).get(store_id)
        if match:
            match = self.env['channel.order.mappings'].browse(match)
        state = 'done'
        store_partner_id = vals.pop('partner_id')

        date_info = self.get_order_date_info(channel_id, vals)
        if date_info.get('confirmation_date'):
            vals['date_order'] = date_info.get('confirmation_date')
        elif date_info.get('date_order'):
            vals['date_order'] = date_info.get('date_order')

        # date_invoice = date_info.get('date_invoice')
        # date_shipping = date_info.get('date_shipping')
        if date_info.get('date_invoice'):
            date_invoice = date_info.get('date_invoice')
        else:
            date_invoice = vals.get('date_order')
        
        if date_info.get('date_shipping'):
            date_shipping = date_info.get('date_shipping')
        else:
            date_shipping = date_info.get('date_order')

        confirmation_date = date_info.get('confirmation_date')

        if store_partner_id and self.customer_name:
            if not match:
                if store_partner_id == 'missing':
                    vals['partner_id'] = channel_id.default_customer_id.id
                    vals['partner_invoice_id'] = channel_id.default_customer_id.id
                    vals['partner_shipping_id'] = channel_id.default_customer_id.id
                else:
                    res_partner = self.get_order_partner_id(store_partner_id, channel_id)
                    message += res_partner.get('message', '')
                    partner_id = res_partner.get('partner_id')
                    partner_invoice_id = res_partner.get('partner_invoice_id')
                    partner_shipping_id = res_partner.get('partner_shipping_id')
                    if partner_id and partner_invoice_id and partner_shipping_id:
                        company=partner_id.parent_id
                        if company and company.is_company and channel_id.import_company_with_order:
                            vals['partner_id'] = company.id
                        else:
                            vals['partner_id'] = partner_id.id
                        vals['partner_invoice_id'] = partner_invoice_id.id
                        vals['partner_shipping_id'] = partner_shipping_id.id
                    else:
                        message += '<br/>Partner,Invoice,Shipping Address must present.'
                        state = 'error'
                        _logger.error('#OrderError1 %r' % message)
        else:
            message += '<br/>No partner in sale order data.'
            state = 'error'
            _logger.error('#OrderError2 %r' % message)

        if state == 'done':
            carrier_id = vals.pop('carrier_id', '')

            if carrier_id:
                carrier_res = self.get_carrier_id(carrier_id, channel_id=channel_id)
                message += carrier_res.get('message')
                carrier_id = carrier_res.get('carrier_id')
                if carrier_id:
                    vals['carrier_id'] = carrier_id.id
            order_line_res = self._get_order_line_vals(vals, carrier_id, channel_id)
            message += order_line_res.get('message', '')
            if not order_line_res.get('status'):
                state = 'error'
                _logger.error('#OrderError3 %r' % order_line_res)
            else:
                order_line = order_line_res.get('order_line')
                if len(order_line):
                    vals['order_line'] = order_line
                    state = 'done'
        currency = self.currency

        if state == 'done' and currency:
            currency_id = channel_id.get_currency_id(currency)
            if not currency_id.active:
                if currency_id: # Currency Form View URL
                    currency = f'<strong><a href="/web#id={currency_id.id}&model=res.currency&view_type=form" target = "_blank">{currency}</a></strong>'
                message += '<br/> Currency %s no active in Odoo' % (currency)
                state = 'error'
                _logger.error('#OrderError4 %r' % message)
            else:
                pricelist_id = channel_id.match_create_pricelist_id(currency_id)
                vals['pricelist_id'] = pricelist_id.id
        if not (channel_id.order_ecomm_sequence and vals.get('name')):
            vals.pop('name')
        vals.pop('id')
        vals.pop('website_message_ids', '')
        vals.pop('message_follower_ids', '')

        if match and match.order_name:
            if state == 'done':
                try:
                    order_state = vals.pop('order_state')
                    if match.order_name.state == 'draft':
                        match.order_name.write(dict(order_line=[(5, 0)]))
                        extra_values = channel_id.get_order_extra_vals(vals, False)
                        vals.update(extra_values)
                        if match.order_name.note and vals['note']:
                            vals['note'] =  match.order_name.note+vals['note']
                        match.order_name.write(vals)
                        message += '<br/> Order %s successfully updated' % (vals.get('name', ''))
                    else:
                        message += 'Only order state can be update as order not in draft state. '
                    if match.order_name.state == 'cancel':
                        message += 'No changes made for this order as the odoo order is already cancelled. '
                    else:
                        message += self.env['multi.channel.skeleton']._SetOdooOrderState(match.order_name, channel_id,
                                                                                         order_state, self.payment_method, date_invoice=date_invoice, confirmation_date=confirmation_date, date_shipping=date_shipping)
                    if not match.store_order_status == order_state:
                        match.store_order_status = order_state
                except Exception as e:
                    message += '<br/>%s' % (e)
                    _logger.error('#OrderError5  %r' % message)
                    state = 'error'
                update_id = match
            elif state == 'error':
                message += '<br/>Error while order update.'
        else:
            if state == 'done':
                try:
                    order_state = vals.pop('order_state')
                    extra_values = channel_id.get_order_extra_vals(vals, True)
                    vals.update(extra_values)
                    erp_id = self.env['sale.order'].create(vals)
                    message += self.env['multi.channel.skeleton']._SetOdooOrderState(erp_id, channel_id, order_state, self.payment_method, date_invoice=date_invoice, confirmation_date=confirmation_date,date_shipping=date_shipping)
                    message += '<br/> Order %s successfully evaluated' % (self.store_id)
                    create_id = channel_id.create_order_mapping(erp_id, store_id, store_source, order_state)

                except Exception as e:
                    message += '<br/>%s' % (e)
                    _logger.error('#OrderError6 %r' % message)
                    state = 'error'
        self.set_feed_state(state=state)
        self.message = "%s <br/> %s" % (message, self.message)
        vals= dict(
            create_id=create_id,
            update_id=update_id,
            message=message
        )
        #"================================================"
        
        order=vals.get('create_id') or vals.get('update_id')
        
        tags=self.order_tag
        if tags and order:
            tags = [item.strip() for item in tags.split(',')]
            order=order.order_name
            list_tag=[]
            for rec in tags:
                tag=self.env['crm.tag'].search([('name','ilike',rec)],limit=1)
                if not tag:
                    tag=self.env['crm.tag'].create({'name':rec})
                list_tag.append(tag.id)
        
            order['tag_ids']=[(6,0,list_tag)]
        return vals
        
  

class PartnerFeed(models.Model):
    _inherit = 'partner.feed'


    @api.model
    def import_partner(self, channel_id):
        
        res=super(PartnerFeed,self).import_partner(channel_id)
        if channel_id.channel != 'shopify' or not channel_id.import_company_with_order:
            return res
       
        if self.company_name:
            company_id = self.create_customer_company_contact_id(channel_id)
            mapping_id = res.get('update_id') or res.get('create_id')
            if mapping_id:
                partner_id = mapping_id.odoo_partner
            if company_id and  partner_id.parent_id !=company_id.id:
                
                partner_id.parent_id=company_id.id
        return res

    @api.model
    def create_customer_company_contact_id(self, channel_id):
        match = None
        erp_id=None
        partner_obj = self.env['res.partner']
        

        if self.company_name:
            vals =self.get_customer_company_contact_vals(channel_id)
            domain=[('name','=',self.company_name),('is_company','=',True)]
            if self.vat:
                domain.append(('vat','=',self.vat))
            match=partner_obj.search(domain, limit=1)
           
            if match:
                match.write(vals)
                erp_id = match
            else:
                erp_id = partner_obj.create(vals)
        return erp_id

    @api.model
    def get_customer_company_contact_vals(self, channel_id):
        name = self.company_name
        tags=self.customer_tag
        list_tag=[]
        if tags:
            tags = [item.strip() for item in tags.split(',')]
            for rec in tags:
                tag=self.env['res.partner.category'].search([('name','ilike',rec)],limit=1)
                if not tag:
                    tag=self.env['res.partner.category'].create({'name':rec})
                list_tag.append(tag.id)
       
        vals = dict(
            name=name,
            email=self.email,
            phone=self.phone,
            mobile=self.mobile,
            vat=self.vat,
            is_company=True,
        )
        if list_tag:
            vals['category_id']=[(6,0,list_tag)]
        if not self.vat:
            vals.pop("vat")
        return vals

   
