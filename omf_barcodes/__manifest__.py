{
    'name': 'OMFoods Barcodes',
    'version': '15.0.1.0.0',
    'category': 'Sale',
    'summary' : 'OMFoods Barcodes Customizations',
    'description': """
Customizations to Barcodes
==========================
1. Display aisle next to product name and sort by aisle
    """,
    'author': 'Hibou Corp.',
    'website': 'https://hibou.io/',
    'maintainer': 'Hibou Corp.',
    'depends': [
        'stock_barcode',
        'stock_picking_extended',
    ],
    'data': [
    ],
    'assets': {
        'web.assets_backend': [
            'omf_barcodes/static/src/**/*.js',
        ],
        'web.assets_qweb': [
            'omf_barcodes/static/src/**/*.xml',
        ],
    },
    'installable': True,
    'auto_install': False,
    'application' : True,
    'license': 'OPL-1',
}
