# -*- coding: utf-8 -*-

from odoo import _, api, fields, models

class ProductReplenishInherit(models.TransientModel):
    _inherit = 'product.replenish'


class ProcurementGroup(models.Model):
    _inherit = 'procurement.group'

    # @api.model
    # def run(self, procurements, raise_user_error=True):
    # 	print(' custom ==================================')
    # 	return