{
    'name': "Wise Solutions: Change Request Custom Last updated by and on",
    'summary': 'Create custom models based on the studio models',
    'sequence': 100,
    'license': 'OPL-1',
    'website': 'https://www.odoo.com',
    'version': '1.1',
    'author': 'Odoo Inc',
    'description': """
        Task id:  2817333
        'This module is to create a field to select the users which can update the write by and on fields'.
    """,
    'depends': ['contacts', 'helpdesk', 'write_record_mixin'],
    'data': [
        'security/security.xml',
        'views/helpdesk_views.xml',
        'views/res_partner_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
