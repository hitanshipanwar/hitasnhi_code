{
    'name': 'CRM History',
    'description': """--crm_history--""",
    'version': '15.0.6',
    'summary': 'crm_history',
    'author': 'Spellbound Soft Solutions',
    'website': 'http://spellboundss.com',
    'maintainer': 'Spellbound Soft Solutions',
    'company': 'Spellbound Soft Solutions',
    'depends': ['base', 'mail', 'stock'],
    'data': [
        'security/ir.model.access.csv',
        'data/crm_history_demo.xml',
        'views/crm_history_view.xml',
        'views/crm_history_page.xml',
        'views/partner_activity_history_view.xml',
        'views/res_partner.xml',
        # 'views/mail_activity_view.xml',
        # 'wizard/outbound_wizard.xml',
        'reports/action_report_crm.xml',
        'reports/sale_activity_report_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'crm_history_module/static/css/activity_history_field.css',
            'crm_history_module/static/src/js/pivot_view.js',
            'crm_history_module/static/src/js/activity.js',
        ],
        'web.assets_qweb': [
            'crm_history_module/static/src/xml/*.xml',
        ]
    },
    'application': True,
    'license': 'LGPL-3',
}
