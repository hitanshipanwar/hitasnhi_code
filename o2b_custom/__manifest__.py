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
    'name': 'O2b Custom',
    'version': '15.0.0.1',
    'author': 'O2b Technologies',
    "license": "LGPL-3",
    'description': """This module helps to Restrict Users to change password""",
    'website': 'https://www.o2btechnologies.com',
    'license': 'OPL-1',
    'depends': ['base', 'stock'],
    'data': [
        # 'security/ir.model.access.csv',
        'views/res_company.xml',
        'views/view.xml',
        'views/stock_picking.xml',
        # 'reports/packing_slip.xml',
        'reports/picking_operations_report.xml',
    ],
    'installable': True,
}
