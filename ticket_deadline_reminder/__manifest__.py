# -*- coding: utf-8 -*-

{
    'name': "Ticket Deadline Reminder",
    'version': '16.0.1.0.0',
    'author': 'Ionicx IT Solutions',
    'company': 'Ionicx IT Solutions',
    'maintainer': 'Ionicx IT Solutions',
    'website': 'http://cognicx.com',
    'summary': '''Automatically Send Mail To Responsible User if Deadline Of Task is Today''',
    'description': '''Automatically Send Mail To Responsible User if Deadline Of Task is Today''',
    'category': "Project",
    'depends': ['project'],
    'license': 'AGPL-3',
    'data': [
            'views/deadline_reminder_view.xml',
            'views/deadline_reminder_cron.xml',
            'data/deadline_reminder_action_data.xml'
             ],
    # 'images': ['static/description/banner.png'],
    'installable': True,
    'auto_install': False
}
