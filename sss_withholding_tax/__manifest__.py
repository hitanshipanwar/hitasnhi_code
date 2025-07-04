# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': 'SSS WithHolding Tax',
    'version': '0.18',
    'summary': 'SSS WithHolding Tax',
    'description': """
        Holding Tax
    """,
    'category': "Accounting",
    'author': "Spellbound Soft Solutions",
    'website': "http://spellboundss.com/",
    'maintainer': 'Spellbound Soft Solutions',
    'company': 'Spellbound Soft Solutions',
    'depends': ['base', 'account','sale'],
    'data': [
        'security/ir.model.access.csv',
        'views/product_view.xml',
        'views/account_view.xml',
        'views/account_move_view.xml',
        'views/account_payment_view.xml',
        'views/withholding_tax_view.xml',
        'views/withholding_tax_cert_view.xml',
        'wizard/account_payment_register_views.xml',
        'wizard/create_withholding_tax_cert.xml',
        'report/withholding_tax_cert_form.xml',
        'report/withholding_tax_cert_form_view.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'sss_withholding_tax/static/src/css/style.css',
        ],
    },
    'license': 'LGPL-3',
}
