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
    'name': 'O2B Helpdesk Team',
    'summary': 'Helpdesk',
    'description': 'Helpdesk Team Management',
    'author': 'O2b Technologies',
    'website': 'https://www.o2btechnologies.com',
    'category': 'Uncategorized',
    'version': '16.1',
    'license': 'OPL-1',
    'depends': ['helpdesk', 'mail', 'wise_password_14','o2b_missing_fields'],
    'data': [
        # 'security/helpdesk_security.xml',
        'security/ir.model.access.csv',
        'views/helpdesk_view.xml',
        'views/helpdesk_config.xml',
    ],
}
