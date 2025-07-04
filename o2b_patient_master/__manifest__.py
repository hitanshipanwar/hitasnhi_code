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
    'name': 'O2B Patient Master',
    'summary': 'This module enables the display of Patient Master',
    'description': 'This module enables the display of Patient Master',
    'author': 'O2b Technologies',
    'website': 'https://www.o2btechnologies.com',
    'category': 'Uncategorized',
    'version': '17.0',
    'license': 'OPL-1',
    'depends': ['base', 'mail'],
    'data': [
        'security/ir.model.access.csv',
        # 'security/security.xml',
        'views/patient.xml',
    ],
}