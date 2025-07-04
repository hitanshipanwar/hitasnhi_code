# -*- coding: utf-8 -*-
{
    'name': "Specs - Invoice",
    'summary': "Short (1 phrase/line) summary of the module's purpose",
    'author': "Soltein SA de CV",
    'website': "https://www.soltein.mx",
    'category': 'Uncategorized',
    'version': '0.1',
    'license': 'LGPL-3',
    'depends': ['l10n_mx_edi', 'solt_quarry_door_sale', 'stock_account'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/report_invoice.xml',
    ],
}

