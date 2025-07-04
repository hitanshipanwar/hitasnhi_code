# -*- coding: utf-8 -*-


from collections import defaultdict

from odoo import _, models
from odoo.exceptions import UserError
from odoo.addons.website.tools import text_from_html


def _prepare_data(env, data):
    # change product ids by actual product object to get access to fields in xml template
    # we needed to pass ids because reports only accepts native python types (int, float, strings, ...)
    layout_wizard = env['product.label.layout'].browse(data.get('layout_wizard'))
    received_date = False
    context = data.get('context')
    if data.get('active_model') == 'product.template':
        products = env['product.template'].with_context(display_default_code=False)
    elif data.get('active_model') == 'product.product':
        products = env['product.product'].with_context(display_default_code=False)
    else:
        raise UserError(_('Product model not defined, Please contact your administrator.'))

    if context.get('active_model') == 'stock.picking':
        stock_picking_id = env['stock.picking'].browse(context.get('active_id'))
        received_date = stock_picking_id.date_done.date() if stock_picking_id.date_done else False

    total = 0
    quantity_by_product = defaultdict(list)
    for p, q in data.get('quantity_by_product').items():
        product = products.browse(int(p))
        if product.is_product_variant:
            price = product.lst_price
        else:
            price = product.list_price
        taxes = product.taxes_id.compute_all(price, product.currency_id, product=product)
        included = taxes['total_included']
        price = str(round(included, 2)) + ' ' + str(product.currency_id.symbol)
        
        quantity_by_product[product].append((product.barcode, q, price))
        total += q
    if data.get('custom_barcodes'):
        # we expect custom barcodes format as: {product: [(barcode, qty_of_barcode)]}
        for product, barcodes_qtys in data.get('custom_barcodes').items():
            quantity_by_product[products.browse(int(product))] += (barcodes_qtys)
            total += sum(qty for _, qty in barcodes_qtys)
    if not layout_wizard:
        return {}

    return {
        'quantity': quantity_by_product,
        # 'rows': layout_wizard.rows,
        # 'columns': layout_wizard.columns,
        # 'page_numbers': (total - 1) // (layout_wizard.rows * layout_wizard.columns) + 1,
        'price_included': data.get('price_included'),
        'extra_html': text_from_html(layout_wizard.extra_html),
        'description': data.get('description'),
        'company_id' : env.company,
        'received_date' : received_date
    }


class ReportProductTemplateLabelShelfTalker(models.AbstractModel):
    _name = 'report.crm_design.report_shelf_talker'
    _description = 'Product Label Report'

    def _get_report_values(self, docids, data):
        return _prepare_data(self.env, data)