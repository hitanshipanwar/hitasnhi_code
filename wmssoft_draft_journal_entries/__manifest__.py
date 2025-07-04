# -*- coding: utf-8 -*-
##############################################################################
#                                                                            #
# Part of WMSSOFT. (Website: www.wmssoft.com.au).                            #
# See LICENSE file for full copyright and licensing details.                 #
#                                                                            #
##############################################################################

{
    'name': 'WMSSoft: Draft Journal Entries',
    'version': '0.0.1',
    'license': 'OPL-1',
    'sequence': 1,
    'category': 'Sales',
    'summary': 'This module used to move post to draft entries',
    "author": "wmssoft: Dhaval",
    'company': 'WMSSoft Pty Ltd',
    'maintainer': 'WMSSoft Pty Ltd',
    'website': "https://www.wmssoft.com.au/",
    'depends': ['account'],
    'data': [
        'views/draft_journal_entries.xml'
        ],
    'installable': True,
    'auto_install': False,
    'application': True,
}
