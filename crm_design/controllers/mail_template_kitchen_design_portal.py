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

class MyCustomerDesignPortal(portal.CustomerPortal):

    @http.route(['/my/kitchen/design', '/my/kitchen/design/<int:sale_order_id>'], type='http', auth="public", website=True)
    def portal_my_design(self, page=1, access_token=None, **kw):
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id
        SaleOrder = request.env['sale.order']
        sale_order_id=kw.get('sale_order_id',False)

        # domain = self._prepare_orders_domain(partner)

        # searchbar_sortings = self._get_sale_searchbar_sortings()

        # # default sortby order
        # if not sortby:
        #     sortby = 'date'
        # sort_order = searchbar_sortings[sortby]['order']

        # if date_begin and date_end:
        #     domain += [('create_date', '>', date_begin), ('create_date', '<=', date_end)]

        # # count for pager
        # order_count = SaleOrder.search_count(domain)
        # # pager
        # pager = portal_pager(
        #     url="/my/orders",
        #     url_args={'date_begin': date_begin, 'date_end': date_end, 'sortby': sortby},
        #     total=order_count,
        #     page=page,
        #     step=self._items_per_page
        # )
        # # content according to pager

        orders = SaleOrder.sudo().search([('id','=',sale_order_id)])
        # designs = request.env['sale.order'].with_user(SUPERUSER_ID).search([('id','=',sale_order_id)])
        
        # request.session['my_orders_history'] = orders.ids[:100]
        # values = {}
        values.update({
            # 'date': date_begin,
            'designs': orders.attachment_ids.sudo(),
            'page_name': 'Design',
            'sale_order': orders,
            # 'pager': pager,
            'default_url': '/my/designs',
            'action': orders._get_portal_return_action(),
            # 'searchbar_sortings': searchbar_sortings,
            # 'sortby': sortby,
        })  
        return request.render("crm_design.design_portal_template", values)
