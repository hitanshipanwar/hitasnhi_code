{
    'name': 'Wise Solutions: Strong Password Policy',
    'summary': '''
        Adds additional password policy requirements for enhanced security
    ''',
    'description': '''
        MPV - TASK ID: 2591735:
        Adds the following features:
        1. Initial Password - Admin sets an initial password that users must 
        verify in order to create their account
        2. Enforce Users to change their password every XX days
        3. Require certain rules for passwords (Contain 1 number, uppercase, 
        lowercase, etc)
    ''',
    'license': 'OPL-1',
    'author': 'Odoo Inc',
    'website': 'https://www.odoo.com',
    'category': 'Development Services/Custom Development',
    'version': '1.0',
    'depends': [
        'base_setup',
        'base_automation',
        'web_unsplash',
        'auth_signup',
        'portal' # Unofficially required by auth_signup to create new portal users
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/password_reset_reminder.xml',
        'data/signup_email.xml',
        'views/password_templates.xml',
        'views/res_config_settings.xml',
        'views/res_users_views.xml'
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'post_init_hook': 'post_init_hook'
}