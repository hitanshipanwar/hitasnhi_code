# -*- coding: utf-8 -*-
{
    'name': "Specs - MRP",

    'summary': "Creates a bill of materials from the Specs configuration",
    'author': "Soltein SA de CV",
    'website': "https://www.soltein.mx",
    'contributors': ['Yosbanis Vicente<90yobi90@gmail.com>'],
    'category': 'Uncategorized',
    'version': '17.0.0.3',
    'license': 'LGPL-3',
    'depends': ['solt_quarry_door_sale', 'mrp', 'solt_quarry_door_sale_purchase_stock', 'sale_mrp'],
    'data': [
        'data/stage_cantera_type_data.xml',
        'views/specs_sale_views.xml',
        'views/mrp_bom_views.xml',
        'views/res_config_settings_views.xml',
    ],
    'auto_install': True
}

