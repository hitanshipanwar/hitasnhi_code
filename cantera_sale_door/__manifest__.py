# -*- coding: utf-8 -*-
{
    'name': "Especificaciones Canteras",

    'summary': """ """,

    'description': """
        
    """,

    'author': "Xmarts",
    'collaborators': "Cesar Noriega",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/12.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '17.0',

    # any module necessary for this one to work correctly
    'depends': ['base',
                'sale_management',
                'sale',
                'crm',
                'sale_crm',
                'product',
                'mail',
                'mrp',
            ],

    # always loaded
    'data': [
        # 'security/security.xml',
        # 'security/ir.model.access.csv',
        # 'data/stage_cantera_type_data.xml',
        # 'report/report_cantera_specs.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        
    ],
    'installable': False
}
