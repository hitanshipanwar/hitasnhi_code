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
    'name': 'O2B Settings Access Rights Tracking',
    'summary': 'This module display the chatter in res users',
    'description': 'This module display the chatter in res users',
    'author': 'O2b Technologies',
    'website': 'https://www.o2btechnologies.com',
    'category': 'Uncategorized',
    'version': '17.1',
    'license': 'OPL-1',
    'depends': ['base', 'mail', 'auth_oauth', 'auth_totp'],
    'data': [
        'views/views.xml',
    ],
}