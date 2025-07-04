# -*- coding: utf-8 -*-
{
    'name': "Ionicx Hr Extend",

    'summary': """
        Ionicx HR Extend""",

    'description': """
        Service Request Section.
    """,

    'author': "Ionicx IT Solutions",
    'website': "http://cognicx.com",
    'category': 'HRMS',
    'version': '0.1',

    'depends': ['base', 'project', 'hr', 'hr_attendance', 'hr_timesheet','utm', 'mail', 'ionicx_timesheet_excel_report', 'hr_holidays'],

    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        'data/data.xml',
        'data/email_template.xml',
        'reports/service_request_report.xml',
        'reports/project_profitability.xml',
        'views/hr_complaint.xml',
        'views/hr_employee.xml',
        'views/hr_attendance.xml',
        'views/hr_leave.xml',
        'views/project_profitability.xml',
        'views/hr_leave_type.xml',
        'views/hr_timehseet.xml',
        'views/res_config.xml',
    ],
}
