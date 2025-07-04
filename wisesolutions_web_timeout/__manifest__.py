{
    'name': "Wise Solutions: Session Timeout",

    'summary': """Allow Admin to set session timeout for all users""",

    'description': """
Task ID: 2733308
When a user is logged into an Odoo DB, the Odoo Server stores a "session" and until that is deleted or the user clears their browser cache, they will never have to log in again. 
With this behavior, the system doesn’t update the field Latest authentication and the user doesn’t need to type the password. 
The client needs to know when was the last time that a user was logged in and ask for the password after a session is finished.
    """,

    'author': "Odoo Inc.",
    'website': "http://www.odoo.com",
    'category': 'Customizations/Studio',
    'license': 'OEEL-1',
    'version': '0.1',
    'depends': ['base','base_setup', 'web'],
    'data': [
        'views/res_config_settings.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'wisesolutions_web_timeout/static/src/core/errors/*',
        ],
    },
}