from odoo import fields, http, SUPERUSER_ID, _
from odoo.exceptions import AccessError, MissingError, ValidationError
from odoo.http import request
from odoo.addons.portal.controllers import portal
from odoo.addons.website.controllers.main import Website
from odoo.http import content_disposition, Controller, request, route
from odoo.addons.portal.controllers.mail import _message_post_helper
from odoo.addons.portal.controllers import portal
from odoo.addons.portal.controllers.portal import pager as portal_pager, get_records_pager
import base64
import binascii

class CRMDesignconllroller(http.Controller):
    @http.route('/get_minutes', type='json', auth='public', website=True, sitemap=False)
    def get_mins(self, **kwargs):
        params = request.env["ir.config_parameter"].sudo()
        inactive_session_time_out_delay = int(params.get_param('auth_session_timeout.inactive_session_time_out_delay'))
        return inactive_session_time_out_delay

class MyCustomerPortal(portal.CustomerPortal):

    @http.route(['/approve/design/'], type='json', auth="public", website=True)
    def approve_design(self, order_id, access_token=None,name=None, signature=None):
        order = request.env['sale.order'].with_user(SUPERUSER_ID).search([('id','=',sale_order_id)])        

        for design in order.attachment_ids:
            if design.id == design_id:
                design.is_approved = True
                design.is_rejected = False
                design.approve_state = 'approve'
                design.comment = comment
                
                if not design.is_final_design:
                    order.state = 'design_confirm'

        return True

    @http.route(['/reject/design'], type='json', auth="public", website=True)
    def reject_design(self,sale_order_id,design_id,comment):
        order = request.env['sale.order'].with_user(SUPERUSER_ID).search([('id','=',sale_order_id)])
        
        for design in order.attachment_ids:
            if design.id == design_id:
                design.is_rejected = True
                design.is_approved = False
                design.comment = comment

                design.approve_state = 'rejected'

        return True


    @http.route(['/my/orders/<int:order_id>/approve'], type='json', auth="public", website=True)
    def portal_design_accept(self, order_id, access_token=None, design_id=None,name=None, signature=None):
        access_token = access_token or request.httprequest.args.get('access_token')
        try:
            order_sudo = self._document_check_access('sale.order', order_id, access_token=access_token)
        except (AccessError, MissingError):
            return {'error': _('Invalid order.')}

        if not signature:
            return {'error': _('Signature is missing.')}

        for design in order_sudo.attachment_ids:
            if design.id == int(design_id):
                design.is_approved = True
                design.is_rejected = False
                design.approve_state = 'approve'
                # design.comment = comment
                design.customer_signature = signature
                
                if not design.is_final_design:
                    order_sudo.state = 'design_confirm'

        base_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
        base_url += order_sudo.get_portal_url()
        email_from = request.env['ir.mail_server'].sudo().search([],limit=1)
        mail_values_user_check = {
            'subject': "Design Confirmed By %s" % (order_sudo.partner_id.name),
            'email_to':order_sudo.user_id.partner_id.email,
            'email_from':email_from.smtp_user,
            'body_html': '''<div> Dear, %s, <br/>
                                %s has Confirmed design. <br/>
                                Reference %s
                            </div>'''%(order_sudo.user_id.partner_id.name,order_sudo.partner_id.name,base_url)

            }
        create_and_send_email = request.env['mail.mail'].sudo().create(mail_values_user_check).sudo().send()
        base_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
        base_url += "/my/kitchen/design/%s"%(order_sudo.id)
        return {
            'force_refresh': True,
            'redirect_url': base_url,
        }
    

    @http.route(['/my/orders/<int:order_id>/reject_design'], type='json', auth="public", website=True)
    def portal_design_reject(self, order_id, access_token=None, design_id=None,name=None, signature=None, comment=''):
        access_token = access_token or request.httprequest.args.get('access_token')
        try:
            order_sudo = self._document_check_access('sale.order', order_id, access_token=access_token)
        except (AccessError, MissingError):
            return {'error': _('Invalid order.')}

        if not signature:
            return {'error': _('Signature is missing.')}


        if access_token:
            if request.env.user._is_public():
                # TODO : After adding the pid and sign_token in access_url when send invoice by email, remove this line
                # TODO : Author must be Public User (to rename to 'Anonymous')
                author_id = order_sudo.partner_id.id if hasattr(order_sudo, 'partner_id') and order_sudo.partner_id.id else request.env.user.partner_id.id
            else:
                author_id = request.env.user.partner_id.id
        else:
            author_id = request.env.user.partner_id.id
            
        for design in order_sudo.attachment_ids:
            if design.id == int(design_id):
                # design.is_rejected = True
                # design.is_approved = False
                design.comment = comment
                design.customer_signature = signature

                design.approve_state = 'rejected'
        order_sudo.with_user(SUPERUSER_ID).message_post(body=comment,author_id=author_id,message_type='comment',subtype_xmlid="mail.mt_comment")

        base_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
        base_url += order_sudo.get_portal_url()
        email_from = request.env['ir.mail_server'].sudo().search([],limit=1)
        mail_values_user_check = {
            'subject': "Design rejected By %s" % (order_sudo.partner_id.name),
            'email_to':order_sudo.user_id.partner_id.email,
            'email_from':email_from.smtp_user,
            'body_html': '''<div> Dear, %s, <br/>
                                %s has Rejected design. <br/>
                                Reference %s
                            </div>'''%(order_sudo.user_id.partner_id.name,order_sudo.partner_id.name,base_url)

            }
        lines = order_sudo.attachment_ids.filtered(lambda l: l.approve_state == 'approve')
        if not lines:
            order_sudo.write({
                'state':'draft'
                })
        create_and_send_email = request.env['mail.mail'].sudo().create(mail_values_user_check).sudo().send()
    
        base_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
        base_url += "/my/kitchen/design/%s"%(order_sudo.id)
        return {
            'force_refresh': True,
            'redirect_url': base_url,
        }


    # Invoice Confirmation From Customer
    @http.route(['/my/invoices/<int:invoice_id>/confirm'], type='json', auth="public", website=True)
    def portal_my_invoice_confirm(self, invoice_id, access_token=None, **kw):
        access_token = access_token or request.httprequest.args.get('access_token')
        try:
            invoice_sudo = self._document_check_access('account.move', invoice_id, access_token)
        except (AccessError, MissingError):
            return request.redirect('/my')

        quotation_approval_group_id = request.env.ref('crm_design.group_manager_quotation').with_user(SUPERUSER_ID).id
        quotation_manager_ids = request.env['res.users'].sudo().search([('groups_id','=',quotation_approval_group_id)])
        base_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
        base_url += invoice_sudo.with_user(SUPERUSER_ID).get_portal_url()
        for manager in quotation_manager_ids:
            email_from = request.env['ir.mail_server'].sudo().search([],limit=1)
            mail_values_user_check = {
                'subject': 'Invoice Confirmed By %s' % (invoice_sudo.partner_id.name),
                'email_to': manager.partner_id.email,
                'email_cc': invoice_sudo.invoice_user_id.partner_id.email,
                'email_from': email_from.smtp_user,
                'body_html': '''<div> Invoice %s is Confirmed by the  %s <br/>
                                Reference :-  %s
                                </div>'''%(invoice_sudo.name,invoice_sudo.partner_id.name,base_url)
                }
            create_and_send_email = request.env['mail.mail'].sudo().create(mail_values_user_check).sudo().send()
            invoice_sudo.write({
                'manager_name': kw.get('name') if kw else request.env.user.name,
                'manager_signed_on': fields.Datetime.now(),
                'manager_signature': kw.get('signature') or False,
                'confirmed_by_customer':True
            })
            # invoice_sudo.confirmed_by_customer = True

            # invoice_sudo.with_user(SUPERUSER_ID).action_post()

        return {
            'force_refresh': True,
            'redirect_url': invoice_sudo.get_portal_url(),
        }

    # Quotation Confirm From Customer
    @http.route(['/my/orders/<int:order_id>/accept'], type='json', auth="public", website=True)
    def portal_quote_accept(self, order_id, access_token=None, name=None, signature=None):
        # get from query string if not on json param
        access_token = access_token or request.httprequest.args.get('access_token')
        try:
            order_sudo = self._document_check_access('sale.order', order_id, access_token=access_token)
        except (AccessError, MissingError):
            return {'error': _('Invalid order.')}

        if not order_sudo._has_to_be_signed():
            return {'error': _('The order is not in a state requiring customer signature.')}
        if not signature:
            return {'error': _('Signature is missing.')}

        try:
            order_sudo.write({
                'signed_by': name,
                'signed_on': fields.Datetime.now(),
                'signature': signature,
                'confirmed_by_customer':True
            })
            request.env.cr.commit()
        except (TypeError, binascii.Error) as e:
            return {'error': _('Invalid signature data.')}

        if not order_sudo._has_to_be_paid():
            order_sudo.action_confirm()
            if order_sudo.opportunity_id:
                order_sudo.opportunity_id.action_set_won()
            order_sudo._send_order_confirmation_mail()

        # pdf = request.env.ref('sale.action_report_saleorder').with_user(SUPERUSER_ID)._render_qweb_pdf([order_sudo.id])[0]

        # _message_post_helper(
        #     'sale.order', order_sudo.id, _('Order signed by %s') % (name,),
        #     attachments=[('%s.pdf' % order_sudo.name, pdf)],
        #     **({'token': access_token} if access_token else {}))

        # pdf = request.env['ir.actions.report'].sudo()._render_qweb_pdf('sale.action_report_saleorder', [order_sudo.id])[0]

        # _message_post_helper(
        #     'sale.order',
        #     order_sudo.id,
        #     _('Order signed by %s', name),
        #     attachments=[('%s.pdf' % order_sudo.name, pdf)],
        #     token=access_token,
        # )


        query_string = '&message=sign_ok'
        if order_sudo._has_to_be_paid(True):
            query_string += '#allow_payment=yes'
        
        base_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
        base_url += order_sudo.get_portal_url()
        email_from = request.env['ir.mail_server'].sudo().search([],limit=1)
        mail_values_user_check = {
            'subject': "Quaotation Confirmed By %s" % (order_sudo.partner_id.name),
            'email_to':order_sudo.user_id.partner_id.email,
            'email_from':email_from.smtp_user,
            'body_html': '''<div> Dear, %s, <br/>
                                Quotation %s is confirmed by %s. <br/>
                                Reference %s
                            </div>'''%(order_sudo.user_id.partner_id.name,order_sudo.name,order_sudo.partner_id.name,base_url)

            }
        create_and_send_email = request.env['mail.mail'].sudo().create(mail_values_user_check).sudo().send()

        return {
            'force_refresh': True,
            'redirect_url': order_sudo.get_portal_url(query_string=query_string),
        }

    # Upload Payment Slip from Portal
    @http.route(['/my/invoices/<int:invoice_id>/upload_slip'], type='http',  methods=['POST'], auth="public", website=True)
    def portal_my_invoice_upload_slip(self, invoice_id, access_token=None, **post):
        try:
            invoice_sudo = self._document_check_access('account.move', invoice_id, access_token)
        except (AccessError, MissingError):
            return request.redirect('/my')
        query_string = '&access_token=%s' % (invoice_sudo.access_token)
        
        name = post.get('myslip').filename
        file = post.get('myslip')
        Attachments = request.env['ir.attachment']


        IrAttachment = request.env['ir.attachment']
        access_token = False

        # Avoid using sudo or creating access_token when not necessary: internal
        # users can create attachments, as opposed to public and portal users.
        if not request.env.user.has_group('base.group_user'):
            IrAttachment = IrAttachment.sudo().with_context(binary_field_real_user=IrAttachment.env.user)
            access_token = IrAttachment._generate_access_token()

        # At this point the related message does not exist yet, so we assign
        # those specific res_model and res_is. They will be correctly set
        # when the message is created: see `portal_chatter_post`,
        # or garbage collected otherwise: see  `_garbage_collect_attachments`.
        attachment_id = IrAttachment.create({
            'name': name,
            'datas': base64.b64encode(file.read()),
            'res_model': invoice_sudo._name,
            'res_id': invoice_sudo.id,
            'access_token': access_token,
        })

        myslip = request.httprequest.files.getlist('myslip')
        for file in myslip:
            payslip_list = []
            if file.filename:
                myslip_attchment = (0,0,{
                    'name': file.filename,
                    'datas': base64.encodebytes(file.read()),
                    })
                payslip_list.append(myslip_attchment)
            invoice_sudo.sudo().write({'payslip_multi_attachments':payslip_list})               


        if access_token:
            if request.env.user._is_public():
                # TODO : After adding the pid and sign_token in access_url when send invoice by email, remove this line
                # TODO : Author must be Public User (to rename to 'Anonymous')
                author_id = invoice_sudo.partner_id.id if hasattr(invoice_sudo, 'partner_id') and invoice_sudo.partner_id.id else request.env.user.partner_id.id
            else:
                author_id = request.env.user.partner_id.id
        else:
            author_id = request.env.user.partner_id.id

        invoice_sudo.with_user(SUPERUSER_ID).message_post(body="Payment Slip",attachment_ids=[attachment_id.id],author_id=author_id,message_type='comment',subtype_xmlid="mail.mt_comment")
        invoice_sudo.paymentslip_uploaded = True
        return request.redirect(invoice_sudo.get_portal_url(query_string=query_string))


    @http.route(['/my/orders/<int:order_id>/decline'], type='json', auth="public", methods=['POST'], website=True)
    def decline(self, order_id, access_token=None, name=None, signature=None, comment=''):
        access_token = access_token or request.httprequest.args.get('access_token')
        try:
            order_sudo = self._document_check_access('sale.order', order_id, access_token=access_token)
        except (AccessError, MissingError):
            return {'error': _('Invalid order.')}

        if not order_sudo._has_to_be_signed():
            return {'error': _('The order is not in a state requiring customer signature.')}
        if not signature:
            return {'error': _('Signature is missing.')}

        # query_string = '&message=sign_ok'
        # if order_sudo._has_to_be_paid(True):
        #     query_string += '#allow_payment=yes'
        if access_token:
            if request.env.user._is_public():
                # TODO : After adding the pid and sign_token in access_url when send invoice by email, remove this line
                # TODO : Author must be Public User (to rename to 'Anonymous')
                author_id = order_sudo.partner_id.id if hasattr(order_sudo, 'partner_id') and order_sudo.partner_id.id else request.env.user.partner_id.id
            else:
                author_id = request.env.user.partner_id.id
        else:
            author_id = request.env.user.partner_id.id

        query_string = False
        if order_sudo._has_to_be_signed():
            order_sudo._action_cancel()
        else:
            query_string = "&message=cant_reject"

        try:
            order_sudo.write({
                'signed_by': name,
                'signed_on': fields.Datetime.now(),
                'signature': signature,
                'confirmed_by_customer':True
            })
            order_sudo.with_user(SUPERUSER_ID).message_post(body=comment,author_id=author_id,message_type='comment',subtype_xmlid="mail.mt_comment")
            request.env.cr.commit()
        except (TypeError, binascii.Error) as e:
            return {'error': _('Invalid signature data.')}

        return {
            'force_refresh': True,
            'redirect_url': order_sudo.get_portal_url(query_string=query_string),
            }
        