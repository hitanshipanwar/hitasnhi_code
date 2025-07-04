# -*- coding: utf-8 -*-
{
    'name': "My Module",

    'summary': """
        My Module""",

    'description': """
        Account Move.
    """,

    'author': "Hitanshi Panwar",
    'category': 'Account',
    'version': '0.1',

    'depends': ['base', 'account'],

    'data': [
        # 'security/ir.model.access.csv',
        # 'security/security.xml',
        'views/account_move.xml',
        'reports/account_move_report.xml',
    ],
}
