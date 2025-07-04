# -*- coding: utf-8 -*-
{
    'name': 'OM Foods Barcode Scan',
    'version': '15.0',
    'category': 'Inventory',
    'summary': 'User cannot add more quantity than demand quantity by scan product barcode and If there is no product in the order and the user scan that product so that product is not add.',

    'depends': ['stock_barcode'],

    'data': [
    ],

    'images': ['static/description/icon.jpg'],

    'author': 'Teqstars',
    'website': 'https://teqstars.com',
    'support': 'support@teqstars.com',
    'maintainer': 'Teqstars,Hibou Corp.',

    'assets': {
        'web.assets_backend': [
            'om_foods_barcode_scan/static/src/js/product_barcode.js',
        ],
    },

    'demo': [],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'OPL-1',
}
