# -*- coding: utf-8 -*-
##############################################################################
# Copyright (c) 2015-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
# See LICENSE file for full copyright and licensing details.
# License URL : <https://store.webkul.com/license.html/>
##############################################################################
from odoo import models, fields
from odoo.addons.odoo_multi_channel_sale.models.feeds.order_feed import OrderFields
OrderFields.extend(['channel_name'])



class OrderFeed(models.Model):
    _inherit = 'order.feed'

    order_tag = fields.Char(string="Order Tag")
    company_name = fields.Char(
        string='Company',
    )

    customer_tag = fields.Char(string="Customer Tag")
    channel_name = fields.Char(string="Channel Name")
    
    refund_json = fields.Char(string="Refund Json")
