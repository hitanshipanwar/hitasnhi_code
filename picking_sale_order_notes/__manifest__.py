{
    'name' : 'Picking Sale Order Notes',
    'description': """--picking_sale_order_notes--""",
    'version':'15.0',
    'summary':'picking_sale_order_notes',
    'author':'Spellbound Soft Solutions',
    'website':'http://spellboundss.com',
    'maintainer': 'Spellbound Soft Solutions',
    'company': 'Spellbound Soft Solutions',
    'depends': ['base','sale','stock'],
    'data': [
    'views/add_notes_view.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
    'license': 'LGPL-3',
}