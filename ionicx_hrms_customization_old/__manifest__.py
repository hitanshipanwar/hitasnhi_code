# -*- coding: utf-8 -*-
{
    'name': "ionicx_hrms_customization",

    'summary': """
        Send Reminder For Timesheet""",

    'description': """
        Send reminder for Timesheet around 8pm or 9pm.
    """,

    'author': "Hitanshi panwar",
    'website': "http://cognicx.com",
    'category': 'HRMS',
    'version': '0.1',

    'depends': ['base', 'mail', 'hr_timesheet'],

    'data': [
        # 'security/ir.model.access.csv',
        'views/views.xml',
        'views/templates.xml',
        'data/data.xml',
        'data/cron_job.xml',
    ],
}
