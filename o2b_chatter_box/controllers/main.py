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
from odoo import http
from datetime import datetime
from odoo.http import content_disposition, dispatch_rpc, request, serialize_exception as _serialize_exception


class Session(http.Controller):

	@http.route('/web/session/logout', type='http', auth="none")
	def logout(self, redirect='/web'):
		user_id = request.env["res.users"].sudo().search(
			[("id", "=", request.session.context.get("uid"))])
		if user_id and request.session:
			user_id.with_user(user_id.id).sudo().write({
				'is_login_custom':False})
		request.session.logout(keep_db=True)
		return request.redirect(redirect, 303)
