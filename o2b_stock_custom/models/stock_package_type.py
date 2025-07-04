# -*- coding: utf-8 -*-
##########################################################################
# Author      : O2b Technologies Pvt. Ltd.(<www.o2btechnologies.com>)
# Copyright(c): 2016-Present O2b Technologies Pvt. Ltd.
# All Rights Reserved.
#
# This program is copyright property of the author mentioned above.
# You can`t redistribute it and/or modify it.
#
##########################################################################
from odoo import models, fields

class StockQuantPackage(models.Model):
    _inherit = 'stock.package.type'

    def print_label(self):
        return self.env.ref('o2b_stock_custom.action_stock_package_type_report_label').report_action(self)
