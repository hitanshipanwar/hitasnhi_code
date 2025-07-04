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
    'name': 'O2B Stock I',
    'summary': 'Add the Get Rate functionality when the delivery method in the sale order is set to Free Shipping.',
    'description': 'Add the Get Rate functionality when the delivery method in the sale order is set to Free Shipping.',
    'author': 'O2b Technologies',
    'website': 'https://www.o2btechnologies.com',
    'category': 'Inventory',
    'version': '15.0.3',
    'license': 'OPL-1',
    'depends': ['base', 'stock_barcode'],
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        # 'views/stock_i_view.xml',
        # 'wizard/update_stock_i_warehouse.xml',
        'views/stock_i_warehouse_view.xml',
        'views/stock_aisle_barcode_view.xml',
        'views/mrp_production_view.xml',
        'views/mrp_production_report.xml',
        'views/aisle_client_view.xml',
        'views/aisle_location.xml',
        'views/ir_config_settings.xml',
        'views/stock_package_type.xml',
        'views/res_company.xml',
        'reports/report.xml',
        'reports/stock_package_type.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'o2b_stock_custom/static/src/**/*.js',
            # 'o2b_stock_custom/static/src/js/main_menu.js',
            # 'o2b_stock_custom/static/src/js/asile_tag.js',

        ],
        'web.assets_qweb': [
            'o2b_stock_custom/static/src/**/*.xml',
        ],
    },
    'installable': True,
    'application': True,
    'auto_install': False,
}