# -*- coding: utf-8 -*-
{
    'name': "Specs - MTO Sale <-> Purchase",

    'summary': "Specs SO/PO relation in case of MTO",
    'author': "Soltein SA de CV",
    'website': "https://www.soltein.mx",
    'contributors': ['Yosbanis Vicente<90yobi90@gmail.com>'],
    'category': 'Uncategorized',
    'version': '0.1',
    'license': 'LGPL-3',
    'depends': ['solt_quarry_door_sale', 'sale_purchase_stock'],
    'data': [
        # 'security/ir.model.access.csv',
        'views/purchase_order_views.xml',
        'views/specs_sale_views.xml',
    ],
}

