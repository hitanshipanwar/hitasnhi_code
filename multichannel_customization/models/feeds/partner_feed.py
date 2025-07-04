# -*- coding: utf-8 -*-
##############################################################################
# Copyright (c) 2015-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
# See LICENSE file for full copyright and licensing details.
# License URL : <https://store.webkul.com/license.html/>
##############################################################################
from odoo import models, fields
from odoo.addons.odoo_multi_channel_sale.models.feeds.partner_feed import PartnerFields




class OrderFeed(models.Model):
    _inherit = 'partner.feed'

    company_name = fields.Char(
        string='Company',
    )

    customer_tag= fields.Char(string="Customer Tag")
    
   

    


