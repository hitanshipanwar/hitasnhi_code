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

from . import const

def get_base_url(type):
    """ Return the base url for Sezzle.

    :param str type: "sandbox" or "production".
    :return: The Base Url
    :rtype: str
    """
    return const.BASE_URL_DEV if type == 'sandbox' else const.BASE_URL_PROD

def get_api_version():
    """ Return the api version for Sezzle.

    :return: API_VERSION
    :rtype: str
    """
    return const.API_VERSION