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


class ResCompany(models.Model):
    _inherit = "res.company"

    password_expiration = fields.Integer(
        "Days",
        default=60,
        help="How many days until passwords expire",
    )
    password_lower = fields.Integer(
        "Lowercase",
        default=1,
        help="Require number of lowercase letters",
    )
    password_upper = fields.Integer(
        "Uppercase",
        default=1,
        help="Require number of uppercase letters",
    )
    password_numeric = fields.Integer(
        "Numeric",
        default=1,
        help="Require number of numeric digits",
    )
    password_special = fields.Integer(
        "Special",
        default=1,
        help="Require number of unique special characters",
    )
    password_history = fields.Integer(
        "History",
        default=30,
        help="Disallow reuse of this many previous passwords - use negative "
        "number for infinite, or 0 to disable",
    )
    password_minimum = fields.Integer(
        "Minimum Hours",
        default=24,
        help="Amount of hours until a user may change password again",
    )
