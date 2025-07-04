# -*- coding: utf-8 -*-

{
    'name': 'Kitchen Purchase Request',
    'version': '0.23',
    'category': 'purchase',
    'author':'Spellbound Soft Solutuion',
    'summary': 'Kitchen Purchase Request for Product',
    'description': """Employee Purchase Request to Manager for their Needs""",
    'license':"LGPL-3",
    'depends': ['base', 'hr', 'purchase', 'product', 'crm_design', 'purchase_stock', 'stock', 'sale_management','sales_team'],
    'data': [
        'security/ir.model.access.csv',
        'security/purchase_request.xml',
        'security/security.xml',
        'data/sequence.xml',
        'data/purchase_request_activity.xml',
        'data/purchase_department.xml',
        'data/stock_package_type.xml',
        'views/purchase_request_view.xml',
        'views/stock_product_views.xml',
        'views/stock_quant_view_inerit.xml',
        'views/purchase_order_views_inherited.xml',
        'wizard/reject_purchase_request_view.xml',
        # 'wizard/import_finished_goods_view.xml',
        'wizard/approve_purchase_request_view.xml',
        'reports/purchase_order_inherit.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'kitchen_purchase_request/static/src/js/digital_sign.js',
            'kitchen_purchase_request/static/src/xml/inherit_base.xml',
            'kitchen_purchase_request/static/src/css/style.css',
        ],
        'web.assets_qweb': [
            'kitchen_purchase_request/static/src/xml/digital_sign.xml',
        ],
    },
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False,
}