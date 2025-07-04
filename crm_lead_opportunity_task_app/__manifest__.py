# -*- coding: utf-8 -*-
{
    'name': 'Project Task from CRM Opportunity | Lead | Pipeline',
    "author": "Edge Technologies",
    'version': '15.0.1.0',
    'live_test_url': "https://youtu.be/erLtbmLuGLs",
    "images":['static/description/main_screenshot.png'],
    'summary': "Create project task from CRM lead project task from create CRM pipeline task CRM opportunity project CRM pipeline project assign CRM opportunity task create CRM pipeline task from CRM project CRM lead task CRM project pipeline CRM project task",
    'description': """You can manage CRM opportunities, When creating project tasks from CRM opportunities or leads, you can enhance your workflow from lead generation to project execution
    """,
    "license" : "OPL-1",
    'depends': ['base','project','crm',],
    'data': [
            'security/ir.model.access.csv',
            'wizard/create_task_crm.xml',
            'views/crm_lead_inherit.xml',
            ],
    'installable': True,
    'auto_install': False,
    'price': 18,
    'currency': "EUR",
    'category': 'Project',
}
