# -*- coding: utf-8 -*-
{
    'name': "Specs - Inter company rules",

    'summary': "Synchronize Specs of Sales Order",
    'author': "Soltein SA de CV",
    'website': "https://www.soltein.mx",
    'contributors': ['Yosbanis Vicente<90yobi90@gmail.com>'],
    'category': 'Uncategorized',
    'version': '0.1',
    'license': 'LGPL-3',
    'depends': ['solt_quarry_door_sale',
                'sale_purchase_inter_company_rules',
                'solt_quarry_door_sale_purchase_stock',
                'solt_quarry_documents_specs'
                ],
    'data': [
        # 'security/ir.model.access.csv',
        'views/views.xml',
    ],
    'auto_install': True
}

