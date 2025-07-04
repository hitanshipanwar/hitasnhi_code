{
    'name': 'OMFoods Manufacturing',
    'version': '15.0.1.0.1',
    'category': 'Manufacturing',
    'author': 'Hibou Corp.',
    'license': 'AGPL-3',
    'website': 'https://hibou.io/',
    'maintainer': 'Hibou Corp.',
    'depends': [
        'base_exception_user',
        'purchase_mrp',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/mrp_production_exception.xml',
        'views/data_migration.xml',
        'views/mrp_production_views.xml',
        'views/purchase_order_views.xml',
        'views/stock_views.xml',
        'wizard/mrp_production_exception_confirm_views.xml',
    ],
    'installable': True,
    'auto_install': False,
}
