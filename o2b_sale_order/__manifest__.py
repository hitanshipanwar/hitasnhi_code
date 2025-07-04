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
    'name': 'O2b Sale Order',
    'version': '1.0',
    'category': 'Sales',
    'summary': 'Automatically Invoice Generation & DST Sequence',
    'author': 'O2b Technologies',
    'website': 'https://www.o2btechnologies.com',
    'depends': ['base','sale','stock','sale_management','sales_team','account','account_accountant'],
    'data': [
        'security/ir.model.access.csv',
        'views/sales_team.xml',
        'data/sequence.xml',
    ],
    'installable': True,
    'application': True,
    'category': 'Uncategorized',
}