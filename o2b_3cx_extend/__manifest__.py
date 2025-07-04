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
    'name'          : "3CX Extend",
    'summary'       : '3CX Extend',
    'license'       : 'OPL-1',
    'website'       : 'https://www.odoo.com',
    'version'       : '0.1',
    'author'        : 'O2B Technologies',
    'description'   : '3CX API Integration.',
    'depends'       : ['base', 'nalios_3cx_full', 'helpdesk'],
    'data'          : [
        # "security/ir.model.access.csv",
        "data/data.xml",
        "views/helpdesk_ticket.xml",
        "views/res_call_log.xml",
        "views/3cx_views.xml",
    ],
    
    'installable'   : True,
    'application'   : False,
}
