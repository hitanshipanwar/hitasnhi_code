# -*- coding: utf-8 -*-
{
    'name': "Web Tech",

    'summary': """
        Web Tech""",

    'description': """
        Service Request Section.
    """,

    'author': "Hitanshi Panwar",
    'category': 'HRMS',
    'version': '0.1',

    'depends': ['base', 'mail'],

    'data': [
        'security/ir.model.access.csv',
        # 'security/security.xml',
        'data/email_template.xml',
        'views/candidate_profie_stage.xml',
        'views/candidates_profile.xml',
    ],
}
