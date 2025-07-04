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
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    password_expiration = fields.Integer(
        related="company_id.password_expiration", readonly=False
    )
    password_minimum = fields.Integer(
        related="company_id.password_minimum", readonly=False
    )
    password_history = fields.Integer(
        related="company_id.password_history", readonly=False
    )
    password_lower = fields.Integer(related="company_id.password_lower", readonly=False)
    password_upper = fields.Integer(related="company_id.password_upper", readonly=False)
    password_numeric = fields.Integer(
        related="company_id.password_numeric", readonly=False
    )
    password_special = fields.Integer(
        related="company_id.password_special", readonly=False
    )
