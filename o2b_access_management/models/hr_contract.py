# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import AccessError

class HrContract(models.Model):
    _inherit = 'hr.contract'

    def _check_access_rights(self):
        """Restrict contract modifications for unauthorized users."""
        if self.env.user.has_group('o2b_access_management.group_hr_contract_user'):
            raise AccessError(_("You are not allowed to modify contracts."))

    @api.model
    def create(self, vals):
        """Restrict contract creation for unauthorized users."""
        self._check_access_rights()
        return super().create(vals)

    def write(self, vals):
        """Restrict contract editing for unauthorized users."""
        self._check_access_rights()
        return super().write(vals)

    def unlink(self):
        """Restrict contract deletion for unauthorized users."""
        self._check_access_rights()
        return super().unlink()



class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    def write(self, vals):
        """Restrict contract editing for unauthorized users."""
        if self.env.user.has_group('o2b_access_management.group_employee_own') and not 'tz' in vals:
            raise AccessError(_("You are not allowed to modify Employee."))
        return super().write(vals)

    def unlink(self):
        """Restrict deletion for employee. """
        if self.env.user.has_group('o2b_access_management.group_employee_own'):
            raise AccessError(_("You are not allowed to delete Employee."))
        return super(HrEmployee, self).unlink()


class User(models.Model):
    _inherit = 'res.users'

    employee_cars_count = fields.Integer(
        related='employee_id.employee_cars_count',
        groups=""
    )