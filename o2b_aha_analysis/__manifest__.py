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
    'name': 'O2B Helpdesk AHA Analysis',
    'summary': 'Helpdesk',
    'description': 'Helpdesk AHA Analysis',
    'author': 'O2b Technologies',
    'website': 'https://www.o2btechnologies.com',
    'category': 'Uncategorized',
    'version': '16.1',
    'license': 'OPL-1',
    'depends': ['helpdesk', 'wise_helpdesk'],
    'data': [
        'security/ir.model.access.csv',
        'views/aha_analysis.xml',
    ],
}
