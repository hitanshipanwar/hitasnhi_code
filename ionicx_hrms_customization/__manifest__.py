{
    'name': 'Timesheet Reminder',
    'version': '16.0.3',
    'category': 'Project',
    'author': 'Ionicx IT Solutions',
    'summary': "Timesheet Reminder",
    'description': "Timesheet Reminder",
    'depends': ['base', 'mail', 'hr', 'hr_timesheet'],
    'data': [
        'data/ir_cron_data.xml',
        'data/mail_template_data.xml',
        'views/views.xml',
        'views/hr_leave.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
