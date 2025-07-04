{
    'name': 'OMFoods Sales',
    'version': '15.0.1.1.0',
    'category': 'Sales',
    'author': 'Hibou Corp.',
    'license': 'AGPL-3',
    'website': 'https://hibou.io/',
    'maintainer': 'Hibou Corp.',
    'depends': [
        'sale',
        'delivery',
        'mrp',
        'purchase_stock',
        'stock',
    ],
    'data': [
        'data/ir_cron_data.xml',
        'views/product_views.xml',
        'views/sale_views.xml',
        'views/stock_views.xml',
    ],
    'installable': True,
    'auto_install': False,
}
