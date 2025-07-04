# -*- coding: utf-8 -*-
{
    "name": "WMSSoft Invoice Format",

    "summary": """
        WMSSoft Invoice Format""",

    "description": """
        WMSSoft Invoice Format
    """,

    "author": "WMSSoft Pty Ltd",
    "company": "WMSSoft Pty Ltd",
    "maintainer": "WMSSoft Pty Ltd",
    "website": "https://www.wmssoft.com.au/",
    "license": "OPL-1",
    "category": "Account",
    "version": "15.0.0.5",
    "depends": ['stock', 'sale', 'sale_stock', 'sale_management', 'account','delivery', 'purchase','web'],
    "data": [
        'views/account_move_view.xml',
        'views/stock_picking.xml',
        'views/report_company.xml',
        'views/res_partner.xml',
        'views/sale_order.xml',
        'views/purchase_order.xml',
        'views/stock_package_type.xml',
        'data/invoiceformat.xml',
        'security/ir.model.access.csv',
        'reports/invoice_format.xml',
        'reports/header_template.xml',
        'reports/custom_template.xml',
        'reports/sale_template.xml',
        'reports/sale_order_template.xml',
        # 'reports/delivery_template.xml',
        'reports/purchase_template.xml',
        'reports/comm_invoice_format.xml',
        'reports/layouts.xml'
    ],
    'assets': {
        'web.report_assets_common': [
            'wmssoft_report/static/src/scss/**/*',
        ],
    },
    "installable": True,
    "auto_install": False,
}
