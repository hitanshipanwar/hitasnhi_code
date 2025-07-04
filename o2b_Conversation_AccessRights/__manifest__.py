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
    'name': 'O2B Conversation Access Rights',
    'summary': 'conversations access control',
    'description': 'Manage access control for conversations in the system',
    'author': 'O2b Technologies',
    'website': 'https://www.o2btechnologies.com',
    'category': 'Uncategorized',
    'version': '16.1',
    'license': 'OPL-1',
    'depends': [ 'mail'],
    'data': [
        'views/access_control_group.xml',
    ],

    "assets": {
    'web.assets_backend': [
        "/o2b_Conversation_AccessRights/static/src/views/messaging_menu.js",
        "/o2b_Conversation_AccessRights/static/src/views/messaging_menu.xml",
    ],
        
    }
}