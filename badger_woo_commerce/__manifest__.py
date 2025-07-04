# -*- coding: utf-8 -*

{
    # Product Info
    'name': 'WMSSoft Badger WooCommerce',
    'version': '0.0.6',
    'license': 'OPL-1',
    'sequence': 1,
    'category': 'Sales',
    'summary': 'This module changes behaviour of Woocommerce Connector',

    # Writer
    'author': 'WMSSoft Pty Ltd',
    'company': 'WMSSoft Pty Ltd',
    'maintainer': 'WMSSoft Pty Ltd',
    'website': "https://www.wmssoft.com.au/",

    # Dependencies
    'depends': ['woo_commerce_ept', 'wmssoft_report', 'account'],

    # View
    'data': [
        'views/stock_picking.xml',
        'views/sale.xml',
        'views/account_move.xml',
        'reports/delivery_template.xml',
        ],

    # Technical
    'installable': True,
    'auto_install': False,
    'application': True,

}
