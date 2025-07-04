# -*- coding: utf-8 -*-
#################################################################################
##    Copyright (c) 2018-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#    You should have received a copy of the License along with this program.
#    If not, see <https://store.webkul.com/license.html/>
#################################################################################

import json
import logging
import requests
import traceback
import math

from datetime import datetime
from odoo import api, fields , models
from odoo.exceptions import ValidationError, UserError

_logger = logging.getLogger(__name__)


class ShipStationDeliveryCarrier(models.Model):
    _inherit="delivery.carrier"

    # @api.model
    # def shipstation_get_shipping_price(self,order):
    #     try :
    #         path = '/shipments/getrates'
    #         shipper_info = self.get_shipment_shipper_address(order)
    #         recipient_info  = self.get_shipment_recipient_address(order)

    #         total_weight = self._get_weight(order)

    #         data = {
    #             'carrierCode' : self.shipstation_carrier_id.carrier_code,
    #             'serviceCode' : self.service_id.service_code,
    #             'packageCode' : self.package_id.package_code,
    #             'fromPostalCode' : shipper_info.get('zip'),
    #             'toState' : recipient_info.get('state_code'),
    #             'toCountry' : recipient_info.get('country_code'),
    #             'toPostalCode' : recipient_info.get('zip'),
    #             'toCity' : recipient_info.get('city'),
    #             'weight' : {
    #                 'value' : round(total_weight,2),
    #                 'units' : self.weight_unit,
    #             },
    #             'confirmation' : self.delivery_confirmation if self.delivery_confirmation else 'none',
    #             'residential' : True if self.address_type == 'residential' else False
    #         }
    #         piece_data = []
    #         package_items = self.wk_get_order_package(order=order)
    #         items = self.wk_group_by('packaging_id', package_items)

    #         for order_packaging_id, wk_package_ids in items:
    #             for package_id in wk_package_ids:
    #                 weight = package_id.get('weight')
    #                 total_weight += weight
    #                 piece_data.append({
    #                     'length' : package_id.get('length'),
    #                     'width' : package_id.get('width'),
    #                     'height' : package_id.get('height'),
    #                     'units' : self.package_unit,
    #                 })
    #         if piece_data:
    #             data['dimensions'] = piece_data[0]
    #         request = requests.request('POST', url=self.shipstation_user_id.request_url+path, headers=self.shipstation_user_id.request_header(), data=json.dumps(data))
    #         _logger.info("##########request-ans===%r=="%(data))
    #         _logger.info("##########request-ans===%r=="%(request.json()))
    #         json_data = request.json()
    #         if request.status_code in [200]:
    #             response = {
    #                 'success':True
    #             }
    #             for element in json_data:
    #                 response['price'] = element.get('shipmentCost')
    #             return response
    #         else:
    #             raise UserError("%r"%json_data.get('ExceptionMessage'))
    #     except Exception as e:
    #         raise UserError("Error: %r"%e)

    @api.model
    def shipstation_get_shipping_price(self, order):
        try:
            path = '/shipments/getrates'
            shipper_info = self.get_shipment_shipper_address(order)
            recipient_info = self.get_shipment_recipient_address(order)
            total_weight = self._get_weight(order)

            max_weight = self.package_id.max_weight
            if not max_weight:
                raise UserError("Please specify the maximum weight for the package.")
            if not all([self.package_id.length, self.package_id.width, self.package_id.height]):
                raise ValidationError("Please provide valid package dimensions: length, width, and height.")
            num_packages = math.ceil(total_weight / max_weight)

            total_shipping_cost = 0.0

            for i in range(num_packages):
                part_weight = min(max_weight, total_weight - (i * max_weight))
                data = {
                    'carrierCode': self.shipstation_carrier_id.carrier_code,
                    'serviceCode': self.service_id.service_code,
                    'packageCode': self.package_id.package_code,
                    'fromPostalCode': shipper_info.get('zip'),
                    'toState': recipient_info.get('state_code'),
                    'toCountry': recipient_info.get('country_code'),
                    'toPostalCode': recipient_info.get('zip'),
                    'toCity': recipient_info.get('city'),
                    'weight': {
                        'value': round(part_weight, 2),
                        'units': self.weight_unit,
                    },
                    'dimensions': {
                        'length': self.package_id.length,
                        'width': self.package_id.width,
                        'height': self.package_id.height,
                        'units': self.package_unit,
                    },
                    'confirmation': self.delivery_confirmation if self.delivery_confirmation else 'none',
                    'residential': True if self.address_type == 'residential' else False
                }

                _logger.info("##########request-payload===%r==" % data)

                request = requests.request(
                    'POST',
                    url=self.shipstation_user_id.request_url + path,
                    headers=self.shipstation_user_id.request_header(),
                    data=json.dumps(data)
                )

                _logger.info("##########response-json===%r==" % request.json())

                json_data = request.json()

                if request.status_code == 200:
                    for element in json_data:
                        cost = element.get('shipmentCost', 0.0)
                        total_shipping_cost += cost
                else:
                    raise UserError("%r" % json_data.get('ExceptionMessage'))

            return {
                'success': True,
                'price': total_shipping_cost
            }
        except Exception as e:
            raise UserError("Error: %r" % e)

    @api.model
    def shipstation_rate_shipment(self, order):
        response = self.shipstation_get_shipping_price(order)
        _logger.info("##########11order===%r==%r=="%(order,response))
        if not response.get('error_message'):response['error_message'] = None
        if not response.get('price'):response['price'] = 0
        if not response.get('warning_message'):response['warning_message'] = None
        if not response.get('success'):return response
        price = self.convert_shipment_price(response)
        response['price'] = price
        _logger.info("##########22order===%r==%r=="%(order,response))
        return response

    # def shipstation_send_shipping(self,pickings):
    #     try:
    #         for obj in self:
    #             path = '/orders/createorder'
    #             result = {
    #                 'exact_price': 0,
    #                 'weight': 0,
    #                 'date_delivery': None,
    #                 'tracking_number': '',
    #                 'attachments': []
    #             }
    #             if not pickings.carrier_tracking_ref:
    #                 raise UserError("Please Generate Shipstation Label First!!")

    #             if len(pickings.package_ids)>1:
    #                 raise UserError("More than one package found!! Shipstation does not support multiple package currently.")

    #             shipper_info = obj.get_shipment_shipper_address(picking=pickings)
    #             recipient_info  = obj.get_shipment_recipient_address(picking=pickings)
    #             data = {}
    #             data['orderNumber'] = pickings.shipstation_order_number
    #             data['orderKey'] = pickings.shipstation_order_key or pickings.sale_id.generate_order_key()
    #             data['orderDate'] = pickings.shipstation_order_date.strftime("%Y-%m-%dT%H:%M:%S.%f")
    #             data['shipByDate'] = pickings.scheduled_date.strftime("%Y-%m-%dT%H:%M:%S.%f")
    #             data['orderStatus'] = 'shipped'
    #             data['customerId'] = pickings.partner_id.shipstation_customer_id
    #             data['customerUsername'] = pickings.partner_id.email or ""
    #             data['customerEmail'] = pickings.partner_id.email or ""
    #             data['billTo'] =  {
    #                 'name' : shipper_info.get('name'),
    #                 'street1' : shipper_info.get('street'),
    #                 'street2' : shipper_info.get('street2') if shipper_info.get('street2') else '',
    #                 'city' : shipper_info.get('city'),
    #                 'state' : shipper_info.get('state_code'),
    #                 'postalCode' : shipper_info.get('zip'),
    #                 'country' : shipper_info.get('country_code'),
    #                 'phone' : shipper_info.get('phone'),
    #             }
    #             data['shipTo'] = {
    #                 'name' : recipient_info.get('name'),
    #                 'street1' : recipient_info.get('street'),
    #                 'street2' : recipient_info.get('street2') if recipient_info.get('street2') else '',
    #                 'city' : recipient_info.get('city'),
    #                 'state' : recipient_info.get('state_code'),
    #                 'postalCode' : recipient_info.get('zip'),
    #                 'country' : recipient_info.get('country_code'),
    #                 'phone' : recipient_info.get('phone'),
    #             }
    #             items = []
    #             for line in pickings.sale_id.order_line:
    #                 if line.product_id.default_code != 'Delivery':
    #                     itm_data = {
    #                         'sku' : line.product_id.default_code,
    #                         'name' : line.product_id.name,
    #                         'weight' : {
    #                             'value' : line.product_id.weight,
    #                             'units' : self.weight_unit,
    #                         },
    #                         'quantity' : int(line.product_uom_qty),
    #                         'unitPrice' : line.price_subtotal/line.product_uom_qty,
    #                         'taxAmount' : line.price_tax/line.product_uom_qty
    #                     }
    #                     items.append(itm_data)
    #             data['items'] = items
    #             data['amountPaid'] = pickings.sale_id.amount_total
    #             data['taxAmount'] = pickings.sale_id.amount_tax
    #             data['shippingAmount'] = pickings.sale_id.shipstation_delivery_amount
    #             data['carrierCode'] = pickings.carrier_id.shipstation_carrier_id.carrier_code
    #             data['serviceCode'] = pickings.carrier_id.service_id.service_code
    #             data['packageCode'] = pickings.carrier_id.package_id.package_code
    #             data['weight'] = {
    #                 'value' : sum(pickings.package_ids.mapped('shipping_weight')),
    #                 'units' : self.weight_unit
    #             }
    #             data['dimensions'] = {
    #                     'length' : pickings.package_ids.length,
    #                     'width' : pickings.package_ids.width,
    #                     'height' : pickings.package_ids.height,
    #                     'units' : pickings.carrier_id.package_unit
    #                 }
    #             if self.shipstation_store_id:
    #                 data['advancedOptions'] = {
    #                     'storeId' : self.shipstation_store_id.store_id
    #                 }
    #             request = requests.request('POST', url=pickings.carrier_id.shipstation_user_id.request_url+path, headers=pickings.carrier_id.shipstation_user_id.request_header(), data=json.dumps(data))
    #             _logger.info("######data===%r####request-ans===%r=="%(data,request.json()))
    #             json_data = request.json()
    #             if request.status_code not in [200]:
    #                 response_error = self.shipstation_user_id.check_error_response(json_data)
    #                 if response_error.get('error'):
    #                    raise UserError(response_error.get('error_message')+" "+response_error.get('message_details')+" "+response_error.get('message_exception')) 
    #             pickings.sale_id.sudo().write({
    #                 "shipstation_order_status":json_data.get("orderStatus"),
    #                 "shipstation_shipped_date":json_data.get('shipByDate') and datetime.strptime(json_data.get('shipByDate').split('.')[0], "%Y-%m-%dT%H:%M:%S"),
    #                 "shipstation_customer_id":json_data.get("customerId")
    #             })
    #             result['tracking_number'] = pickings.carrier_tracking_ref
    #             #pickings.carrier_id.shipstation_user_id.get_shipstation_orders()
    #             return result
    #     except Exception as e:
    #         raise UserError(e)

    def shipstation_send_shipping(self, pickings):
        if pickings.picking_type_id.sequence_code == 'OUT':
            try:
                for obj in self:
                    path = '/orders/createorder'
                    result = {
                        'exact_price': 0,
                        'weight': 0,
                        'date_delivery': None,
                        'tracking_number': '',
                        'attachments': []
                    }

                    if not pickings.carrier_tracking_ref:
                        raise UserError("Please Generate Shipstation Label First!!")

                    if not pickings.package_ids:
                        raise UserError("No package found. Please create a package first!")

                    for package in pickings.package_ids:
                        shipper_info = obj.get_shipment_shipper_address(picking=pickings)
                        recipient_info = obj.get_shipment_recipient_address(picking=pickings)
                        
                        data = {
                            'orderNumber': pickings.shipstation_order_number,
                            'orderKey': pickings.shipstation_order_key or pickings.sale_id.generate_order_key(),
                            'orderDate': pickings.shipstation_order_date.strftime("%Y-%m-%dT%H:%M:%S.%f"),
                            'shipByDate': pickings.scheduled_date.strftime("%Y-%m-%dT%H:%M:%S.%f"),
                            'orderStatus': 'shipped',
                            'customerId': pickings.partner_id.shipstation_customer_id,
                            'customerUsername': pickings.partner_id.email or "",
                            'customerEmail': pickings.partner_id.email or "",
                            'billTo': {
                                'name': shipper_info.get('name'),
                                'street1': shipper_info.get('street'),
                                'street2': shipper_info.get('street2') or '',
                                'city': shipper_info.get('city'),
                                'state': shipper_info.get('state_code'),
                                'postalCode': shipper_info.get('zip'),
                                'country': shipper_info.get('country_code'),
                                'phone': shipper_info.get('phone'),
                            },
                            'shipTo': {
                                'name': recipient_info.get('name'),
                                'street1': recipient_info.get('street'),
                                'street2': recipient_info.get('street2') or '',
                                'city': recipient_info.get('city'),
                                'state': recipient_info.get('state_code'),
                                'postalCode': recipient_info.get('zip'),
                                'country': recipient_info.get('country_code'),
                                'phone': recipient_info.get('phone'),
                            },
                            'items': [],
                            'amountPaid': pickings.sale_id.amount_total,
                            'taxAmount': pickings.sale_id.amount_tax,
                            'shippingAmount': pickings.sale_id.shipstation_delivery_amount,
                            'carrierCode': pickings.carrier_id.shipstation_carrier_id.carrier_code,
                            'serviceCode': pickings.carrier_id.service_id.service_code,
                            'packageCode': pickings.carrier_id.package_id.package_code,
                            'weight': {
                                'value': package.shipping_weight,
                                'units': self.weight_unit
                            },
                            'dimensions': {
                                'length': package.length,
                                'width': package.width,
                                'height': package.height,
                                'units': pickings.carrier_id.package_unit
                            }
                        }

                        # Add advanced options if store ID is set
                        if self.shipstation_store_id:
                            data['advancedOptions'] = {
                                'storeId': self.shipstation_store_id.store_id
                            }

                        # Build item lines
                        for line in pickings.sale_id.order_line:
                            if line.product_id.default_code != 'Delivery':
                                data['items'].append({
                                    'sku': line.product_id.default_code,
                                    'name': line.product_id.name,
                                    'weight': {
                                        'value': line.product_id.weight,
                                        'units': self.weight_unit,
                                    },
                                    'quantity': int(line.product_uom_qty),
                                    'unitPrice': line.price_subtotal / line.product_uom_qty,
                                    'taxAmount': line.price_tax / line.product_uom_qty
                                })

                        # Send request
                        request = requests.request(
                            'POST',
                            url=pickings.carrier_id.shipstation_user_id.request_url + path,
                            headers=pickings.carrier_id.shipstation_user_id.request_header(),
                            data=json.dumps(data)
                        )

                        _logger.info("######data===%r####request-ans===%r==" % (data, request.json()))

                        json_data = request.json()

                        if request.status_code not in [200]:
                            response_error = self.shipstation_user_id.check_error_response(json_data)
                            if response_error.get('error'):
                                raise UserError(
                                    f"{response_error.get('error_message')} "
                                    f"{response_error.get('message_details')} "
                                    f"{response_error.get('message_exception')}"
                                )

                        # Write shipment status to sale
                        pickings.sale_id.sudo().write({
                            "shipstation_order_status": json_data.get("orderStatus"),
                            "shipstation_shipped_date": json_data.get('shipByDate') and datetime.strptime(json_data.get('shipByDate').split('.')[0], "%Y-%m-%dT%H:%M:%S"),
                            "shipstation_customer_id": json_data.get("customerId")
                        })

                    # Assuming one tracking number per picking (first one), update result
                    result['tracking_number'] = pickings.carrier_tracking_ref
                    return result

            except Exception as e:
                raise UserError(e)


    @api.model
    def shipstation_get_tracking_link(self, picking):
        if not self.shipstation_tracking_link:
            raise UserError(f"Please add the tracking link in the {self.name} shipping method")
        return self.shipstation_tracking_link.strip() + picking.carrier_tracking_ref
        
