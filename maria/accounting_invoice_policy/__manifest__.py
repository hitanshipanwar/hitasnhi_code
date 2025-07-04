# -*- coding: utf-8 -*-
{
    'name': "Accounting Invoice Policy",
    'summary': """Accounting Invoice Policy""",
    'description': """To Create Invoice on Selecion Basis Like Allow Combined Invoices/ Never
    Combine Invoices/ Split Invoice per VAT Basis""",
    'author': "Linserv Aktiebolag",
    'website': "https://www.linserv.se",
    'category': 'Account',
    'contributors': ['Sujeet Butani <sujeet.butani@linserv.se>'],
    'version': '15.0.1',
    'license': 'OPL-1',
    'depends': ['base', 'account', 'sale'],
    'data': [
        'views/views.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}
