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


class ResUsersPassHistory(models.Model):
    _name = "res.users.pass.history"
    _description = "Res Users Password History"

    _order = "user_id, date desc, id desc"

    user_id = fields.Many2one(
        string="User",
        comodel_name="res.users",
        ondelete="cascade",
        index=True,
    )
    password_crypt = fields.Char(
        string="Encrypted Password",
    )
    date = fields.Datetime(
        default=lambda s: fields.Datetime.now(),
        index=True,
    )
