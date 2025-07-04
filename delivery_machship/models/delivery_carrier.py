# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, _
from odoo.exceptions import UserError

import requests
import json

MACSHIP_URL = "https://live.machship.com"

class DeliveryCarrier(models.Model):
    _inherit = 'delivery.carrier'

    delivery_type = fields.Selection(selection_add=[('machship', 'MachShip')], ondelete={'machship': 'set default'})
    chep_fast = fields.Selection([('0', 'Cheapest'), ('1', 'Fastest')], 'Best Method')
    machship_token = fields.Char('Token')
    mach_carrier_id = fields.Integer('Carrier ID')
    mach_acc_carrier_id = fields.Integer('Carrier Account ID')
    comp_carrier_account_id = fields.Integer('Company Carrier Account ID')
    
    def machship_check_conn(self):
        self.ensure_one()
        if not self.machship_token:
            raise UserError(_("Please set a token to proceed"))
        ping_url = MACSHIP_URL + "/apiv2/authenticate/ping"
        headers = {'Content-type': 'application/json', 'Accept': 'application/json', 'token': self.machship_token}
        data = {}
        try:
            r = requests.post(ping_url, data=json.dumps(data), headers=headers)
        except:
            raise UserError(_("Unable to connect MachShip"))
        status_code = r.status_code
        if status_code == 200:
            title = _("Connection Successful")
            message = _("Token Verified !")
            return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': title,
                        'message': message,
                        'sticky': True,
                    }
                }
        else:
            raise UserError(_("Invalid Token"))
        
    def create_cons(self, picking):
        # Shipment creation based on packages
        packs = []
        pack_dict = {}
        for line in picking.move_line_ids_without_package:
            if line.result_package_id and line.qty_done != 0.00:
                package = line.result_package_id
                if not package.package_type_id:
                    raise UserError(_("Please specify package type in package"))
                if not package.package_type_id.shipper_package_code:
                    raise UserError(_("Please specify shipper code of package type"))
                if not pack_dict.get(package, False):
                    pack_dict[package] = 0.00
                pack_dict[package] += line.qty_done
        for line in pack_dict:
            vals = {
                'name': line.name,
                'companyItemId': line.package_type_id.shipper_package_code,
                'quantity': 1,#int(pack_dict[line]),
                'height': round(line.package_type_id.height / 10.00, 2),
                'width': round(line.package_type_id.width / 10.00, 2),
                'length': round(line.package_type_id.packaging_length / 10.00, 2),
                'weight': line.shipping_weight
                }
            packs.append(vals)
        if not picking.picking_type_id.warehouse_id or not picking.picking_type_id.warehouse_id.partner_id.zip:
            raise UserError(_("Invalid Warehouse address."))
        
        
        if not picking.picking_type_id.warehouse_id.macship_location_id or \
                    picking.picking_type_id.warehouse_id.macship_location_id == 0:
            raise UserError(_("Please provide a MachShip Location ID in warehouse"))
        parent_cont = picking.partner_id.get_partner_parent()
        ship_vals = {
            'customerReference': picking.sale_id and picking.sale_id.name,
            'customerReference2': picking.name,
            'items': packs,
            'fromCompanyLocationId': picking.picking_type_id.warehouse_id.macship_location_id,
            'fromLocation': {
                'suburb': picking.picking_type_id.warehouse_id.partner_id.city,
                'postcode': picking.picking_type_id.warehouse_id.partner_id.zip
                },
            'toName': parent_cont and parent_cont.name or picking.partner_id.name,
            'toContact': picking.partner_id.name,
            'toPhone': picking.partner_id.phone or '',
            'toEmail': picking.partner_id.email or '',
            'toAddressLine1': picking.partner_id.street or '',
            'toAddressLine2': picking.partner_id.street2 or '',
            'toLocation': {
                'suburb': picking.partner_id.city,
                'postcode': picking.partner_id.zip or ''
                }
            }
        if self.chep_fast:
            ship_vals['defaultRouteSelection'] = int(self.chep_fast)
        else:
            if not self.mach_carrier_id or self.mach_carrier_id == 0:
                raise UserError(_("Please set carrier ID before proceeding"))
            if not self.comp_carrier_account_id or self.comp_carrier_account_id == 0:
                raise UserError(_("Please set company carrier account id"))
            if not self.mach_acc_carrier_id or self.mach_acc_carrier_id == 0:
                raise UserError(_("Please set carrier account id"))
            ship_vals['carrierId'] = self.mach_carrier_id
            ship_vals['carrierAccountId'] = self.mach_acc_carrier_id
            ship_vals['companyCarrierAccountId'] = self.comp_carrier_account_id
        if picking.partner_id and picking.partner_id.x_studio_default_delivery_instructions:
            ship_vals['specialInstructions'] = picking.partner_id.x_studio_default_delivery_instructions
        cons_url = MACSHIP_URL + "/apiv2/consignments/createConsignment"
        headers = {'Content-type': 'application/json', 'Accept': 'application/json', 'token': self.machship_token}
        try:
            r = requests.post(cons_url, data=json.dumps(ship_vals), headers=headers)
        except:
            raise UserError(_("Unable to connect MachShip"))
        status_code = r.status_code
        req_response = r.json()
        if status_code == 200:
            if not req_response['object']:
                errors = req_response['errors']
                error_str = ''
                for err in errors:
                    error_str += "%s \n"%(err['errorMessage'])
                return self.create_pending_cons(ship_vals, headers, picking, error_str)
            else:
                carrier_cons_id = req_response['object']['carrierConsignmentId']
                cons_id = req_response['object']['id']
                cons_number = req_response['object']['consignmentNumber']
                picking.carrier_tracking_ref = carrier_cons_id
                picking.machship_cons_id = cons_id
                picking.machship_cons_number = cons_number
                if req_response['object'].get('trackingPageAccessToken', False):
                    tracking_token = req_response['object']['trackingPageAccessToken']
                    tracking_url = "https://live.machship.com/tracking/#/consignments/%s"%(tracking_token)
                    picking.tracking_url = tracking_url
                if req_response['object'].get('carrier', False) and req_response['object']['carrier'].get('id', False) and \
                        picking.carrier_id.chep_fast in ['0', '1']:
                    carrier_id = req_response['object']['carrier']['id']
                    del_ids = self.env['delivery.carrier'].search([('mach_carrier_id', '=', carrier_id)])
                    if del_ids:
                        picking.carrier_id = del_ids[0].id
        else:
            raise UserError(_("Unable to connect to Machship"))
    
    def create_pending_cons(self, ship_vals, headers, picking, parent_error):
        notification = {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': None,
                'type': 'success',
                'sticky': True,
            },
        }
        cons_url = MACSHIP_URL + "/apiv2/pendingConsignments/createPendingConsignment"
        try:
            r = requests.post(cons_url, data=json.dumps(ship_vals), headers=headers)
        except:
            raise UserError(_("Unable to connect MachShip"))
        status_code = r.status_code
        req_response = r.json()
        if status_code == 200:
            if not req_response['object']:
                
                errors = req_response['errors']
                error_str = ''
                for err in errors:
                    error_str += "%s \n"%(err['errorMessage'])
                raise UserError(_("Following Error occured during pending consignment creation:\n%s"%(error_str)))
            cons_number = req_response['object']['consignmentNumber']
            cons_id = req_response['object']['id']
            picking.machship_cons_number = cons_number
            picking.machship_cons_id = cons_id
            picking.pen_cons = True
            notification['params'].update({
                'title': _("Pending consignment %s created due to error : %s"%(cons_number, parent_error)),
            })
            return notification
        else:
            raise UserError(_("Unable to connect to Machship"))
    
    def get_pen_cons_status(self, picking):
        #Get Machship Pending Consignment Status
        if not self.machship_token:
            raise UserError(_("Please set a token to proceed"))
        status_url = MACSHIP_URL + "/apiv2/consignments/getConsignmentByPendingConsignmentId?id=%s"%(picking.machship_cons_id)
        header = {'Accept': 'text/plain', 'token': self.machship_token}
        r = requests.get(status_url, headers=header)
        status_code = r.status_code
        if status_code == 200:
            req_response = r.json()
            if req_response.get('object', False):
                carrier_id = req_response['object'].get('carrierConsignmentId', False)
                cons_id = req_response['object']['id']
                cons_number = req_response['object']['consignmentNumber']
                if carrier_id:
                    picking.carrier_tracking_ref = carrier_id
                    picking.machship_cons_id = cons_id
                    picking.machship_cons_number = cons_number
                    picking.pen_cons = False
                    if req_response['object'].get('carrierId', False) and \
                            picking.carrier_id.chep_fast in ['0', '1']:
                        carrier_id = req_response['object']['carrierId']
                        del_ids = self.env['delivery.carrier'].search([('mach_carrier_id', '=', carrier_id)])
                        if del_ids:
                            picking.carrier_id = del_ids[0].id
                    if req_response['object'].get('trackingPageAccessToken', False):
                        tracking_token = req_response['object']['trackingPageAccessToken']
                        tracking_url = "https://live.machship.com/tracking/#/consignments/%s"%(tracking_token)
                        picking.tracking_url = tracking_url
    
    def get_cons_status(self, picking):
        #Get Machship Consignment Status
        if not self.machship_token:
            raise UserError(_("Please set a token to proceed"))
        status_url = MACSHIP_URL + "/apiv2/consignments/getConsignment?id=%s"%(picking.machship_cons_id)
        header = {'Accept': 'text/plain', 'token': self.machship_token}
        r = requests.get(status_url, headers=header)
        status_code = r.status_code
        if status_code == 200:
            req_response = r.json()
            if req_response.get('object', False):
                status = req_response['object'].get('status', {}).get('name', '')
                picking.machship_status = status
        