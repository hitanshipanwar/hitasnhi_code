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
    'name'          : 'O2B Sezzle Integration',
    'summary'       : 'Integrate Sezzle with Odoo.',
    'description'   : 'Odoo - Sezzle integration module.',
    'version'       : '1.0',
    'author'        : 'O2b Technologies',
    'website'       : "https://www.o2btechnologies.com/",
    'category'      : 'Accounting',
    'license'       : 'OPL-1',
    'depends'       : ['base', 'account', 'account_accountant'],
    'data': [
        'security/ir.model.access.csv',
        'views/sezzle_views.xml',
        'data/sezzle_transaction_create_cron.xml',
        # 'wizards/import_sezzle_transactions_view.xml'
    ],
    'installable'   : True,
    'application'   : True,
}
