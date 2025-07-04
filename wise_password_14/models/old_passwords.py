import passlib.context
from odoo import api, fields, models, _


'''
This model stores the hashed versions of users' old passwords to compare
against new passwords and ensure that users aren't reusing old passwords
'''
class OldPasswords(models.Model):
    _name = 'wise_password_14.old_passwords'
    _description = 'Previous encrypted passwords to be compared to the users\' new password'

    user_id = fields.Many2one(string='User', comodel_name='res.users', ondelete='cascade')
    date_changed = fields.Datetime(string='Date Password Changed')
    password = fields.Char(string='Previous Password', invisible=True, copy=False)