# -*- coding: utf-8 -*-
{
    'name': "Specs - Helpdesk",

    'summary': "Create Card Request from Helpdesk App",

    'description': """
Long description of module's purpose
    """,

    'author': "Soltein SA de CV",
    'website': "https://www.soltein.mx",
    'contributors': ['Yosbanis Vicente<90yobi90@gmail.com>'],
    'category': 'Uncategorized',
    'version': '0.1',
    'license': 'LGPL-3',
    'depends': ['solt_quarry_door_sale', 'helpdesk_sale'],
    'data': [
        # 'security/ir.model.access.csv',
        'data/stage_cantera_type_data.xml',
        'data/helpdesk_data.xml',
        'views/helpdesk_ticket_type_views.xml',
        'views/helpdesk_team_views.xml',
        'views/helpdesk_ticket_views.xml',
        'views/helpdesk_stage_views.xml',
        'views/specs_sale_views.xml',
    ],
}

