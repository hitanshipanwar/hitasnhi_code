import logging
import requests
import binascii
import xml.etree.ElementTree as etree
import xml.etree.ElementTree as ET
from odoo import models, fields, api, _
from odoo.exceptions import Warning, ValidationError, UserError
from odoo.addons.purolator_shipping_integration.models.purolator_response import Response
import hashlib
from requests.auth import HTTPBasicAuth
from PyPDF2 import PdfFileMerger

import io
import base64
import uuid
import re
import time

_logger = logging.getLogger("Purolator")


class DeliveryCarrier(models.Model):
    _inherit = "delivery.carrier"

    delivery_type = fields.Selection(selection_add=[("purolator", "Purolator")],
                                     ondelete={'purolator': 'set default'})
    purolator_package_type = fields.Selection([("ExpressEnvelope", "ExpressEnvelope"),
                                               ("ExpressPack", "ExpressPack"),
                                               ("CustomerPackaging", "CustomerPackaging"),
                                               ("ExpressBox", "ExpressBox")])
    purolator_service = fields.Selection([("PurolatorGround", "PurolatorGround"),
                                            ("PurolatorExpress", "PurolatorExpress")], string="Purolator Service")
    weight_unit = fields.Selection([("lb", "lb - pounds"),
                                    ("kg", "kg - kilogram")])

    def purolator_rate_shipment(self, orders):
        "This Method Is Used For Get Rate"

        shipper_address = orders.warehouse_id and orders.warehouse_id.partner_id
        recipient_address = orders.partner_shipping_id

        if not shipper_address.zip or not shipper_address.city or not shipper_address.country_id:
            return {'success': False, 'price': 0.0,
                    'error_message': "Please Define Proper Sender Address!",
                    'warning_message': False}

        if not recipient_address.zip or not recipient_address.city or not recipient_address.country_id:
            return {'success': False, 'price': 0.0,
                    'error_message': "Please Define Proper Recipient Address!",
                    'warning_message': False}

        total_weight_in = sum(
        [(line.product_id.weight * line.product_uom_qty) for line in orders.order_line if not line.is_delivery])

        # Calculate the total weight and dimensions for each package
        packages_ids = self.env.context.get('packages', [])
        _logger.info("Request Data packages::::%s" % packages_ids)
        packages = []
        if not len(packages_ids):
            # packages = []
            weight = sum(
                [(line.product_id.weight * line.product_uom_qty) for line in orders.order_line if not line.is_delivery])
            weight_limit = 150
            pieces = []
            while weight > weight_limit:
                pieces.append(weight_limit)
                weight -= weight_limit
            if weight > 0:
                pieces.append(weight)
            for line in pieces:
                weight = str(line)
                length = "1"
                width = "1"
                height = "1"
                packages.append({
                    'weight': weight,
                    'length': length,
                    'width': width,
                    'height': height,
                })
        else:
            # packages = []
            for line in packages_ids:
                weight = str(line.shipping_weight)
                length = "1"
                width = "1"
                height = "1"
                packages.append({
                    'weight': weight,
                    'length': length,
                    'width': width,
                    'height': height,
                })

        # Create the root element with namespaces
        root = ET.Element("SOAP-ENV:Envelope", {
            "xmlns:SOAP-ENV": "http://schemas.xmlsoap.org/soap/envelope/",
            "xmlns:v2": "http://purolator.com/pws/datatypes/v2"
        })

        # Create the Header
        header = ET.SubElement(root, "SOAP-ENV:Header")
        request_context = ET.SubElement(header, "v2:RequestContext")
        ET.SubElement(request_context, "v2:Version").text = "2.0"
        ET.SubElement(request_context, "v2:Language").text = "en"
        ET.SubElement(request_context, "v2:GroupID").text = "xxx"
        ET.SubElement(request_context, "v2:RequestReference").text = "Rating Example"

        # Create the Body
        body = ET.SubElement(root, "SOAP-ENV:Body")
        get_full_estimate_request = ET.SubElement(body, "v2:GetFullEstimateRequest")

        # Add Shipment
        shipment = ET.SubElement(get_full_estimate_request, "v2:Shipment")

        # Add SenderInformation
        StreetNameShipper = ' '.join(filter(None, [shipper_address.street, shipper_address.street2]))
        sender_info = ET.SubElement(shipment, "v2:SenderInformation")
        sender_address = ET.SubElement(sender_info, "v2:Address")
        ET.SubElement(sender_address, "v2:Name").text = shipper_address.name or ''
        ET.SubElement(sender_address, "v2:StreetNumber").text = ""
        ET.SubElement(sender_address, "v2:StreetName").text = StreetNameShipper
        ET.SubElement(sender_address, "v2:City").text = shipper_address.city or ''
        ET.SubElement(sender_address, "v2:Province").text = shipper_address.state_id and shipper_address.state_id.code or ''
        ET.SubElement(sender_address, "v2:Country").text = shipper_address.country_id and shipper_address.country_id.code or ''
        ET.SubElement(sender_address, "v2:PostalCode").text = shipper_address.zip or ''
        shipper_area_code, shipper_phone = self.get_area_code_and_phone(shipper_address.phone)
        phone_number = ET.SubElement(sender_address, "v2:PhoneNumber")
        ET.SubElement(phone_number, "v2:CountryCode").text = "1"
        ET.SubElement(phone_number, "v2:AreaCode").text = shipper_area_code
        ET.SubElement(phone_number, "v2:Phone").text = shipper_phone

        # Add ReceiverInformation
        StreetNameRecipient = ' '.join(filter(None, [recipient_address.street, recipient_address.street2]))
        receiver_info = ET.SubElement(shipment, "v2:ReceiverInformation")
        receiver_address = ET.SubElement(receiver_info, "v2:Address")
        ET.SubElement(receiver_address, "v2:Name").text = recipient_address.name or ''
        ET.SubElement(receiver_address, "v2:StreetNumber").text = ""
        ET.SubElement(receiver_address, "v2:StreetName").text = StreetNameRecipient
        ET.SubElement(receiver_address, "v2:City").text = recipient_address.city or ''
        ET.SubElement(receiver_address, "v2:Province").text = recipient_address.state_id and recipient_address.state_id.code or ''
        ET.SubElement(receiver_address, "v2:Country").text = recipient_address.country_id and recipient_address.country_id.code or ''
        ET.SubElement(receiver_address, "v2:PostalCode").text = recipient_address.zip or ''
        recipient_area_code, recipient_phone = self.get_area_code_and_phone(recipient_address.phone)
        phone_number = ET.SubElement(receiver_address, "v2:PhoneNumber")
        ET.SubElement(phone_number, "v2:CountryCode").text = "1"
        ET.SubElement(phone_number, "v2:AreaCode").text = recipient_area_code
        ET.SubElement(phone_number, "v2:Phone").text = recipient_phone

        # Add PackageInformation
        package_info = ET.SubElement(shipment, "v2:PackageInformation")
        ET.SubElement(package_info, "v2:ServiceID").text = "PurolatorExpress"
        total_weight = ET.SubElement(package_info, "v2:TotalWeight")
        ET.SubElement(total_weight, "v2:Value").text = str(total_weight_in)
        ET.SubElement(total_weight, "v2:WeightUnit").text = self.weight_unit or ''
        ET.SubElement(package_info, "v2:TotalPieces").text = str(len(packages))

        for piece in packages:
            piece_info = ET.SubElement(package_info, "v2:PiecesInformation")
            _logger.info("Request Data piece_info::::%s" % piece_info)
            ET.SubElement(piece_info, "v2:Length").text = piece["length"]
            ET.SubElement(piece_info, "v2:Width").text = piece["width"]
            ET.SubElement(piece_info, "v2:Height").text = piece["height"]
            ET.SubElement(piece_info, "v2:Weight").text = piece["weight"]
            ET.SubElement(piece_info, "v2:WeightUnit").text = self.weight_unit or ''

        

        # Add OptionsInformation
        # options_info = ET.SubElement(package_info, "ns1:OptionsInformation")
        # options = ET.SubElement(options_info, "ns1:Options")
        # option_id_value_pair = ET.SubElement(options, "ns1:OptionIDValuePair")
        # ET.SubElement(option_id_value_pair, "ns1:ID").text = "DangerousGoods"
        # ET.SubElement(option_id_value_pair, "ns1:Value").text = "true"
        # option_id_value_pair = ET.SubElement(options, "ns1:OptionIDValuePair")
        # ET.SubElement(option_id_value_pair, "ns1:ID").text = "DangerousGoodsMode"
        # ET.SubElement(option_id_value_pair, "ns1:Value").text = "Air"
        # option_id_value_pair = ET.SubElement(options, "ns1:OptionIDValuePair")
        # ET.SubElement(option_id_value_pair, "ns1:ID").text = "DangerousGoodsClass"
        # ET.SubElement(option_id_value_pair, "ns1:Value").text = "FullyRegulated"

        # Add PaymentInformation
        payment_info = ET.SubElement(shipment, "v2:PaymentInformation")
        ET.SubElement(payment_info, "v2:PaymentType").text = "Sender"
        ET.SubElement(payment_info, "v2:RegisteredAccountNumber").text = self.company_id.purolator_account_number
        ET.SubElement(payment_info, "v2:BillingAccountNumber").text = self.company_id and self.company_id.purolator_account_number

        # Add PickupInformation
        pickup_info = ET.SubElement(shipment, "v2:PickupInformation")
        ET.SubElement(pickup_info, "v2:PickupType").text = "DropOff"

        # Add ShowAlternativeServicesIndicator
        ET.SubElement(get_full_estimate_request, "v2:ShowAlternativeServicesIndicator").text = "true"

        # Generate the XML string
        # base_data = etree.tostring(root)
        xml_str = ET.tostring(root, encoding='utf-8', method='xml')




        # root_element = etree.Element("soapenv:Envelope")
        # root_element.attrib['xmlns:soapenv'] = "http://schemas.xmlsoap.org/soap/envelope/"
        # root_element.attrib['xmlns:v2'] = "http://purolator.com/pws/datatypes/v2"

        # root_header = etree.SubElement(root_element, "soapenv:Header")
        # request_context = etree.SubElement(root_header, "v2:RequestContext")
        # etree.SubElement(request_context, "v2:Version").text = "2.2"
        # etree.SubElement(request_context, "v2:Language").text = "en"
        # etree.SubElement(request_context, "v2:GroupID").text = str((uuid.uuid4().int))[:4]
        # etree.SubElement(request_context, "v2:RequestReference").text = "rate"

        # root_body = etree.SubElement(root_element, "soapenv:Body")
        # root_getquickestimateRequest = etree.SubElement(root_body, "v2:GetQuickEstimateRequest")
        # etree.SubElement(root_getquickestimateRequest,
        #                  "v2:BillingAccountNumber").text = self.company_id and self.company_id.purolator_account_number
        # etree.SubElement(root_getquickestimateRequest, "v2:SenderPostalCode").text = sender_address.zip or ''
        # root_receiveraddress = etree.SubElement(root_getquickestimateRequest, "v2:ReceiverAddress")
        # etree.SubElement(root_receiveraddress, "v2:City").text = receiver_address.city or ''
        # etree.SubElement(root_receiveraddress,
        #                  "v2:Province").text = receiver_address.state_id and receiver_address.state_id.code or ''
        # etree.SubElement(root_receiveraddress,
        #                  "v2:Country").text = receiver_address.country_id and receiver_address.country_id.code or ''
        # etree.SubElement(root_receiveraddress, "v2:PostalCode").text = receiver_address.zip or ''

        # etree.SubElement(root_getquickestimateRequest, "v2:PackageType").text = self.purolator_package_type

        # # Add each package to the request
        # for package in packages:
        #     package_element = etree.SubElement(root_getquickestimateRequest, "v2:Package")
        #     weight_element = etree.SubElement(package_element, "v2:Weight")
        #     etree.SubElement(weight_element, "v2:Value").text = str(package['weight'])
        #     etree.SubElement(weight_element, "v2:WeightUnit").text = self.weight_unit
        #     etree.SubElement(package_element, "v2:Length").text = str(package['length'])
        #     etree.SubElement(package_element, "v2:Width").text = str(package['width'])
        #     etree.SubElement(package_element, "v2:Height").text = str(package['height'])
        #     # etree.SubElement(package_element, "v2:DimensionUnit").text = "in"  # or the appropriate unit

        # root_totalweight = etree.SubElement(root_getquickestimateRequest, "v2:TotalWeight")
        # weight = sum(
        # [(line.product_id.weight * line.product_uom_qty) for line in orders.order_line if not line.is_delivery])
        # etree.SubElement(root_totalweight, "v2:Value").text = str(weight)
        # etree.SubElement(root_totalweight, "v2:WeightUnit").text = self.weight_unit

        # base_data = etree.tostring(root_element)

        try:
            headers = {
                "Content-Type": "text/xml; charset=utf-8",
                "SOAPAction": "http://purolator.com/pws/service/v2/GetFullEstimate"
            }
            username = self.company_id.purolator_username
            password = self.company_id.purolator_password
            url = "{0}/v2/Estimating/EstimatingService.asmx".format(
                self.company_id and self.company_id.purolator_api_url)
            _logger.info("Request Data Of Rate::::%s" % xml_str)
            response_data = requests.request(method="POST", url=url, headers=headers,
                                             auth=HTTPBasicAuth(username=username, password=password),
                                             data=xml_str)
            _logger.info("Response Data Of Rate%s" % response_data.content)
            if response_data.status_code in [200, 201]:
                api = Response(response_data)
                response_data = api.dict()
                common_response = response_data.get('Envelope').get('Body').get('GetFullEstimateResponse')
                check_errors = common_response.get('ResponseInformation').get('Errors')
                if check_errors:
                    raise ValidationError(check_errors)

                purolator_shipping_charge_obj = self.env['purolator.shipping.charge']

                existing_records = purolator_shipping_charge_obj.search([('sale_order_id', '=', orders and orders.id)])
                existing_records.sudo().unlink()
                if common_response.get('ShipmentEstimates').get('ShipmentEstimate'):
                    rate_response_dicts = common_response.get('ShipmentEstimates').get('ShipmentEstimate')
                else:
                    raise ValidationError("Response Data : %s" % (response_data))
                if isinstance(rate_response_dicts, dict):
                    rate_response_dicts = [rate_response_dicts]
                for response_dict in rate_response_dicts:
                    purolator_service_id = response_dict.get('ServiceID')
                    expected_delivery_date = response_dict.get('ExpectedDeliveryDate')
                    estimated_transit_days = response_dict.get('EstimatedTransitDays')
                    purolator_total_charge = response_dict.get('TotalPrice')
                    purolator_shipping_charge_obj.sudo().create(
                        {
                            'purolator_service_id': purolator_service_id,
                            'expected_delivery_date': expected_delivery_date,
                            'estimated_transit_days': estimated_transit_days,
                            'purolator_total_charge': purolator_total_charge,
                            'sale_order_id': orders and orders.id
                        }
                    )
                purolator_charge_id = purolator_shipping_charge_obj.search(
                    [('sale_order_id', '=', orders and orders.id)], order='purolator_total_charge', limit=1)
                orders.purolator_shipping_charge_id = purolator_charge_id and purolator_charge_id.id
                return {'success': True,
                        'price': purolator_charge_id and purolator_charge_id.purolator_total_charge or 0.0,
                        'error_message': False, 'warning_message': False, 'base_data': xml_str}
            else:
                return {'success': False, 'price': 0.0,
                        'error_message': "%s %s" % (response_data, response_data.text),
                        'warning_message': False, 'base_data': xml_str}
        except Exception as e:
            _logger.error("An error occurred: %s", str(e))
            msg = str(e)
            picking = self.env['stock.picking'].search([('sale_id', '=', orders.id), ('picking_type_id.sequence_code', '=', 'OUT')])
            self.env.cr.commit()
            if picking:
                self.env.cr.commit()
                picking.message_post(body=msg)
                self.env.cr.commit()
            raise ValidationError(e)

    def get_area_code_and_phone(self, phone):
        digits = re.sub(r'\D', '', phone)
        if not phone or len(digits) < 10:
            raise ValidationError("Invalid phone number. Please provide a 10-digit phone number.")
        area_code = digits[-10:-7]
        phone_number = digits[-7:]
        return area_code, phone_number

    def purolator_send_shipping(self, pickings):
        """This Method Is Used For Sending The Shipping Request To Shipper"""
        has_package = any(line.result_package_id for line in pickings.move_line_ids_without_package)
        packages = []
        if not has_package:
            weight = sum(
                [(line.product_id.weight * line.qty_done) for line in pickings.move_line_ids_without_package])
            weight_limit = 150
            pieces = []
            while weight > weight_limit:
                pieces.append(weight_limit)
                weight -= weight_limit
            if weight > 0:
                pieces.append(weight)
            for line in pieces:
                weight = str(line)
                length = "1"
                width = "1"
                height = "1"
                packages.append({
                    'weight': weight,
                    'length': length,
                    'width': width,
                    'height': height,
                })
        else:
            for package in pickings.package_ids:
                weight = str(package.shipping_weight)
                length = "1"
                width = "1"
                height = "1"
                packages.append({
                    'weight': weight,
                    'length': length,
                    'width': width,
                    'height': height,
                })
        response = []
        for picking in pickings:
            recipient_address = picking.partner_id
            shipper_address = picking.picking_type_id.warehouse_id.partner_id
            # total_bulk_weight = picking.weight_bulk
            total_bulk_weight = picking.shipping_weight

            if not shipper_address.zip or not shipper_address.city or not shipper_address.country_id:
                raise ValidationError("Please define  proper sender addres")

            # check Receiver Address
            if not recipient_address.zip or not recipient_address.city or not recipient_address.country_id:
                raise ValidationError("Please define  proper receiver address")

            root_element = etree.Element("soapenv:Envelope")
            root_element.attrib['xmlns:soapenv'] = "http://schemas.xmlsoap.org/soap/envelope/"
            root_element.attrib['xmlns:v2'] = "http://purolator.com/pws/datatypes/v2"

            root_header = etree.SubElement(root_element, "soapenv:Header")
            request_context = etree.SubElement(root_header, "v2:RequestContext")
            etree.SubElement(request_context, "v2:Version").text = "2.2"
            etree.SubElement(request_context, "v2:Language").text = "en"
            etree.SubElement(request_context, "v2:GroupID").text = "1"
            etree.SubElement(request_context, "v2:RequestReference").text = "Shipping Request123"
            # etree.SubElement(request_context, "v2:UserToken").text = "b4a9f14b1dfd4315902eef4e0c4da56a"

            root_body = etree.SubElement(root_element, "soapenv:Body")
            root_createshipment = etree.SubElement(root_body, "v2:CreateShipmentRequest")
            root_shipment = etree.SubElement(root_createshipment, "v2:Shipment")
            root_senderinformation = etree.SubElement(root_shipment, "v2:SenderInformation")
            root_address = etree.SubElement(root_senderinformation, "v2:Address")

            StreetNameShipper = ' '.join(filter(None, [shipper_address.street, shipper_address.street2]))

            etree.SubElement(root_address, "v2:Name").text = shipper_address.name or ''
            etree.SubElement(root_address, "v2:StreetNumber").text = ''
            etree.SubElement(root_address, "v2:StreetName").text = StreetNameShipper
            etree.SubElement(root_address, "v2:City").text = shipper_address.city or ''
            etree.SubElement(root_address,
                             "v2:Province").text = shipper_address.state_id and shipper_address.state_id.code
            etree.SubElement(root_address,
                             "v2:Country").text = shipper_address.country_id and shipper_address.country_id.code
            etree.SubElement(root_address, "v2:PostalCode").text = shipper_address.zip or ''

            root_phonenumber = etree.SubElement(root_address, "v2:PhoneNumber")
            shipper_area_code, shipper_phone = self.get_area_code_and_phone(shipper_address.phone)
            etree.SubElement(root_phonenumber, "v2:CountryCode").text = "1"
            etree.SubElement(root_phonenumber, "v2:AreaCode").text = shipper_area_code
            etree.SubElement(root_phonenumber, "v2:Phone").text = shipper_phone

            root_receiverinformation = etree.SubElement(root_shipment, "v2:ReceiverInformation")
            root_recaddress = etree.SubElement(root_receiverinformation, "v2:Address")

            # StreetName = recipient_address.street
            # if not recipient_address.street and recipient_address.street2:
            #     StreetName = recipient_address.street2
            StreetNameRecipient = ' '.join(filter(None, [recipient_address.street, recipient_address.street2]))

            etree.SubElement(root_recaddress, "v2:Name").text = recipient_address.name or ''
            etree.SubElement(root_recaddress, "v2:StreetNumber").text = ''
            etree.SubElement(root_recaddress, "v2:StreetName").text = StreetNameRecipient
            etree.SubElement(root_recaddress, "v2:City").text = recipient_address.city or ''
            etree.SubElement(root_recaddress,
                             "v2:Province").text = recipient_address.state_id and recipient_address.state_id.code or ''
            etree.SubElement(root_recaddress,
                             "v2:Country").text = recipient_address.country_id and recipient_address.country_id.code or ''
            etree.SubElement(root_recaddress, "v2:PostalCode").text = recipient_address.zip or ''

            root_recphonenumber = etree.SubElement(root_recaddress, "v2:PhoneNumber")
            recipient_area_code, recipient_phone = self.get_area_code_and_phone(recipient_address.phone)
            etree.SubElement(root_recphonenumber, "v2:CountryCode").text = "1"
            etree.SubElement(root_recphonenumber, "v2:AreaCode").text = recipient_area_code
            etree.SubElement(root_recphonenumber, "v2:Phone").text = recipient_phone

            etree.SubElement(root_shipment, "v2:ShipmentDate").text = picking.scheduled_date.strftime("%Y-%m-%d")

            root_package_information = etree.SubElement(root_shipment, "v2:PackageInformation")
            etree.SubElement(root_package_information,
                             "v2:ServiceID").text = picking.carrier_id.purolator_service
            root_total_weight = etree.SubElement(root_package_information, "v2:TotalWeight")
            etree.SubElement(root_total_weight, "v2:Value").text = str(picking.shipping_weight) or ''
            etree.SubElement(root_total_weight, "v2:WeightUnit").text = self.weight_unit or ''

            etree.SubElement(root_package_information, "v2:TotalPieces").text = str(len(packages))
            piece_info = etree.SubElement(root_package_information, "v2:PiecesInformation")
            for piece in packages:
                piece_in = etree.SubElement(piece_info, "v2:Piece")
                _logger.info("Request Data piece_info::::%s" % piece_info)
                piece_total_weight = etree.SubElement(piece_in, "v2:Weight")
                etree.SubElement(piece_total_weight, "v2:Value").text = piece["weight"]
                etree.SubElement(piece_total_weight, "v2:WeightUnit").text = self.weight_unit or ''
                piece_total_length = etree.SubElement(piece_in, "v2:Length")
                etree.SubElement(piece_total_length, "v2:Value").text = piece["length"]
                etree.SubElement(piece_total_length, "v2:DimensionUnit").text = 'in'
                piece_total_Width = etree.SubElement(piece_in, "v2:Width")
                etree.SubElement(piece_total_Width, "v2:Value").text = piece["width"]
                etree.SubElement(piece_total_Width, "v2:DimensionUnit").text = 'in'
                piece_total_Height = etree.SubElement(piece_in, "v2:Height")
                etree.SubElement(piece_total_Height, "v2:Value").text = piece["height"]
                etree.SubElement(piece_total_Height, "v2:DimensionUnit").text = 'in'
                # etree.SubElement(piece_in, "v2:Weight").text = piece["weight"]
                # etree.SubElement(piece_in, "v2:WeightUnit").text = self.weight_unit or ''


            root_payment_information = etree.SubElement(root_shipment, "v2:PaymentInformation")
            etree.SubElement(root_payment_information, "v2:PaymentType").text = "Sender"
            etree.SubElement(root_payment_information, "v2:RegisteredAccountNumber").text = self.company_id.purolator_account_number
            etree.SubElement(root_payment_information, "v2:BillingAccountNumber").text = self.company_id.purolator_account_number

            root_pickup_information = etree.SubElement(root_shipment, "v2:PickupInformation")
            etree.SubElement(root_pickup_information, "v2:PickupType").text = "DropOff"

            root_notification_information = etree.SubElement(root_shipment, "v2:NotificationInformation")
            etree.SubElement(root_notification_information, "v2:ConfirmationEmailAddress").text = self.company_id.email

            etree.SubElement(root_createshipment, "v2:PrinterType").text = "Thermal"
            request_data = etree.tostring(root_element, encoding='utf-8', method='xml')
            _logger.info("=====>Request data of shipment%s" % request_data)

            try:
                headers = {
                    'Content-Type': "text/xml;  charset=utf-8",
                    'SOAPAction': "http://purolator.com/pws/service/v2/CreateShipment"
                }
                username = self.company_id.purolator_username
                password = self.company_id.purolator_password
                url = "{0}/v2/Shipping/ShippingService.asmx".format(
                    self.company_id and self.company_id.purolator_api_url)
                _logger.info("Request Data Of Shipping::::%s" % etree.tostring(root_element))
                response_data = requests.request(method="POST", url=url, headers=headers,
                                                 auth=HTTPBasicAuth(username=username, password=password),
                                                 data=etree.tostring(root_element, encoding='utf-8', method='xml'))
                _logger.info("Response Data Of Rate%s" % response_data.content)
                if response_data.status_code in [200, 201]:
                    api = Response(response_data)
                    response_data = api.dict()
                    common_response_data = response_data.get('Envelope').get('Body').get('CreateShipmentResponse')
                    check_errors = common_response_data.get('ResponseInformation').get('Errors')
                    if check_errors:
                        raise ValidationError(check_errors)
                    purolator_shipment_pin = common_response_data.get('ShipmentPIN').get('Value')
                    label_response_data = self.purolator_get_label_using_shipment_pin(picking, purolator_shipment_pin)
                    picking.carrier_tracking_ref = purolator_shipment_pin

                    pdf_label_url = label_response_data.get('Envelope') and label_response_data.get('Envelope').get(
                        'Body') and label_response_data.get('Envelope').get('Body').get(
                        'GetDocumentsResponse') and label_response_data.get('Envelope').get('Body').get(
                        'GetDocumentsResponse').get('Documents') and label_response_data.get('Envelope').get(
                        'Body').get('GetDocumentsResponse').get('Documents').get(
                        'Document') and label_response_data.get('Envelope').get('Body').get('GetDocumentsResponse').get(
                        'Documents').get('Document').get('DocumentDetails').get('DocumentDetail').get('URL')

                    headers = {'Content-Type': "application/x-www-form-urlencoded", 'Accept': "application/pdf"}
                    time.sleep(2)  # Sleep for 2 seconds
                    pdf_response = requests.request("GET", url=pdf_label_url, headers=headers)
                    logmessage = ("<b>Tracking Numbers:</b> %s") % (purolator_shipment_pin)
                    pickings.message_post(body=logmessage,
                                          attachments=[
                                              ("%s.pdf" % (purolator_shipment_pin), pdf_response.content)])
                    shipping_chrg = self.purolator_rate_shipment(picking.sale_id)
                    shipping_data = {'exact_price': shipping_chrg['price'], 'tracking_number': purolator_shipment_pin}
                    response += [shipping_data]
                    return response

                else:
                    raise ValidationError(response_data.text)
            except Exception as e:
                raise ValidationError(e)


    def combine_pdfs(self, pdfs):
        merger = PdfFileMerger()
        for pdf in pdfs:
            try:
                merger.append(io.BytesIO(pdf))
            except Exception as e:
                # Log the error and skip the invalid PDF
                _logger.warning(f"Error reading PDF: {e} - Skipping invalid PDF.")
        combined_pdf = io.BytesIO()
        merger.write(combined_pdf)
        combined_pdf.seek(0)
        return combined_pdf.getvalue()

    def purolator_cancel_shipment(self, picking):
        """This Method Used For Cancel The Shipment"""

        cancel_request = etree.Element("soapenv:Envelope")
        cancel_request.attrib['xmlns:soapenv'] = "http://schemas.xmlsoap.org/soap/envelope/"
        cancel_request.attrib['xmlns:v2'] = "http://purolator.com/pws/datatypes/v2"

        header_node = etree.SubElement(cancel_request, "soapenv:Header")

        request_context_node = etree.SubElement(header_node, "v2:RequestContext")
        etree.SubElement(request_context_node, "v2:Version").text = "2.2"
        etree.SubElement(request_context_node, "v2:Language").text = "en"
        etree.SubElement(request_context_node, "v2:GroupID").text = "123"
        etree.SubElement(request_context_node, "v2:RequestReference").text = "Cancel Request"

        body_node = etree.SubElement(cancel_request, "soapenv:Body")

        void_shipment_request_node = etree.SubElement(body_node, "v2:VoidShipmentRequest")
        pin_node = etree.SubElement(void_shipment_request_node, "v2:PIN")

        etree.SubElement(pin_node, 'v2:Value').text = picking.carrier_tracking_ref
        _logger.info("Cancel request data %s" % etree.tostring(cancel_request))
        try:
            headers = {
                'Content-Type': "text/xml;  charset=utf-8",
                'SOAPAction': "http://purolator.com/pws/service/v2/VoidShipment"
            }
            username = self.company_id.purolator_username
            password = self.company_id.purolator_password
            url = "{0}/v2/Shipping/ShippingService.asmx".format(
                self.company_id and self.company_id.purolator_api_url)
            _logger.info("Request Data Of Cancel::::%s" % etree.tostring(cancel_request))
            response_data = requests.request(method="POST", url=url, headers=headers,
                                             auth=HTTPBasicAuth(username=username, password=password),
                                             data=etree.tostring(cancel_request))
            _logger.info("Response Data Of Rate%s" % response_data.content)
            if response_data.status_code in [200, 201]:
                api = Response(response_data)
                response_data = api.dict()
                _logger.info(response_data)
                common_response = response_data.get('Envelope').get('Body').get('VoidShipmentResponse')
                if common_response.get('ShipmentVoided') == 'true':
                    return True
                else:
                    raise ValidationError(common_response.get('ResponseInformation').get('Errors'))
        except Exception as e:
            raise ValidationError(e)

    def purolator_get_tracking_link(self, pickings):
        """This Method is used for tracking parcel"""
        return "https://www.purolator.com/en/shipping/tracker?pins={}".format(pickings.carrier_tracking_ref)

    def purolator_get_label_using_shipment_pin(self, picking, purolator_shipment_pin):

        root_element = etree.Element("SOAP-ENV:Envelope")
        root_element.attrib["xmlns:SOAP-ENV"] = "http://schemas.xmlsoap.org/soap/envelope/"
        root_element.attrib["xmlns:ns1"] = "http://purolator.com/pws/datatypes/v1"
        root_header = etree.SubElement(root_element, "SOAP-ENV:Header")
        request_context = etree.SubElement(root_header, "ns1:RequestContext")
        etree.SubElement(request_context, "ns1:Version").text = "1.3"
        etree.SubElement(request_context, "ns1:Language").text = "en"
        etree.SubElement(request_context, "ns1:GroupID").text = "123"
        etree.SubElement(request_context, "ns1:RequestReference").text = "Get Label Request"

        root_body = etree.SubElement(root_element, "SOAP-ENV:Body")
        root_get_document_request = etree.SubElement(root_body, "ns1:GetDocumentsRequest")
        root_document_criterium = etree.SubElement(root_get_document_request, "ns1:DocumentCriterium")
        root_document_criteria = etree.SubElement(root_document_criterium, "ns1:DocumentCriteria")
        root_pin = etree.SubElement(root_document_criteria, "ns1:PIN")
        etree.SubElement(root_pin, "ns1:Value").text = purolator_shipment_pin
        _logger.info(etree.tostring(root_element))

        try:
            headers = {
                'Content-Type': "text/xml;  charset=utf-8",
                'SOAPAction': "http://purolator.com/pws/service/v1/GetDocuments"
            }
            username = self.company_id.purolator_username
            password = self.company_id.purolator_password
            url = "{0}/v1/ShippingDocuments/ShippingDocumentsService.asmx".format(
                self.company_id and self.company_id.purolator_api_url)
            _logger.info("Request Data Of Rate::::%s" % etree.tostring(root_element))
            response_data = requests.request(method="POST", url=url, headers=headers,
                                             auth=HTTPBasicAuth(username=username, password=password),
                                             data=etree.tostring(root_element, encoding='utf-8', method='xml'))
            _logger.info("Response Data Of Rate%s" % response_data.content)
            if response_data.status_code in [200, 201]:
                api = Response(response_data)
                response_data = api.dict()
                return response_data
        except Exception as e:
            raise Warning(e)

    def purolator_return_rate_shipment(self, orders, return_wiz, out_picking):
        "This Method Is Used For Get Rate"

        shipper_address = orders.warehouse_id and orders.warehouse_id.partner_id
        recipient_address = orders.partner_shipping_id

        if not shipper_address.zip or not shipper_address.city or not shipper_address.country_id:
            return {'success': False, 'price': 0.0,
                    'error_message': "Please Define Proper Sender Address!",
                    'warning_message': False}

        if not recipient_address.zip or not recipient_address.city or not recipient_address.country_id:
            return {'success': False, 'price': 0.0,
                    'error_message': "Please Define Proper Recipient Address!",
                    'warning_message': False}

        total_weight_in = sum(
                [(line.product_id.weight * line.quantity) for line in return_wiz.product_return_moves])
        _logger.info("Total weight: %s " % total_weight_in)
        # Calculate the total weight and dimensions for each package
        packages_ids = self.env.context.get('packages', [])
        _logger.info("Request Data packages::::%s" % packages_ids)
        packages = []
        if not len(packages_ids):
            # packages = []
            weight = sum(
                [(line.product_id.weight * line.quantity) for line in return_wiz.product_return_moves])
            weight_limit = 68
            pieces = []
            while weight > weight_limit:
                pieces.append(weight_limit)
                weight -= weight_limit
            if weight > 0:
                pieces.append(weight)
            for line in pieces:
                weight = str(line)
                length = "1"
                width = "1"
                height = "1"
                packages.append({
                    'weight': weight,
                    'length': length,
                    'width': width,
                    'height': height,
                })
        else:
            # packages = []
            for line in packages_ids:
                weight = str(line.shipping_weight)
                length = "1"
                width = "1"
                height = "1"
                packages.append({
                    'weight': weight,
                    'length': length,
                    'width': width,
                    'height': height,
                })

        _logger.info("Weight Division package: %s " % packages)
        # Create the root element with namespaces
        root = ET.Element("SOAP-ENV:Envelope", {
            "xmlns:SOAP-ENV": "http://schemas.xmlsoap.org/soap/envelope/",
            "xmlns:v2": "http://purolator.com/pws/datatypes/v2"
        })

        # Create the Header
        header = ET.SubElement(root, "SOAP-ENV:Header")
        request_context = ET.SubElement(header, "v2:RequestContext")
        ET.SubElement(request_context, "v2:Version").text = "2.0"
        ET.SubElement(request_context, "v2:Language").text = "en"
        ET.SubElement(request_context, "v2:GroupID").text = "xxx"
        ET.SubElement(request_context, "v2:RequestReference").text = "Rating Example"

        # Create the Body
        body = ET.SubElement(root, "SOAP-ENV:Body")
        get_full_estimate_request = ET.SubElement(body, "v2:GetFullEstimateRequest")

        # Add Shipment
        shipment = ET.SubElement(get_full_estimate_request, "v2:Shipment")

        # Add SenderInformation
        StreetNameShipper = ' '.join(filter(None, [shipper_address.street, shipper_address.street2]))
        sender_info = ET.SubElement(shipment, "v2:SenderInformation")
        sender_address = ET.SubElement(sender_info, "v2:Address")
        ET.SubElement(sender_address, "v2:Name").text = shipper_address.name or ''
        ET.SubElement(sender_address, "v2:StreetNumber").text = ""
        ET.SubElement(sender_address, "v2:StreetName").text = StreetNameShipper
        ET.SubElement(sender_address, "v2:City").text = shipper_address.city or ''
        ET.SubElement(sender_address, "v2:Province").text = shipper_address.state_id and shipper_address.state_id.code or ''
        ET.SubElement(sender_address, "v2:Country").text = shipper_address.country_id and shipper_address.country_id.code or ''
        ET.SubElement(sender_address, "v2:PostalCode").text = shipper_address.zip or ''
        shipper_area_code, shipper_phone = self.get_area_code_and_phone(shipper_address.phone)
        phone_number = ET.SubElement(sender_address, "v2:PhoneNumber")
        ET.SubElement(phone_number, "v2:CountryCode").text = "1"
        ET.SubElement(phone_number, "v2:AreaCode").text = shipper_area_code
        ET.SubElement(phone_number, "v2:Phone").text = shipper_phone

        # Add ReceiverInformation
        StreetNameRecipient = ' '.join(filter(None, [recipient_address.street, recipient_address.street2]))
        receiver_info = ET.SubElement(shipment, "v2:ReceiverInformation")
        receiver_address = ET.SubElement(receiver_info, "v2:Address")
        ET.SubElement(receiver_address, "v2:Name").text = recipient_address.name or ''
        ET.SubElement(receiver_address, "v2:StreetNumber").text = ""
        ET.SubElement(receiver_address, "v2:StreetName").text = StreetNameRecipient
        ET.SubElement(receiver_address, "v2:City").text = recipient_address.city or ''
        ET.SubElement(receiver_address, "v2:Province").text = recipient_address.state_id and recipient_address.state_id.code or ''
        ET.SubElement(receiver_address, "v2:Country").text = recipient_address.country_id and recipient_address.country_id.code or ''
        ET.SubElement(receiver_address, "v2:PostalCode").text = recipient_address.zip or ''
        recipient_area_code, recipient_phone = self.get_area_code_and_phone(recipient_address.phone)
        phone_number = ET.SubElement(receiver_address, "v2:PhoneNumber")
        ET.SubElement(phone_number, "v2:CountryCode").text = "1"
        ET.SubElement(phone_number, "v2:AreaCode").text = recipient_area_code
        ET.SubElement(phone_number, "v2:Phone").text = recipient_phone

        # Add PackageInformation
        package_info = ET.SubElement(shipment, "v2:PackageInformation")
        ET.SubElement(package_info, "v2:ServiceID").text = "PurolatorExpress"
        total_weight = ET.SubElement(package_info, "v2:TotalWeight")
        ET.SubElement(total_weight, "v2:Value").text = str(total_weight_in)
        ET.SubElement(total_weight, "v2:WeightUnit").text = self.weight_unit or ''
        ET.SubElement(package_info, "v2:TotalPieces").text = str(len(packages))

        for piece in packages:
            piece_info = ET.SubElement(package_info, "v2:PiecesInformation")
            _logger.info("Request Data piece_info::::%s" % piece_info)
            ET.SubElement(piece_info, "v2:Length").text = piece["length"]
            ET.SubElement(piece_info, "v2:Width").text = piece["width"]
            ET.SubElement(piece_info, "v2:Height").text = piece["height"]
            ET.SubElement(piece_info, "v2:Weight").text = piece["weight"]
            ET.SubElement(piece_info, "v2:WeightUnit").text = self.weight_unit or ''

        

        # Add OptionsInformation
        # options_info = ET.SubElement(package_info, "ns1:OptionsInformation")
        # options = ET.SubElement(options_info, "ns1:Options")
        # option_id_value_pair = ET.SubElement(options, "ns1:OptionIDValuePair")
        # ET.SubElement(option_id_value_pair, "ns1:ID").text = "DangerousGoods"
        # ET.SubElement(option_id_value_pair, "ns1:Value").text = "true"
        # option_id_value_pair = ET.SubElement(options, "ns1:OptionIDValuePair")
        # ET.SubElement(option_id_value_pair, "ns1:ID").text = "DangerousGoodsMode"
        # ET.SubElement(option_id_value_pair, "ns1:Value").text = "Air"
        # option_id_value_pair = ET.SubElement(options, "ns1:OptionIDValuePair")
        # ET.SubElement(option_id_value_pair, "ns1:ID").text = "DangerousGoodsClass"
        # ET.SubElement(option_id_value_pair, "ns1:Value").text = "FullyRegulated"

        # Add PaymentInformation
        payment_info = ET.SubElement(shipment, "v2:PaymentInformation")
        ET.SubElement(payment_info, "v2:PaymentType").text = "Sender"
        ET.SubElement(payment_info, "v2:RegisteredAccountNumber").text = self.company_id.purolator_account_number
        ET.SubElement(payment_info, "v2:BillingAccountNumber").text = self.company_id and self.company_id.purolator_account_number

        # Add PickupInformation
        pickup_info = ET.SubElement(shipment, "v2:PickupInformation")
        ET.SubElement(pickup_info, "v2:PickupType").text = "DropOff"

        # Add ShowAlternativeServicesIndicator
        ET.SubElement(get_full_estimate_request, "v2:ShowAlternativeServicesIndicator").text = "true"

        # Generate the XML string
        # base_data = etree.tostring(root)
        xml_str = ET.tostring(root, encoding='utf-8', method='xml')



        # root_element = etree.Element("soapenv:Envelope")
        # root_element.attrib['xmlns:soapenv'] = "http://schemas.xmlsoap.org/soap/envelope/"
        # root_element.attrib['xmlns:v2'] = "http://purolator.com/pws/datatypes/v2"

        # root_header = etree.SubElement(root_element, "soapenv:Header")
        # request_context = etree.SubElement(root_header, "v2:RequestContext")
        # etree.SubElement(request_context, "v2:Version").text = "2.2"
        # etree.SubElement(request_context, "v2:Language").text = "en"
        # etree.SubElement(request_context, "v2:GroupID").text = str((uuid.uuid4().int))[:4]
        # etree.SubElement(request_context, "v2:RequestReference").text = "rate"

        # root_body = etree.SubElement(root_element, "soapenv:Body")
        # root_getquickestimateRequest = etree.SubElement(root_body, "v2:GetQuickEstimateRequest")
        # etree.SubElement(root_getquickestimateRequest,
        #                  "v2:BillingAccountNumber").text = self.company_id and self.company_id.purolator_account_number
        # etree.SubElement(root_getquickestimateRequest, "v2:SenderPostalCode").text = sender_address.zip or ''
        # root_receiveraddress = etree.SubElement(root_getquickestimateRequest, "v2:ReceiverAddress")
        # etree.SubElement(root_receiveraddress, "v2:City").text = receiver_address.city or ''
        # etree.SubElement(root_receiveraddress,
        #                  "v2:Province").text = receiver_address.state_id and receiver_address.state_id.code or ''
        # etree.SubElement(root_receiveraddress,
        #                  "v2:Country").text = receiver_address.country_id and receiver_address.country_id.code or ''
        # etree.SubElement(root_receiveraddress, "v2:PostalCode").text = receiver_address.zip or ''

        # etree.SubElement(root_getquickestimateRequest, "v2:PackageType").text = self.purolator_package_type

        # # Add each package to the request
        # for package in packages:
        #     package_element = etree.SubElement(root_getquickestimateRequest, "v2:Package")
        #     weight_element = etree.SubElement(package_element, "v2:Weight")
        #     etree.SubElement(weight_element, "v2:Value").text = str(package['weight'])
        #     etree.SubElement(weight_element, "v2:WeightUnit").text = self.weight_unit
        #     etree.SubElement(package_element, "v2:Length").text = str(package['length'])
        #     etree.SubElement(package_element, "v2:Width").text = str(package['width'])
        #     etree.SubElement(package_element, "v2:Height").text = str(package['height'])
        #     # etree.SubElement(package_element, "v2:DimensionUnit").text = "in"  # or the appropriate unit

        # root_totalweight = etree.SubElement(root_getquickestimateRequest, "v2:TotalWeight")
        # weight = sum(
        # [(line.product_id.weight * line.product_uom_qty) for line in orders.order_line if not line.is_delivery])
        # etree.SubElement(root_totalweight, "v2:Value").text = str(weight)
        # etree.SubElement(root_totalweight, "v2:WeightUnit").text = self.weight_unit

        # base_data = etree.tostring(root_element)

        try:
            headers = {
                "Content-Type": "text/xml; charset=utf-8",
                "SOAPAction": "http://purolator.com/pws/service/v2/GetFullEstimate"
            }
            username = self.company_id.purolator_username
            password = self.company_id.purolator_password
            url = "{0}/v2/Estimating/EstimatingService.asmx".format(
                self.company_id and self.company_id.purolator_api_url)
            _logger.info("Request Data Of Rate::::%s" % xml_str)
            response_data = requests.request(method="POST", url=url, headers=headers,
                                             auth=HTTPBasicAuth(username=username, password=password),
                                             data=xml_str)
            _logger.info("Response Data Of Rate%s" % response_data.content)
            _logger.info("Response Data Of Rate code%s" % response_data.status_code)
            if response_data.status_code in [200, 201]:
                api = Response(response_data)
                response_data = api.dict()
                common_response = response_data.get('Envelope').get('Body').get('GetFullEstimateResponse')
                check_errors = common_response.get('ResponseInformation').get('Errors')
                if check_errors:
                    raise ValidationError(check_errors)

                purolator_shipping_charge_obj = self.env['purolator.shipping.charge']

                existing_records = purolator_shipping_charge_obj.search([('sale_order_id', '=', orders and orders.id)])
                existing_records.sudo().unlink()
                if common_response.get('ShipmentEstimates').get('ShipmentEstimate'):
                    rate_response_dicts = common_response.get('ShipmentEstimates').get('ShipmentEstimate')
                else:
                    raise ValidationError("Response Data : %s" % (response_data))
                if isinstance(rate_response_dicts, dict):
                    rate_response_dicts = [rate_response_dicts]
                for response_dict in rate_response_dicts:
                    purolator_service_id = response_dict.get('ServiceID')
                    expected_delivery_date = response_dict.get('ExpectedDeliveryDate')
                    estimated_transit_days = response_dict.get('EstimatedTransitDays')
                    purolator_total_charge = response_dict.get('TotalPrice')
                    purolator_shipping_charge_obj.sudo().create(
                        {
                            'purolator_service_id': purolator_service_id,
                            'expected_delivery_date': expected_delivery_date,
                            'estimated_transit_days': estimated_transit_days,
                            'purolator_total_charge': purolator_total_charge,
                            'sale_order_id': orders and orders.id
                        }
                    )
                purolator_charge_id = purolator_shipping_charge_obj.search(
                    [('sale_order_id', '=', orders and orders.id)], order='purolator_total_charge', limit=1)
                orders.purolator_shipping_charge_id = purolator_charge_id and purolator_charge_id.id
                return {'success': True,
                        'price': purolator_charge_id and purolator_charge_id.purolator_total_charge or 0.0,
                        'error_message': False, 'warning_message': False, 'base_data': xml_str}
            else:
                return {'success': False, 'price': 0.0,
                        'error_message': "%s %s" % (response_data, response_data.text),
                        'warning_message': False, 'base_data': xml_str}
        except Exception as e:
            _logger.error("An error occurred: %s", str(e))
            msg = str(e)
            active_id = self.env.context.get('active_id')
            picking = self.env['stock.picking'].browse(active_id)
            self.env.cr.commit()
            if picking:
                self.env.cr.commit()
                picking.message_post(body=msg)
                self.env.cr.commit()
            raise ValidationError(e)


    def purolator_create_return_shipment(self, pickings, new_picking, return_wiz):
        """This Method Is Used For Sending The Return Shipping Request To Shipper"""

        total_weights = sum(
                [(line.product_id.weight * line.quantity) for line in return_wiz.product_return_moves])
        _logger.info("Total weight: %s " % total_weights)
        packages = []
        weight = sum(
            [(line.product_id.weight * line.quantity) for line in return_wiz.product_return_moves])
        package_count = return_wiz.package_qty

        _logger.info("Package count: %s" % package_count)
        if package_count < 0:
            raise ValidationError("Please define a valid Package Count! It should be a positive integer.")
        pieces = []
        weight_limit = 150
        if package_count > 0:
            per_package_weight = round((weight / package_count), 2)
            for _ in range(package_count):
                pieces.append(per_package_weight)
        else:
            while weight > weight_limit:
                pieces.append(weight_limit)
                weight -= weight_limit
            if weight > 0:
                pieces.append(round(weight, 2))

        _logger.info("Packages: %s" % pieces)
        for line in pieces:
            weight = str(line)
            length = "1"
            width = "1"
            height = "1"
            packages.append({
                'weight': weight,
                'length': length,
                'width': width,
                'height': height,
            })
        response = []
        _logger.info("Purolator Weight Division package: %s" % packages)
        for picking in new_picking:
            sender_address = picking.partner_id
            receiver_address = picking.picking_type_id.warehouse_id.partner_id
            if not sender_address.zip or not sender_address.city or not sender_address.country_id:
                raise ValidationError("Please define  proper sender addres")

            # check Receiver Address
            if not receiver_address.zip or not receiver_address.city or not receiver_address.country_id:
                raise ValidationError("Please define  proper receiver address")

            envelope = ET.Element('soap:Envelope', {
                'xmlns:soap': 'http://schemas.xmlsoap.org/soap/envelope/',
                'xmlns:v2': 'http://purolator.com/pws/datatypes/v2'
            })

            # Create the Header
            header = ET.SubElement(envelope, 'soap:Header')
            request_context = ET.SubElement(header, 'v2:RequestContext')
            ET.SubElement(request_context, 'v2:Version').text = '2.0'
            ET.SubElement(request_context, 'v2:Language').text = 'en'
            ET.SubElement(request_context, 'v2:GroupID').text = 'xxx'
            ET.SubElement(request_context, 'v2:RequestReference').text = 'Return Request'

            # Create the Body
            body = ET.SubElement(envelope, 'soap:Body')
            create_request = ET.SubElement(body, 'v2:CreateReturnsManagementShipmentRequest')
            # ET.SubElement(create_request, 'v2:RMA').text = 'RMA123'

            # Returns Management Shipment
            returns_management_shipment = ET.SubElement(create_request, 'v2:ReturnsManagementShipment')

            StreetNameSender = ' '.join(filter(None, [sender_address.street, sender_address.street2]))

            # Sender Information
            sender_info = ET.SubElement(returns_management_shipment, 'v2:SenderInformation')
            address_sender = ET.SubElement(sender_info, 'v2:Address')
            ET.SubElement(address_sender, 'v2:Name').text = sender_address.name or ''
            # ET.SubElement(address_sender, 'v2:Company').text = 'Purolator Courier Ltd'
            # ET.SubElement(address_sender, "v2:Department").text = "Web Services"
            ET.SubElement(address_sender, 'v2:StreetNumber').text = ''
            ET.SubElement(address_sender, 'v2:StreetName').text = StreetNameSender
            # ET.SubElement(address_sender, 'v2:StreetType').text = 'Street'
            ET.SubElement(address_sender, 'v2:City').text = sender_address.city or ''
            ET.SubElement(address_sender, 'v2:Province').text = sender_address.state_id and sender_address.state_id.code
            ET.SubElement(address_sender, 'v2:Country').text = sender_address.country_id and sender_address.country_id.code
            ET.SubElement(address_sender, 'v2:PostalCode').text = sender_address.zip or ''
            phone_sender = ET.SubElement(address_sender, 'v2:PhoneNumber')
            sender_area_code, sender_phone = self.get_area_code_and_phone(sender_address.phone)
            ET.SubElement(phone_sender, 'v2:CountryCode').text = '1'
            ET.SubElement(phone_sender, 'v2:AreaCode').text = sender_area_code
            ET.SubElement(phone_sender, 'v2:Phone').text = sender_phone

            # Receiver Information
            receiver_info = ET.SubElement(returns_management_shipment, 'v2:ReceiverInformation')
            StreetNameReceiver = ' '.join(filter(None, [receiver_address.street, receiver_address.street2]))

            address_receiver = ET.SubElement(receiver_info, 'v2:Address')
            ET.SubElement(address_receiver, 'v2:Name').text = receiver_address.name or ''
            # ET.SubElement(address_receiver, 'v2:Company').text = 'Purolator Courier Ltd'
            # ET.SubElement(address_receiver, "v2:Department").text = "Web Services"
            ET.SubElement(address_receiver, 'v2:StreetNumber').text = ''
            ET.SubElement(address_receiver, 'v2:StreetName').text = StreetNameReceiver
            # ET.SubElement(address_receiver, 'v2:StreetType').text = 'Street'
            ET.SubElement(address_receiver, 'v2:City').text = receiver_address.city or ''
            ET.SubElement(address_receiver, 'v2:Province').text = receiver_address.state_id and receiver_address.state_id.code or ''
            ET.SubElement(address_receiver, 'v2:Country').text = receiver_address.country_id and receiver_address.country_id.code or ''
            ET.SubElement(address_receiver, 'v2:PostalCode').text = receiver_address.zip or ''
            phone_receiver = ET.SubElement(address_receiver, 'v2:PhoneNumber')
            receiver_area_code, receiver_phone = self.get_area_code_and_phone(receiver_address.phone)
            ET.SubElement(phone_receiver, 'v2:CountryCode').text = '1'
            ET.SubElement(phone_receiver, 'v2:AreaCode').text = receiver_area_code
            ET.SubElement(phone_receiver, 'v2:Phone').text = receiver_phone

            # Package Information
            package_info = ET.SubElement(returns_management_shipment, 'v2:PackageInformation')
            # ET.SubElement(package_info, 'v2:ServiceID').text = ""
            ET.SubElement(package_info, 'v2:ServiceID').text = return_wiz.carrier_id.purolator_service
            # ET.SubElement(package_info, 'v2:ServiceID').text = pickings.carrier_id.purolator_service
            total_weight = ET.SubElement(package_info, 'v2:TotalWeight')
            ET.SubElement(total_weight, 'v2:Value').text = str(total_weights) or ''
            # ET.SubElement(total_weight, 'v2:Value').text = str(picking.shipping_weight) or ''
            ET.SubElement(total_weight, 'v2:WeightUnit').text = self.weight_unit or ''
            ET.SubElement(package_info, 'v2:TotalPieces').text = str(len(packages))
            pieces_info = ET.SubElement(package_info, 'v2:PiecesInformation')

            for package in packages:
                piece = ET.SubElement(pieces_info, 'v2:Piece')
                weight = ET.SubElement(piece, 'v2:Weight')
                ET.SubElement(weight, 'v2:Value').text = package["weight"]
                ET.SubElement(weight, 'v2:WeightUnit').text = self.weight_unit or ''
                length = ET.SubElement(piece, 'v2:Length')
                ET.SubElement(length, 'v2:Value').text = package["length"]
                ET.SubElement(length, 'v2:DimensionUnit').text = 'in'
                width = ET.SubElement(piece, 'v2:Width')
                ET.SubElement(width, 'v2:Value').text = package["width"]
                ET.SubElement(width, 'v2:DimensionUnit').text = 'in'
                height = ET.SubElement(piece, 'v2:Height')
                ET.SubElement(height, 'v2:Value').text = package["height"]
                ET.SubElement(height, 'v2:DimensionUnit').text = 'in'

            # Payment Information
            payment_info = ET.SubElement(returns_management_shipment, 'v2:PaymentInformation')
            ET.SubElement(payment_info, 'v2:PaymentType').text = 'Sender'
            ET.SubElement(payment_info, 'v2:RegisteredAccountNumber').text = self.company_id.purolator_account_number

            # Pickup Information
            pickup_info = ET.SubElement(returns_management_shipment, 'v2:PickupInformation')
            ET.SubElement(pickup_info, 'v2:PickupType').text = 'DropOff'

            if pickings.carrier_id.delivery_type == 'purolator':
                tracking_info = ET.SubElement(returns_management_shipment, 'v2:TrackingReferenceInformation')
                ET.SubElement(tracking_info, 'v2:Reference1').text = str(pickings.origin)


            # Printer Type
            ET.SubElement(create_request, 'v2:PrinterType').text = 'Thermal'
            request_data = etree.tostring(envelope, encoding='utf-8', method='xml')

    #         request_data = f"""
    # <soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/"
    #                xmlns:v2="http://purolator.com/pws/datatypes/v2">
    #     <soap:Header>
    #         <v2:RequestContext>
    #             <v2:Version>2.0</v2:Version>
    #             <v2:Language>en</v2:Language>
    #             <v2:GroupID>xxx</v2:GroupID>
    #             <v2:RequestReference>Example Code</v2:RequestReference>
    #         </v2:RequestContext>
    #     </soap:Header>
    #     <soap:Body>
    #         <v2:CreateReturnsManagementShipmentRequest>
    #             <v2:RMA>RMA123</v2:RMA>
    #             <v2:ReturnsManagementShipment>
    #                 <v2:SenderInformation>
    #                     <v2:Address>
    #                         <v2:Name>Sender Name</v2:Name>
    #                         <v2:Company>Purolator Courier Ltd</v2:Company>
    #                         <v2:StreetNumber>2245</v2:StreetNumber>
    #                         <v2:StreetName>Main</v2:StreetName>
    #                         <v2:StreetType>Street</v2:StreetType>
    #                         <v2:City>Mississauga</v2:City>
    #                         <v2:Province>ON</v2:Province>
    #                         <v2:Country>CA</v2:Country>
    #                         <v2:PostalCode>L4W5M8</v2:PostalCode>
    #                         <v2:PhoneNumber>
    #                             <v2:CountryCode>1</v2:CountryCode>
    #                             <v2:AreaCode>905</v2:AreaCode>
    #                             <v2:Phone>5555555</v2:Phone>
    #                         </v2:PhoneNumber>
    #                     </v2:Address>
    #                 </v2:SenderInformation>
    #                 <v2:ReceiverInformation>
    #                     <v2:Address>
    #                         <v2:Name>Receiver Name</v2:Name>
    #                         <v2:Company>Purolator Courier Ltd</v2:Company>
    #                         <v2:StreetNumber>2245</v2:StreetNumber>
    #                         <v2:StreetName>Main</v2:StreetName>
    #                         <v2:StreetType>Street</v2:StreetType>
    #                         <v2:City>Mississauga</v2:City>
    #                         <v2:Province>ON</v2:Province>
    #                         <v2:Country>CA</v2:Country>
    #                         <v2:PostalCode>L4W5M8</v2:PostalCode>
    #                         <v2:PhoneNumber>
    #                             <v2:CountryCode>1</v2:CountryCode>
    #                             <v2:AreaCode>905</v2:AreaCode>
    #                             <v2:Phone>5555555</v2:Phone>
    #                         </v2:PhoneNumber>
    #                     </v2:Address>
    #                 </v2:ReceiverInformation>
    #                 <v2:PackageInformation>
    #                     <v2:ServiceID>PurolatorExpress</v2:ServiceID>
    #                     <v2:TotalWeight>
    #                         <v2:Value>40</v2:Value>
    #                         <v2:WeightUnit>lb</v2:WeightUnit>
    #                     </v2:TotalWeight>
    #                     <v2:TotalPieces>1</v2:TotalPieces>
    #                     <v2:PiecesInformation>
    #                         <v2:Piece>
    #                             <v2:Weight>
    #                                 <v2:Value>40</v2:Value>
    #                                 <v2:WeightUnit>lb</v2:WeightUnit>
    #                             </v2:Weight>
    #                             <v2:Length>
    #                                 <v2:Value>40</v2:Value>
    #                                 <v2:DimensionUnit>in</v2:DimensionUnit>
    #                             </v2:Length>
    #                             <v2:Width>
    #                                 <v2:Value>10</v2:Value>
    #                                 <v2:DimensionUnit>in</v2:DimensionUnit>
    #                             </v2:Width>
    #                             <v2:Height>
    #                                 <v2:Value>2</v2:Value>
    #                                 <v2:DimensionUnit>in</v2:DimensionUnit>
    #                             </v2:Height>
    #                         </v2:Piece>
    #                     </v2:PiecesInformation>
    #                 </v2:PackageInformation>
    #                 <v2:PaymentInformation>
    #                     <v2:PaymentType>Sender</v2:PaymentType>
    #                     <v2:RegisteredAccountNumber>9999999999</v2:RegisteredAccountNumber>
    #                 </v2:PaymentInformation>
    #                 <v2:PickupInformation>
    #                     <v2:PickupType>DropOff</v2:PickupType>
    #                 </v2:PickupInformation>
                    
    #             </v2:ReturnsManagementShipment>
                
    #             <v2:PrinterType>Thermal</v2:PrinterType>
    #         </v2:CreateReturnsManagementShipmentRequest>
    #     </soap:Body>
    # </soap:Envelope>
    # """

            try:
                # Set headers and endpoint URL
                headers = {
                    'Content-Type': "text/xml; charset=utf-8",
                    'SOAPAction': "http://purolator.com/pws/service/v2/CreateReturnShipment"
                }
                username = picking.company_id.purolator_username
                password = picking.company_id.purolator_password
                url = "{0}/v2/ReturnsManagement/ReturnsManagementService.asmx".format(
                        picking.company_id and picking.company_id.purolator_api_url)

                _logger.info("Request Data of Return: %s", request_data)
                response_data = requests.post(url=url, headers=headers,
                                              auth=HTTPBasicAuth(username=username, password=password),
                                              data=request_data)
                _logger.info("Response Data of Return: %s", response_data.content)
                _logger.info("Response Data of Return: %s", response_data.status_code)
                if response_data.status_code in [200, 201]:
                    api_response = Response(response_data)
                    response_data_dict = api_response.dict()
                    common_response_data = response_data_dict.get('Envelope', {}).get('Body', {}).get('CreateReturnsManagementShipmentResponse')
                    errors = common_response_data.get('ResponseInformation', {}).get('Errors')

                    if errors:
                        raise ValidationError(errors)

                    carrier_price = self.purolator_return_rate_shipment(picking.sale_id, return_wiz, picking)
                    purolator_return_pin = common_response_data.get('ShipmentPIN', {}).get('Value')
                    new_picking.carrier_tracking_ref = purolator_return_pin
                    new_picking.carrier_price = carrier_price['price']
                    new_picking.get_min_cost = carrier_price['price']
                    new_picking.carrier_id = return_wiz.carrier_id
                    label_response_data = self.purolator_get_label_using_shipment_pin(picking, purolator_return_pin)
                    pdf_label_url = label_response_data.get('Envelope') and label_response_data.get('Envelope').get(
                        'Body') and label_response_data.get('Envelope').get('Body').get(
                        'GetDocumentsResponse') and label_response_data.get('Envelope').get('Body').get(
                        'GetDocumentsResponse').get('Documents') and label_response_data.get('Envelope').get(
                        'Body').get('GetDocumentsResponse').get('Documents').get(
                        'Document') and label_response_data.get('Envelope').get('Body').get('GetDocumentsResponse').get(
                        'Documents').get('Document').get('DocumentDetails').get('DocumentDetail').get('URL')

                    headers = {'Content-Type': "application/x-www-form-urlencoded", 'Accept': "application/pdf"}
                    time.sleep(2)  # Sleep for 2 seconds
                    pdf_response = requests.request("GET", url=pdf_label_url, headers=headers)
                    logmessage = ("%s Return Shipment Label !<br/> <b>Return Shipment Tracking Number : </b>%s") % (
                                return_wiz.carrier_id.name, purolator_return_pin)
                    new_picking.message_post(body=logmessage,
                                          attachments=[
                                              ("%s.pdf" % (purolator_return_pin), pdf_response.content)])
                    shipping_chrg = self.purolator_return_rate_shipment(picking.sale_id, return_wiz, picking)
                    # shipping_chrg = self.purolator_rate_shipment(picking.sale_id)
                    shipping_data = {'exact_price': shipping_chrg['price'], 'tracking_number': purolator_return_pin}
                    response += [shipping_data]
                    return response

                else:
                    raise ValidationError(response_data.text)
            except Exception as e:
                raise ValidationError(e)

