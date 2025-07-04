# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) Sitaram Solutions (<https://sitaramsolutions.in/>).
#
#    For Module Support : info@sitaramsolutions.in  or Skype : contact.hiren1188
#
##############################################################################

{
    'name': "Import Purchase Orders from Excel/CSV",
    'version': "15.0.0.1",
    'summary': "This module helps you to import Purchase Orders from Excel/CSV",
    'category': 'Purchases',
    'description': """
     Using this module Purchase Orders is imported using excel/CSV sheets
    import Purchase Orders using csv 
    import Purchase Orders using xls
    import bulk purchase from Excel file
    import bulk purchase from CSV file
    Import purchase order lines from CSV or Excel file
    Add PO from Excel
    Add PO from CSV
    import PO
    import large purchase orders in odoo
    import purchase quotations from old legacy system to odoo
    import purchase quotations from old odoo version to newer odoo version
    import RFQ from other erp to odoo
    """,
    'author': "Sitaram",
    'website': "https://sitaramsolutions.in",
    'depends': ['base', 'purchase'],
    'data': [
        'security/ir.model.access.csv',
        'wizard/import_purchase.xml',
        
    ],
    'live_test_url':'https://youtu.be/fPgZYHlavXA',
    'images': ['static/description/banner.png'],
    "price": 20,
    "currency": 'EUR',
    'demo': [],
    "license": "OPL-1",
    'installable': True,
    'auto_install': False,
}
