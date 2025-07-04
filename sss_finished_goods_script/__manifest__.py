# -*- coding: utf-8 -*-

{
    'name': 'SSS Finished Goods Script',
    'version': '0.1',
    'category': 'inventory',
    'author': 'Spellbound Soft Solutuion',
    'website': 'http://spellboundss.com',
    'summary': 'Finished Goods Script',
    'description': """a Script to import finished Goods and Creates Picking from 
                      that base on the selected Tag/Job Order""",
    'license': "LGPL-3",
    'depends': ['base', 'product', 'stock', 'sale_management', 'delivery','kitchen_purchase_request'],
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        'wizard/import_finished_goods_view.xml',
        'views/sale_order_view_inherit.xml',
        'views/stock_picking_view.xml',
        'reports/delivery_slip.xml',
        'reports/product_product_label.xml',
        'reports/shelf_talker_reports.xml',
    ],
    'assets': {

    },
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False,
}
