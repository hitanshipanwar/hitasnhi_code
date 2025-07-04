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
    'name': 'O2b SMTP Per User',
    'summary': """
        SMTP Per User""",
    'description': """
        SMTP Per User
    """,
    'author': 'O2b Technologies',
    'website': 'http://www.o2btechnologies.com',
    'license': 'OPL-1',
    'category': 'Uncategorized',
    'version': '1.0',
    'depends': ['base', 'mail', 'google_gmail', 'microsoft_outlook', 'hr'],
    'data': [
        'security/ir.model.access.csv',
        'views/user_view.xml',
    ],
}

