# -*- coding: utf-8 -*-
{
    "name": "WMSSoft Barcode labels",

    "summary": """
        WMSSoft Barcode labels customisation""",

    "description": """
        WMSSoft Barcode labels customisation
    """,

    "author": "WMSSoft Pty Ltd",
    "company": "WMSSoft Pty Ltd",
    "maintainer": "WMSSoft Pty Ltd",
    "website": "https://www.wmssoft.com.au/",
    "license": "OPL-1",
    "category": "Account",
    "version": "15.0.0.1",
    "depends": ['stock', 'product'],
    "data": [
        'reports/location_barcode.xml',
        'reports/product_zpl.xml',
        'reports/product_label.xml',
        'reports/employee_barcode.xml',
        'reports/sale_order_barcode.xml',
        'reports/inventory_sale_order_barcode.xml',
    ],
    "installable": True,
    "auto_install": False,
}
