# -*- coding: utf-8 -*-
{
    'name': "Ionicx Payslip",

    'summary': """
        Ionicx Payslip""",

    'description': """
        Payslip.
    """,

    'author': "Ionicx IT Solutions",
    'website': "http://cognicx.com",
    'category': 'HRMS',
    'version': '0.1',

    'depends': ['base', 'mail', 'portal', 'hr', 'web'],

    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'reports/payslip_report.xml',
        'views/payslip_payslip.xml',
        'views/portal_template.xml',
    ],
}
