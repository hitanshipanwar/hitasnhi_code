
# -*- coding: utf-8 -*-
##########################################################################
# Author      : O2b Technologies Pvt. Ltd.(<www.o2btechnologies.com>)
# Copyright(c): 2016-Present O2b Technologies Pvt. Ltd.
# All Rights Reserved.
#
# This program is copyright property of the author mentioned above.
# You can`t redistribute it and/or modify it.
#
##########################################################################
{
    'name'          : 'O2B Vendor Dashboard',
    'version'       : '1.0',
    'summary'       : 'Custom O2B theme for for Vendor Dashboard.',
    'description'   : 'Custom O2B theme for for Vendor Dashboard.',
    'author'        : 'O2b Technologies',
    'website'       : 'https://www.o2btechnologies.com',
    'license'       : 'OPL-1',
    'version'       : '16.0',
    'data'          : [
                        'views/menu_templates.xml',
                        'views/vendor_dashboard_side_menu.xml',
                        'views/login/change_password_template.xml',
                        'views/controller_vendor_template.xml',
                        'views/controller_purchase_template.xml',
                        'views/controller_unpaid_invoice_template.xml',
                        'views/controller_paid_invoice_template.xml',
                        'views/create_invoice_template.xml',
                        'views/open_invoice_template.xml',
                        'views/search_template/vendor_search_template.xml',
                        'views/search_template/purchase_search_template.xml',
                        'views/search_template/unpaid_invoice_search_template.xml',
                        'views/search_template/paid_invoice_search_template.xml',
                        'views/search_template/not_found_template.xml',
                        'views/training_videos_template.xml',
                        'views/setting_template.xml',
                        'views/phone_verification/check_phone_form.xml',
                        ],
    'depends'       : ['base','sale','product','website', 'website_sale','web'],
    # 'assets': {
    #     'web.assets_frontend': [
    #         # 'custom_vendor_dashboard/static/src/js/main.js',
    #     ],
    # },
    'assets': {
        'web.assets_frontend': [
            'custom_vendor_dashboard/static/src/css/main.css',
            'custom_vendor_dashboard/static/src/css/style.css',

        ],
    },
}