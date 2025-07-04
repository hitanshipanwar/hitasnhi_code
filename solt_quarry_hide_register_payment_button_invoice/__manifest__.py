# -*- coding: utf-8 -*-
{
    'name': "Ocultar botón Registrar pagos en las Facturas de clientes",
    'summary': "",
    'author': "Soltein SA de CV",
    'website': "https://www.soltein.mx",
    'category': 'Uncategorized',
    'version': '17.0.0.4',
    'license': 'LGPL-3',
    # any module necessary for this one to work correctly
    'depends': ['account'],
    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'security/res_groups.xml',
        'views/account_move_views.xml',
    ],
}

