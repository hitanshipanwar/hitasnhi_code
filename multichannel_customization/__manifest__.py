# -*- coding: utf-8 -*-
#################################################################################
# Author      : Webkul Software Pvt. Ltd. (<https://webkul.com/>)
# Copyright(c): 2015-Present Webkul Software Pvt. Ltd.
# All Rights Reserved.
#
#
#
# This program is copyright property of the author mentioned above.
# You can`t redistribute it and/or modify it.
#
#
# You should have received a copy of the License along with this program.
# If not, see <https://store.webkul.com/license.html/>
#################################################################################
{
    "name": "Odoo Multi-Channel Customization",
    "summary": """The multi channel module is Multiple platform connector with Odoo. You can connect and manage various platforms like Amazon, Bagisto, Cscart, CSV, Ebay, Etsy, Flipkart, Magento 2, Prestashop, Shopify, Walmart, Woocommerce in odoo with the help of Odoo multichannel sale bridge.""",
    "category": "eCommerce",
    "version": "2.7.17",
    "sequence": 1,
    "author": "Webkul Software Pvt. Ltd.",
    "license": "Other proprietary",
    "website": "https://store.webkul.com/odoo-multi-channel-sale.html",
    "description": """Odoo multi-channel Customization
     """,
   
    "depends": [
        'shopify_odoo_bridge',
        
    ],
    "data": [
        'views/core/sale_order.xml',
        'views/base/order_feed.xml',
        'views/base/multi_channel_sale_form_inherit.xml',
        'wizard/export_operation.xml',
        'wizard/export_template.xml',
    ],
        "application": True,
    "installable": True,
    "auto_install": False,
   
    "pre_init_hook": "pre_init_check",
}
