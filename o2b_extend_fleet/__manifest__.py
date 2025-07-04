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
    'name': 'O2b Extend Fleet',
    'version': '15.0.0.1',
    'author': 'O2b Technologies',
    "license": "LGPL-3",
    'description': """This module will extend fleet vehicle.""",
    'website': 'https://www.o2btechnologies.com',
    'license': 'OPL-1',
    'depends': ['base', 'mail', 'fleet', 'maintenance'],
    'data': [
        'security/ir.model.access.csv',
        'data/email_template.xml',
        'data/cron.xml',
        'views/fleet_vehicle_views.xml',
        'views/highway_toll.xml',
        'views/fleet_fine.xml',
        'views/res_partner.xml',
        'views/maintenance.xml',
    ],
    'installable': True,
}
