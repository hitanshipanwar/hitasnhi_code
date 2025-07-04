# -*- coding: utf-8 -*-

from odoo import models, fields


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    create_batch_payment = fields.Boolean(related='company_id.create_batch_payment', string="Create Bill.Com Payments Batch", readonly=False)

