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
    "name"          : 'O2b Vendor Dashboard',
    "version"       : "1.0",
    "author"        : "O2b Technologies Pvt. Ltd.",
    "contributors"  : ['O2b Technologies <info@o2b.co.in>'],
    "category"      : "mail",
    "website"       :'https://www.o2btechnologies.com',
    "description"   : """This module will helps us to get the transctions from Client DB""",
    "summary"       :"""This module will helps us to get the transctions from Client DB""",
    "depends"       : ['base','purchase', 'account', 'payment'],
    "data"          : [
                      # 'views/res_config_settings.xml',
                      'views/session_expired.xml',
                      'views/login_template.xml',
                      'views/custom_view/payment_term.xml',
                      'views/login/otp_fill_email_template.xml',
                      'views/login/change_password_template.xml',
                      'views/login/login_template.xml',
                      'views/login/otp_fill_template.xml',
                      'views/login/trouble_signIn_template.xml',
                      'views/login/email_otp_send_button_template.xml',
                      'views/login/reset_password_template.xml',
                      'views/login/forget_password_template.xml',
                      'views/login/change_password_phone_otp_template.xml',
                      'views/login/reset_password_confirm_password.xml',
                      'views/search_template/not_found_template.xml',
                      'views/email_verification/email_submit_form.xml',
                      'views/email_verification/chech_email_form.xml',
                      'views/email_verification/email_verified_confirm_form.xml',
                      'views/phone_verification/phone_number_verification_and_confirm_form.xml',
                      'views/phone_verification/check_phone_form.xml',
                      'views/phone_verification/phone_no_submit_form.xml',
                      'views/setting/setting_template_manage_email.xml',
                      'views/setting/setting_template_manage_phone.xml',
                      'views/setting/setting_template_manage_profile.xml',
                      'views/setting/setting_template_manage_reset_password.xml',
                      'views/setting_template.xml',
                      ],
    "installable"   : True,
    "auto_install"  : False,
    "license"       : "OPL-1",
    "price"         : 213,
    "currency"      : "EUR",
}
