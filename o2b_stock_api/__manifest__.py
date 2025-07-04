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
    'name': 'O2B Stock API',
    'summary': 'Add the Get Rate functionality when the delivery method in the sale order is set to Free Shipping.',
    'description': 'Add the Get Rate functionality when the delivery method in the sale order is set to Free Shipping.',
    'author': 'O2b Technologies',
    'website': 'https://www.o2btechnologies.com',
    'category': 'Inventory',
    'version': '15.0.0',
    'license': 'OPL-1',
    'depends': ['base', 'stock_barcode', 'delivery', 'stock', 'sale', 'purolator_shipping_integration', 'canadapost_shipping_integration', 'delivery_fedex'],
    'data': [
        'security/ir.model.access.csv',
        'views/stock_picking.xml',
        'views/sale_order.xml',
        'views/delivery_carrier.xml',
        'views/stock_return_picking.xml',
        'reports/custom_label_template.xml',
        'reports/picking_sheet_new.xml',
        'reports/report.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'o2b_stock_api/static/src/js/barcode.js',
            'o2b_stock_api/static/src/js/stock_barcode_menu.js',
            'o2b_stock_api/static/src/components/main.js',
        ],
        'web.assets_qweb': [
            'o2b_stock_api/static/src/components/main.xml'
        ],
    },
    'installable': True,
    'application': True,
    'auto_install': False,
}