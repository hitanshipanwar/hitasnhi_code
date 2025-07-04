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
{
    'name': 'O2B Password Security',
    'summary': 'Allow admin to set password security requirements.',
    'description': 'Allow admin to set password security requirements.',
    'author': 'O2b Technologies',
    'website': 'https://www.o2btechnologies.com',
    'category': 'Tools',
    'version': '17.0',
    'license': 'OPL-1',
    "depends": [
        "auth_signup",
        "auth_password_policy_signup",
    ],
    "data": [
        "views/res_config_settings_views.xml",
        "security/ir.model.access.csv",
        "security/res_users_pass_history.xml",
    ],
    "demo": [
        "demo/res_users.xml",
    ],
    "installable": True,
}