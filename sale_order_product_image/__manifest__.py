{
    'name': 'Sale Order Product Image',
    'version': '1.0',
    'summary': 'Sale order line with product image',
    'depends': ['sale_management', 'base','sale'],
    'category': 'Sales',
    'data': [
        'views/sale_order_product_image.xml',
        'report/sale_order_report.xml',
    ],
    "auto_install": False,
    "installable": True,
    "application": False,
}