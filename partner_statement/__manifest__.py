# -*- coding: utf-8 -*-
##############################################################################
#                                                                            #
# Part of WMSSOFT. (Website: www.wmssoft.com.au).                            #
# See LICENSE file for full copyright and licensing details.                 #
#                                                                            #
##############################################################################

{
    "name": "Partner Statement",
    "version": "15.0.1.0.0",
    "category": "Accounting & Finance",
    "summary": "Financial Reports",
    "author": "wmssoft: Dhaval",
    "website": "https://www.wmssoft.com.au",
    "license": "AGPL-3",
    "depends": ["account", "account_followup", "contacts"],
    "external_dependencies": {"python": ["dateutil"]},
    "data": [
        "security/statement_security.xml",
        "security/ir.model.access.csv",
        "data/customer_statement_email_template.xml",
        "views/activity_statement.xml",
        "views/outstanding_statement.xml",
        # "views/assets.xml",
        "views/aging_buckets.xml",
        "views/res_config_settings.xml",
        "wizard/statement_wizard.xml",
    ],
    "installable": True,
    "application": False,
}
