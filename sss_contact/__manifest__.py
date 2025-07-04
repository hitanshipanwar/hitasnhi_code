# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name' : 'SSS Contacts',
    'version' : '16.0.4',
    'summary': 'Contacts',
    'description': """
        Res Partner
    """,
    'author': "Spellbound Soft Solutions",
    'website': "http://spellboundss.com/",
    'maintainer': 'Spellbound Soft Solutions',
    'company': 'Spellbound Soft Solutions',
    'depends' : ['base', 'account'],
    'data': [
        'views/res_partner_inherit.xml',
    ],
    
    'license': 'LGPL-3',
    'installable': True,
    'application': True,
    'auto_install': False,
}