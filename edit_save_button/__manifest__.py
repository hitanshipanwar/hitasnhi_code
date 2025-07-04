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
    'name': 'Edit Button In Odoo16',
    'version': '16.0.1.0.4',
    'summary': 'Edit Button Odoo16',
    'description': 'Edit Button in Odoo16',
    'author': 'O2b Technologies',
    'website': 'https://www.o2btechnologies.com',
    'images': ['static/description/banner.png'],
    'website': 'https://www.cybrosys.com',
    'depends': ['base', 'product'],
    'data': [
        'views/product_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            '/edit_save_button/static/src/views/form/form_controller.js',
            '/edit_save_button/static/src/views/form/form_controller.xml',
        ]
    },
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
