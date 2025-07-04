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
    "name"          : 'O2b Base',
    "version"       : "17.0.0.1",
    "author"        : "O2b Technologies Pvt. Ltd.",
    "contributors"  : ['O2b Technologies <info@o2b.co.in>'],
    "category"      : "mail",
    "website"       :'https://www.o2btechnologies.com',
    "description"   : """This module for Client Side""",
    "summary"       :"""This module for Client Side""",
    "depends"       : ['base', 'mail'],
    "data"          : [
                      'security/ir.model.access.csv',
                      'views/views.xml',
                      # 'data/ir_cron.xml',
                      ],
    "installable"   : True,
    "auto_install"  : False,
    "license"       : "OPL-1",
    "price"         : 213,
    "currency"      : "EUR",
}
