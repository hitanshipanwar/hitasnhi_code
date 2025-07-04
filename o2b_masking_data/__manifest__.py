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
    'name': 'O2B Masking Data',
    'summary': 'This module mask data from the user',
    'description': 'This module mask data from the user',
    'author': 'O2b Technologies',
    'website': 'https://www.o2btechnologies.com',
    'category': 'Uncategorized',
    'version': '17.0',
    'license': 'OPL-1',
    'depends': ['base', 'o2b_patient_master'],
    'data': [
        'security/security.xml',
        'views/res_users.xml',
    ],
}