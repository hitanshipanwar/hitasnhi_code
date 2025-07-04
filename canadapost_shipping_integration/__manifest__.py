# -*- coding: utf-8 -*-pack
{

    # App information
    'name': 'CanadaPost Odoo Integration',
    'category': 'Website',
    'version': '15.0.0',
    'summary': """""",
    'description': """Integrate & Manage CanadaPost shipping operations from Odoo by using Odoo CanadaPost Integration.Using Canada post Integration we Export the Order to canadapost and generate the label in odoo.We are providing following modules odoo shipping integration,freightcom,shipstation,sendle,shipengine,ChitChats.""",

    # Dependencies

    'depends': ['delivery'],

    # Views

    'data': [
        'views/delivery_carrier_view.xml',
        'views/res_company.xml'],

    # Author
    'author': 'Vraja Technologies',
    'website': 'https://www.vrajatechnologies.com',
    'maintainer': 'Vraja Technologies',
    'live_test_url': 'https://www.vrajatechnologies.com/contactus',
    'images': ['static/description/cover.jpg'],
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False,
    'price': '149',
    'currency': 'EUR',
    'license': 'OPL-1',

}
# 15.0.25.11.21 initial version
