# -*- coding: utf-8 -*-

import binascii

from odoo import fields, http, _
from odoo.addons.sale.controllers import portal as sale_portal
from odoo.http import request
from odoo.exceptions import AccessError, MissingError, ValidationError
from odoo.addons.portal.controllers.mail import _message_post_helper


class CustomerPortal(sale_portal.CustomerPortal):

    @http.route(['/my/orders/<int:order_id>'], type='http', auth="public", website=True)
    def portal_order_page(
            self,
            order_id,
            report_type=None,
            access_token=None,
            message=False,
            download=False,
            downpayment=None,
            **kw
    ):
        try:
            order_sudo = self._document_check_access('sale.order', order_id, access_token=access_token)
        except (AccessError, MissingError):
            return request.redirect('/my')

        if report_type in ('html', 'pdf', 'text') or 'report' in kw:
            report_template = request.env['ir.ui.view'].sudo().search([('key', '=', 'sale.report_saleorder_raw_copy_1')])
            report_ref = 'sale.action_report_saleorder'
            if kw.get('report') == 'purchase_agreement':
                report_ref = 'solt_quarry_door_sale.action_report_sale_purchase_agreement'
                order_sudo.write({'is_agreement_doc_download': True})
            elif report_template.exists():
                report_ref = 'sale.report_saleorder_raw_copy_1'
                order_sudo.write({'is_detail_doc_download': True})

            return self._show_report(
                model=order_sudo,
                report_type=report_type,
                report_ref=report_ref,
                download=download,
            )

        return super(CustomerPortal, self).portal_order_page(order_id,
            report_type=report_type,
            access_token=access_token,
            message=message,
            download=download,
            downpayment=downpayment,
            **kw)

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
        if not order_sudo.is_detail_doc_download:
            return {'error': _('The Detail estimate document has not been read.')}
        if not order_sudo.is_agreement_doc_download:
            return {'error': _('The Purchase Agreement document has not been read.')}
        if not signature:
            return {'error': _('Signature is missing.')}

        try:
            order_sudo.write({
                'signed_by': name,
                'signed_on': fields.Datetime.now(),
                'signature': signature,
            })
            request.env.cr.commit()
        except (TypeError, binascii.Error) as e:
            return {'error': _('Invalid signature data.')}

        if not order_sudo._has_to_be_paid():
            order_sudo.action_confirm()
            order_sudo._send_order_confirmation_mail()

        report_template = request.env['ir.ui.view'].search([('key', '=', 'sale.report_saleorder_raw_copy_1')])
        report_ref = 'sale.action_report_saleorder'
        if report_template.exists():
            report_ref = 'sale.report_saleorder_raw_copy_1'

        pdf = request.env['ir.actions.report'].sudo()._render_qweb_pdf(report_ref, [order_sudo.id])[
            0]

        _message_post_helper(
            'sale.order',
            order_sudo.id,
            _('Order signed by %s', name),
            attachments=[('%s.pdf' % order_sudo.name, pdf)],
            token=access_token,
        )

        query_string = '&message=sign_ok'
        if order_sudo._has_to_be_paid():
            query_string += '#allow_payment=yes'
        return {
            'force_refresh': True,
            'redirect_url': order_sudo.get_portal_url(query_string=query_string),
        }