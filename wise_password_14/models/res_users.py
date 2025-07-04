from datetime import date, datetime, timedelta
from passlib.utils.binary import ab64_decode
from odoo import api, fields, models, _, SUPERUSER_ID
from odoo.exceptions import UserError, AccessDenied
from odoo.addons.auth_signup.models.res_partner import SignupError, now
from ..exceptions import ExpiredPassword
import logging

_logger = logging.getLogger(__name__)

class ResUsers(models.Model):
    _inherit = 'res.users'

    date_password_changed = fields.Datetime(string='The datetime the password was last modified', copy=False)
    old_passwords = fields.One2many(string='Old Passwords', comodel_name='wise_password_14.old_passwords',
        inverse_name='user_id', copy=False)

    '''
    (Overridden) Before setting the password, make sure that it:
        1. Meets the password requirements(minimum length, upper,lower, etc)
        2. Is not one of the user's old passwords if the setting is enabled
    '''
    def _set_password(self):
        for rec in self:            
            rec._check_password_reqs(rec.password)
            rec._check_password_history()
            '''
            Need to call super() before we call _limit_password_history(). 
            This is because unlink is called inside update_password_history,
            and that clears the cache, which means that the password fields in
            res.users will be cleared and won't be able to be stored after
            '''
            super(ResUsers, rec)._set_password()
            rec._limit_password_history()
            rec.date_password_changed = datetime.now()

    '''
    (Overridden) Check that the user's password has not expired yet. If it has,
    redirect them to the set_password endpoint
    '''
    @classmethod
    def _login(cls, db, login, password, user_agent_env):
        uid = super(ResUsers, cls)._login(db, login, password, user_agent_env)
        with cls.pool.cursor() as cr:
            self = api.Environment(cr, SUPERUSER_ID, {})[cls._name]
            num_days_till_reset = int(self.env['ir.config_parameter'].sudo().get_param('wise.pwd_num_days_till_reset', 0))
            user = self.browse([uid])
            if num_days_till_reset > 0 and isinstance(user.date_password_changed, datetime):
                if user.date_password_changed + timedelta(days=num_days_till_reset) < datetime.now():
                    raise ExpiredPassword('Your password has expired. ')
        return uid

    '''
    # (Overridden) This function is copied over to delay deleting the 
    # token until after we have written all of the changes to the user. This is 
    # so that we can throw appropriate errors for invalid passwords and still
    # have the user retry with the same token.
    # '''
    @api.model
    def signup(self, values, token=None):
        """ signup a user, to either:
            - create a new user (no token), or
            - create a user for a partner (with token, but no user for partner), or
            - change the password of a user (with token, and existing user).
            :param values: a dictionary with field values that are written on user
            :param token: signup token (optional)
            :return: (dbname, login, password) for the signed up user
        """
        if token:
            # signup with a token: find the corresponding partner id
            partner = self.env['res.partner']._signup_retrieve_partner(token, check_validity=True, raise_exception=True)
            # invalidate signup token
            # partner.write({'signup_token': False, 'signup_type': False, 'signup_expiration': False})

            partner_user = partner.user_ids and partner.user_ids[0] or False

            # avoid overwriting existing (presumably correct) values with geolocation data
            if partner.country_id or partner.zip or partner.city:
                values.pop('city', None)
                values.pop('country_id', None)
            if partner.lang:
                values.pop('lang', None)

            if partner_user:
                # user exists, modify it according to values
                values.pop('login', None)
                values.pop('name', None)
                partner_user.write(values)
                if not partner_user.login_date:
                    partner_user._notify_inviter()
                ##### invalidate signup token
                partner.write({'signup_token': False, 'signup_type': False, 'signup_expiration': False})
                return (partner_user.login, values.get('password'))
            else:
                # user does not exist: sign up invited user
                values.update({
                    'name': partner.name,
                    'partner_id': partner.id,
                    'email': values.get('email') or values.get('login'),
                })
                if partner.company_id:
                    values['company_id'] = partner.company_id.id
                    values['company_ids'] = [(6, 0, [partner.company_id.id])]
                partner_user = self._signup_create_user(values)
                partner_user._notify_inviter()
                ###### invalidate signup token
                partner.write({'signup_token': False, 'signup_type': False, 'signup_expiration': False})
        else:
            # no token, sign up an external user
            values['email'] = values.get('email') or values.get('login')
            self._signup_create_user(values)

        return (values.get('login'), values.get('password'))


    '''
    (Overridden) Only send an email if the admin has already created an
    initial password for the user. A new signup email template was also created
    and signup_type can now also have the value of 'set', which means a new
    user still hasn't created their own password.
    '''
    def action_reset_password(self):
        self.ensure_one()
        if not self.date_password_changed:
            _logger.info('Admin has not yet created a password for new user, not sending email')
            return

        """ create signup token for each user, and send their signup url by email """
        create_mode = bool(self.env.context.get('create_user'))
        template = None
        signup_type = None
        email_template = None
        if create_mode:
            signup_type = 'set'
            email_template = 'wise_password_14.set_password_email'
        else:
            signup_type = 'reset'
            email_template = 'auth_signup.reset_password_email'

        template = self.env.ref(email_template, raise_if_not_found=False)
        if not template:
            _logger.warn(_('The proper email template could not be found'))

        ''' no time limit for initial invitation, only for reset password '''
        expiration = False if create_mode else now(days=+1)
        odoo_bot = self.env.ref('base.user_root')

        self.mapped('partner_id').signup_prepare(signup_type=signup_type, expiration=expiration)

        email_values = {
            'email_cc': False,
            'auto_delete': True,
            'message_type': 'user_notification',
            'recipient_ids': [],
            'partner_ids': [],
            'scheduled_date': False,
            'email_from': odoo_bot.email,
        }
        assert template._name == 'mail.template'

        for user in self:
            if not user.email:
                raise UserError(_("Cannot send email: user %s has no email address.", user.name))
            email_values['email_to'] = user.email
            # TDE FIXME: make this template technical (qweb)
            with self.env.cr.savepoint():
                force_send = not(self.env.context.get('import_file', False))
                template.send_mail(user.id, force_send=force_send, raise_exception=True, email_values=email_values)
            _logger.info("Password reset email sent for user <%s> to <%s>", user.login, user.email)

    '''
    (New) This button opens the wizard change password wizard with the context
    set to create a new user properly
    '''
    def button_set_initial_password(self):
        self.ensure_one()
        return {
            'name': _('Create Initial Password'),
            'view_mode': 'form',
            'type': 'ir.actions.act_window',
            'res_model': 'change.password.wizard',
            'context': {'create_user': True},
            'target': 'new',
        }

    '''
    (New) Sends an email to all users whose password is expiring within the n 
    days, where n = number of days till reminder (found in the User Password 
    Section in settings). Will be called from an automated action scheduled to 
    run daily
    '''
    @api.model
    def remind_expiring_passwords(self):
        days_till_reminder = int(self.env['ir.config_parameter'].sudo().get_param('wise.pwd_num_days_till_reminder', 0))
        days_till_reset = int(self.env['ir.config_parameter'].sudo().get_param('wise.pwd_num_days_till_reset', 0))
        days_till_email = days_till_reset - days_till_reminder
        if days_till_reminder == 0 or days_till_reset == 0:
            return

        for user in self.search([]):
            expiration_date = user.date_password_changed + timedelta(days=days_till_reset)            
            if user.date_password_changed + timedelta(days=days_till_email) <= datetime.now():
                _logger.info(_(f'{user.name}\'s password is expiring soon. Sending email to remind them to change it'))
                user.partner_id.signup_prepare(signup_type='expired_pwd', expiration=False)
                email_template = 'wise_password_14.expire_password_reminder_email'
                template = self.env.ref(email_template, raise_if_not_found=False)
                if not template:
                    _logger.warn(_('The proper email template could not be found'))

                assert template._name == 'mail.template'
                odoo_bot = self.env.ref('base.user_root')

                email_values = {
                    'email_from': odoo_bot.email,
                    'email_cc': False,
                    'auto_delete': True,
                    'scheduled_date': False,
                    'recipient_ids': [],
                    'partner_ids': [],
                }
                
                if not user.email:
                    raise UserError(_(f'Cannot send email: user {user.name} has no email address.'))
                email_values['email_to'] = user.email
                with self.env.cr.savepoint():
                    expiration_date = expiration_date.strftime('%B %d, %Y at %I:%M %p')
                    force_send = not(self.env.context.get('import_file', False))
                    template.with_context(lang=user.lang, expiration_date=expiration_date).send_mail(user.id, force_send=force_send, raise_exception=True, email_values=email_values)

    '''
    (Helper) Checks that the password meets the requirements of the current db.
    If they don't, throws a UserError
    '''
    def _check_password_reqs(self, password):
        self.ensure_one()
        min_len = self.env['ir.config_parameter'].sudo().get_param('wise.pwd_min_len')
        include_num = self.env['ir.config_parameter'].sudo().get_param('wise.pwd_include_num')
        include_upper = self.env['ir.config_parameter'].sudo().get_param('wise.pwd_include_upper')
        include_lower = self.env['ir.config_parameter'].sudo().get_param('wise.pwd_include_lower')
        include_special = self.env['ir.config_parameter'].sudo().get_param('wise.pwd_include_special')

        errs = []
        if min_len and len(password) < int(min_len):
            errs.append(f'una longitud mayor que {min_len} caracteres')
        if include_num and not any(char.isdigit() for char in password):
            errs.append('un número')
        if include_upper and not any(char.isupper() for char in password):
            errs.append('una mayúscula')
        if include_lower and not any(char.islower() for char in password):
            errs.append('una minúscula')
        if include_special and all(char.isalnum() or char.isspace() for char in password):
            errs.append('un cáracter especial (!”#$%&/)')
        '''
        Since exceptions can't format new lines, 
        make the errors into a sentence
        '''
        if len(errs):
            msg = 'La contraseña debe tener '
            if len(errs) == 1:
                msg += errs[0]
            else:
                for i in errs[:-1]:
                    msg += i + ', '
                msg += f'y {errs[-1]}.'
            raise UserError(_(msg))

    '''
    (Helper) Checks that the new password isn't the same as the previous stored
    passwords
    '''
    def _check_password_history(self):
        for pwd in self._get_password_history():
            ctx = self._crypt_context()
            __, alg, rounds, salt, hash = pwd.split('$')
            new_pwd = ctx.hash(self.password, salt=ab64_decode(salt), rounds=int(rounds))
            __, new_alg, new_rounds, new_salt, new_hash = new_pwd.split('$')
            if alg != new_alg:
                _logger.warn('New hashing algorithm detected. Will not be able to correctly verify \
                    that passwords are not the same as old passwords')
            if hash == new_hash:
                raise UserError(_('Cannot reuse old passwords'))

    '''
    (Helper) Adds the current password to old_paswords and then returns up to n 
    old_passwords (n=num_pwds_stored)
    '''
    def _get_password_history(self):
        self.ensure_one()
        num_pwds_stored = int(self.env['ir.config_parameter'].sudo().get_param('wise.pwd_num_stored'))
        self.env.cr.execute(f'SELECT password, date_password_changed FROM res_users WHERE id={self.id}')
        cur_pwd, date_changed = self.env.cr.fetchone()
        if not cur_pwd:
            return []
        self.old_passwords.create({
            'user_id': self.id,
            'date_changed': date_changed,
            'password': cur_pwd
        })
        return self.old_passwords.sorted('date_changed', reverse=True).mapped('password')[:num_pwds_stored]

    '''
    (Helper) This function ensures that the number of passwords is at most
    equal to the password history limit (That is set in the settings)
    '''
    def _limit_password_history(self):
        self.ensure_one()
        num_pwds_stored = int(self.env['ir.config_parameter'].sudo().get_param('wise.pwd_num_stored'))
        pwds_to_keep = self.old_passwords.sorted('date_changed', reverse=True)[:num_pwds_stored -1]
        pwds_to_delete = self.old_passwords - pwds_to_keep
        pwds_to_delete.unlink()
class ChangePasswordUser(models.TransientModel):
    _inherit = 'change.password.user'

    '''
    (Overridden) Changed function so that if it is called with context with 
    create_user=True, it will run user_id.action_reset_password() which just 
    sends the invitation email to the new user. It also ensures that the 
    password will be deleted in the event of an exception being thrown
    '''
    def change_password_button(self):
        try:
            for rec in self:
                if not rec.new_passwd:
                    raise UserError(_("Before clicking on 'Change Password', you have to write a new password."))
                rec.user_id.write({'password': rec.new_passwd})
                if self.env.context.get('create_user'):
                    rec.user_id.with_context(password=rec.new_passwd).action_reset_password()
        finally:
            '''
            Regardless of there is an exception or not, delete the new password
            from the transient model. To do so, we need to get new cursor since
            odoo will rollback when an exception is thrown and undo deleting 
            the pwd
            '''
            with self.pool.cursor() as cr:
                for l in self:
                    cr.execute(f"UPDATE change_password_user SET new_passwd='' WHERE id={l.id}")