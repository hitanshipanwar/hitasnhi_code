{
    'name': 'HR Timesheet',
    'version': '1.0.0',
    'category': 'OFC',
    'sequence': -100,
    'summary': 'ld hr timesheet',
    'description': "timesheet entering data",
    'depends': ['base', 'project', 'hr_timesheet'],
    'data': [
        # 'views/hr_timesheet_views.xml',
        'views/res_config_settings.xml',
    ],
    'demo': [],
    'application': True,
    'auto_install': False,
    'licence': 'LGPL-3',
}
