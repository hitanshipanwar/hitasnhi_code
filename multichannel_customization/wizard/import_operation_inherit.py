# -*- coding: utf-8 -*-
##############################################################################
# Copyright (c) 2015-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
# See LICENSE file for full copyright and licensing details.
# License URL : <https://store.webkul.com/license.html/>
##############################################################################
from odoo import fields, models
from datetime import datetime


class ImportOperation(models.TransientModel):
    _inherit = 'import.operation'

    def shopify_get_filter(self):
        kw = super(ImportOperation, self).shopify_get_filter()
        if self.channel_id.import_order_after_date or self.channel_id.import_order_end_date:
            if self.channel == 'shopify' and self.shopify_filter_type in ['all', 'data_range'] and self.object == 'sale.order':
                kw = {'filter_type': 'data_range'}
                kw['created_at_min'] = self.channel_id.import_order_after_date
                kw['created_at_max'] = self.channel_id.import_order_end_date if self.channel_id.import_order_end_date else datetime.today(
                ).strftime("%d/%m/%Y %H:%M:%S")
        return kw
