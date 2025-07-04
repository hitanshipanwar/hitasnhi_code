# -*- coding: utf-8 -*-
{
    'name': 'Product Labels',
    'version': '12.0',
    'category': 'Inventory',
    'summary': 'Generate the product label report from stock picking',

    'depends': ['stock'],

    'data': [
        'reports/report_menu.xml',
        'reports/report_product_labels.xml',
    ],

    'images': ['static/description/icon.jpg'],

    'author': 'Teqstars',
    'website': 'https://teqstars.com',
    'support': 'support@teqstars.com',
    'maintainer': 'Teqstars',

    'demo': [],
    'installable': False,
    'application': False,
    'auto_install': False,
    'license': 'OPL-1',
}