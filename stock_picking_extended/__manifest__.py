{
    'name': 'Stock Picking extended',
    'summary': 'Stock picking extended delivery slip change and select order picker ',
    'version': '15.0',
    'author': 'Teqstars',
    'website': 'https://teqstars.com',
    'support': 'info@teqstars.com',
    'maintainer': 'Teqstars',

    'category': 'Delivery',
    'depends': ['stock'],
    'data': [
        'security/ir.model.access.csv',
        'views/stock_picking_views.xml',
        'views/report_pickingslip.xml',
        'views/stock_report_views.xml',
        'views/product.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
