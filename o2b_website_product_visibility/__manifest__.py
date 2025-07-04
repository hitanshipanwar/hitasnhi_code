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
    'name': 'O2b website product visibility',
    'version': '15.0.0.1',
    'author': 'O2b Technologies',
    "license": "LGPL-3",
    'description': """This module helps to Restrict produt visibility on website""",
    'website': 'https://www.o2btechnologies.com',
    'license': 'OPL-1',
    'depends': ['base', 'web', 'website_sale'],
    'data': [
        # 'security/ir.model.access.csv',
        'security/security.xml',
        'views/product_public_category.xml',
    ],
    'installable': True,
}
