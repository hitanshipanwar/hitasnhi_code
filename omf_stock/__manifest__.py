{
    'name': 'OMFoods Inventory',
    'version': '15.0.1.0.0',
    'category': 'Inventory',
    'author': 'Hibou Corp.',
    'license': 'AGPL-3',
    'website': 'https://hibou.io/',
    'maintainer': 'Hibou Corp.',
    'depends': [
        'stock',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/stock_views.xml',
        'views/stock_picking_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'omf_stock/static/src/scss/omf_stock_backend.scss',
        ],
    },
    'installable': True,
    'auto_install': False,
}
