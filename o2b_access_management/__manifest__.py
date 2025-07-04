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
    'name': 'O2b Access Management',
    'version': '15.0.0.1',
    'author': 'O2b Technologies',
    "license": "LGPL-3",
    'description': """This module helps to Manage Access Rights for Admin, Employee, Manager and Manufacturing Users""",
    'website': 'https://www.o2btechnologies.com',
    'license': 'OPL-1',
    'depends': ['base','hr', 'hr_timesheet', 'fleet', 'sale', 'purchase', 'mrp', 'lunch', 'hr_contract', 'calendar', 'hr_attendance'
    ],
    'data': [
        # 'security/ir.model.access.csv',
        'security/security.xml',
        'views/views.xml',
        'views/fleet_vehicle.xml',
        'views/lunch.xml',
        'views/purchase_order.xml',
        'views/stock_quant.xml',
    ],
    'installable': True,
}
