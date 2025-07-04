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
    'name': 'O2b Custom Reports',
    'version': '15.0.0.1',
    'author': 'O2b Technologies',
    "license": "LGPL-3",
    'description': """This module make changes on SO PO reports""",
    'website': 'https://www.o2btechnologies.com',
    'license': 'OPL-1',
    'depends': ['base', 'sale', 'purchase'],
    'data': [
        'reports/report_template.xml',
    ],
    'installable': True,
}
