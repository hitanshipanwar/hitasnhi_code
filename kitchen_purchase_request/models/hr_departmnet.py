# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _

class Department(models.Model):
	_inherit = "hr.department"

	def write(self, vals):
		# Add Manager to Purchase Request Group Automatically
		if 'manager_id' in vals:
			manager_id = vals.get("manager_id")
			if manager_id:
				manager = self.env['hr.employee'].browse(manager_id)
				if manager.user_id:
					purchase_request_manager_group = self.env.ref('kitchen_purchase_request.group_purchase_request_manager', raise_if_not_found=False)
					if purchase_request_manager_group:
						purchase_request_manager_group.sudo().write({'users': [(4, manager.user_id.id)]})
					
		return super(Department, self).write(vals)