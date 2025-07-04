# -*- coding: utf-8 -*-
import werkzeug
import logging
from ..exceptions import ExpiredPassword
from odoo import http, _
from odoo.http import request
from odoo.addons.web.controllers.main import ensure_db
from odoo.exceptions import UserError, AccessDenied
from odoo.addons.auth_signup.models.res_users import SignupError
from odoo.addons.auth_signup.controllers.main import AuthSignupHome


_logger = logging.getLogger(__name__)

class WiseSolAuth(AuthSignupHome):
    '''
    (New) This route is for new users who still haven't set their password. To
    set a password, they also would need to enter the password that the admin
    has initially set for their account.
    '''
    @http.route('/web/set_password', type='http', auth='public', website=True, sitemap=False)
    def web_auth_set_password(self, *args, **kw):
        qcontext = self.get_auth_signup_qcontext()
        if not qcontext.get('token'):
            raise werkzeug.exceptions.NotFound()
        if 'error' not in qcontext and request.httprequest.method == 'POST':
            try:
                self._get_and_validate_user(request)
                self.do_signup(qcontext)
                return self.web_login(*args, **kw)
            except UserError as e:
                qcontext['error'] = e.name or e.value
            except SignupError:
                qcontext['error'] = _('Could not reset your password')
            except AccessDenied as e:
                qcontext['error'] = _('Invalid Initial Password')
            except Exception as e:
                qcontext['error'] = str(_(e))
        response = request.render('wise_password_14.set_password', qcontext)
        response.headers['X-Frame-Options'] = 'DENY'
        return response

    '''
    (New) This route is for users' whose passwords have expired. To renew their
    password they also need their old password
    '''
    @http.route('/web/renew_password', type='http', auth='public', website=True, sitemap=False)
    def web_auth_renew_password(self, *args, **kw):
        request.params['token'] = 'renew'
        if 'error' not in request.params and request.httprequest.method == 'POST':
            try:
                user = self._get_and_validate_user(request)
                user.password = request.params.get('password')
                ''' Commit changes to db so that web_login can have the new pwd'''
                request.env.cr.commit()
                return self.web_login(*args, **kw)
            except UserError as e:
                request.params['error'] = e.name or e.value
            except SignupError:
                request.params['error'] = _('Could not reset your password')
            except AccessDenied as e:
                request.params['error'] = _('Invalid Previous Password')
            except Exception as e:
                request.params['error'] = str(_(e))
        response = request.render('wise_password_14.renew_password', request.params)
        response.headers['X-Frame-Options'] = 'DENY'
        return response

    '''
    (Inherritted) If the user's password has expired, redirect them to the 
    set_password route and pass the signup_token as a parameter as well. 
    '''
    @http.route()
    def web_login(self, *args, **kw):
        ensure_db()
        try:
            response = super(WiseSolAuth, self).web_login(*args, **kw)
        except ExpiredPassword:
            request.params.pop('password')
            request.params.pop('login_success')
            return request.redirect_query('/web/renew_password',  query=request.params)
        return response

    '''
    (Helper) Validates that the proper previous password was given and that the
    new passwords match. Then returns the new user
    '''
    def _get_and_validate_user(self, request):
        login = request.params.get('login')
        prev_pwd = request.params.get('prev_password')
        new_pwd = request.params.get('password')
        confirm_pwd = request.params.get('confirm_password')
        
        if not login:
            raise Exception('Missing Login/Email')
        if new_pwd != confirm_pwd:
            raise Exception('New Passwords do not match')
        user = request.env['res.users'].sudo().search([('login', '=', login)], limit=1)
        if not user:
            raise Exception('Invalid Login/Email')
        ''' If invalid login, _check_credentials will raise AccessDenied  '''
        user.with_user(user)._check_credentials(prev_pwd, {'interactive': True})
        return user