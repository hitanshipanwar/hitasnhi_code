# -*- coding: utf-8 -*-
##############################################################################
#                                                                            #
# Part of WMSSOFT. (Website: www.wmssoft.com.au).                            #
# See LICENSE file for full copyright and licensing details.                 #
#                                                                            #
##############################################################################

{
    'name': 'WMSSoft: Delete Duplicate Pricelist Items',
    'version': '0.0.1',
    'license': 'OPL-1',
    'sequence': 1,
    'category': 'Sales',
    'summary': 'This module used to Delete Duplicate and zero priced Pricelist Items',
    "author": "wmssoft: Dhaval",
    'company': 'WMSSoft Pty Ltd',
    'maintainer': 'WMSSoft Pty Ltd',
    'website': "https://www.wmssoft.com.au/",
    'depends': ['product'],
    'data': [
        'views/remove_price_rule.xml'
        ],
    'installable': True,
    'auto_install': False,
    'application': True,
}
