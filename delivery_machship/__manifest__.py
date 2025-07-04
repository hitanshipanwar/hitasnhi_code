# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': "Machship Shipping",
    'description': "Send your shippings through Machship and track them online",
    'category': 'Inventory/Delivery',
    'sequence': 277,
    'version': '1.0',
    'application': True,
    'depends': ['delivery', 'stock'],
    'data': [
        'data/delivery_machship_data.xml',
        'views/delivery_machship_view.xml',
        'views/stock_picking.xml',
        'views/stock.xml'
        ],
    'license': 'OEEL-1',
}
