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
    'name': "Add missing fields",
    'summary': 'Adds new fields to Quality Metrics',
    'license': 'OPL-1',
    'website': 'https://www.odoo.com',
    'version': '0.1',
    'author': 'Odoo Inc',
    'description': 'This module extends the quality.metrics model to add additional fields which is present in odoo 13 but not in odoo 16.',
    'depends': ['contacts', 'helpdesk','wise_helpdesk','mail' ,'web'],
    'data': [
      "security/ir.model.access.csv",
      "views/inherit_view.xml",
    ],
    'installable': True,
    'application': False,
}
