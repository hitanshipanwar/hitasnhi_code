{
    'name': 'Odoo Shopify Connector Extended',
    'version': '15.0',
    'category': 'Sale',
    'summary' : 'Extend for update order status details from Odoo to Shopify without tracking number',
    'description': """
    """,
    'author': 'Emipro Technologies Pvt. Ltd. ',
    'website': 'http://www.emiprotechnologies.com/',
    'maintainer': 'Emipro Technologies Pvt. Ltd.',
    'depends': ['shopify_ept'],    
    'data': [
        'views/shopify_process_import_export_view.xml',
        'views/product_view.xml'
             ],    
    'installable': True,
    'auto_install': False,
    'application' : True,
}
