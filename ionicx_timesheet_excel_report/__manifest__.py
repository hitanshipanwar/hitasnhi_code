# -*- coding: utf-8 -*-
{
    'name': "Ionicx Timesheet Excel Report",

    'summary': """
        Timesheet Excel Report""",

    'description': """
        Timesheet Excel
    """,
    'author': "Ionicx IT Solutions",
    'website': "http://cognicx.com",
    'category': 'HRMS',
    'version': '0.1',

    'depends': ['base', 'hr_timesheet', 'hr_holidays', 'project', 'hr', 'mail'],

    'data': [
        'security/ir.model.access.csv',
        'data/ir_cron_data.xml',
        'data/mail_template_data.xml',
        'wizard/timesheet_report_wizard.xml',
        'views/hr_leave_view.xml',
        'views/project.xml',
        'views/project_task.xml',
    ],
}
