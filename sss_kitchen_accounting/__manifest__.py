# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name' : 'SSS Accounting Kitchen',
    'version' : '0.11',
    'summary': 'Accounting Kitchen',
    'description': """
        Accounting Kitchen
    """,
    'category': "Accounting",
    'author': "Spellbound Soft Solutions",
    'website': "http://spellboundss.com/",
    'maintainer': 'Spellbound Soft Solutions',
    'company': 'Spellbound Soft Solutions',
    'depends' : ['base','account'],
    'data': [
        # 'security/ir.model.access.csv',
        'wizard/account_payment_register.xml'
    ],

    'assets': {
    },
    
    'license': 'LGPL-3',
}
