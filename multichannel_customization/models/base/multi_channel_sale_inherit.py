# -*- coding: utf-8 -*-
##############################################################################
# Copyright (c) 2015-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
# See LICENSE file for full copyright and licensing details.
# License URL : <https://store.webkul.com/license.html/>
##############################################################################

from odoo import fields, models, _, api
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)

class MultiChannelSale(models.Model):
    _inherit = 'multi.channel.sale'

    import_order_after_date = fields.Datetime(
        string="Import Orders After Date")

    import_company_with_order = fields.Boolean(
        "Import Company With Customer", default=False)

    import_order_end_date = fields.Datetime(string="Import Order End Date")

    default_customer_id  = fields.Many2one(
        comodel_name='res.partner',
        string='Default Customer',
        default=lambda self: self.env.ref('odoo_multi_channel_sale.def_customer').id,
    )
   
    

    @api.onchange('import_order_after_date', 'import_order_end_date')
    def import_order_start_end_date(self):
        self.import_order_date = self.import_order_after_date
        if self.import_order_after_date and self.import_order_end_date:
            if self.import_order_after_date >= self.import_order_end_date:
                raise ValidationError(
                    "Start Date should be before then End Date")

    @api.model
    def match_partner_mappings(self, store_id=None, _type='contact',vals=None, domain=None, limit=1,):
        
        res=super(MultiChannelSale,self).match_partner_mappings(store_id,_type,vals,domain,limit)
        if not res:
            email=vals.get('email')
            if email:
                erp_id=self.env['res.partner'].search([('email','=',email),('is_company','!=',True),('type','=','contact')],limit=1)
                if erp_id:
                    create_id = self.create_partner_mapping(erp_id, store_id, _type)
                    return create_id
            elif _type in ['invoice','delivery']:
                address_lines = [
                    ('zip', '=', vals.get('zip')),
                    ('type', '=', _type),
                    ('city', 'ilike', vals.get('city')),
                    ('street', '=', vals.get('street')),
                    ('street2', '=', vals.get('street2')),
                ]
                erp_id=self.env['res.partner'].search(address_lines,limit=1)
                if erp_id:
                    create_id = self.create_partner_mapping(erp_id, store_id, _type)
                    return create_id
        return res

    def shopify_import_order_cron(self):
        self.env['import.operation'].create(
            {'channel_id': self.id}
        ).with_context(cron='order').import_with_filter(
            object='sale.order',
            filter_type='data_range',
            created_at_min=self.import_order_date,
            created_at_max=self.import_order_end_date,
        )

    def get_order_extra_vals(self, vals, from_create=True):
        vals=super(MultiChannelSale,self).get_order_extra_vals(vals, vals)
        vals['channel_name']=self.name
        return vals
     

