# -*- coding: utf-8 -*-


from odoo import models, fields, api
from odoo.tools.float_utils import float_is_zero


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    show_button_update_price = fields.Boolean(compute="_compute_show_button_update_price")

    @api.depends(
        'order_id.sale_order_count',
        'product_id'
    )
    def _compute_show_button_update_price(self):
        for line in self:
            line.show_button_update_price = False
            if line.order_id.sale_order_count > 0 and line.product_id.product_spec_ok:
                line.show_button_update_price = True

    @api.model
    def _prepare_purchase_order_line_from_procurement(self, product_id, product_qty, product_uom, company_id, values,
                                                      po):
        res = super(PurchaseOrderLine, self)._prepare_purchase_order_line_from_procurement(product_id, product_qty, product_uom, company_id, values,
                                                      po)
        line_sale_specs_name = ''
        spec = self.env['specs.sale'].sudo()
        if values.get('product_description_variants'):
            line_sale_specs_name = values['product_description_variants']
            if line_sale_specs_name.startswith('\n'):
                line_sale_specs_name = line_sale_specs_name.split('\n')[1]
            spec = spec.search([('name', '=', line_sale_specs_name)])
        if line_sale_specs_name and product_id.name != line_sale_specs_name and len(line_sale_specs_name.split('/')) == 6:
            names = []
            for i, name in enumerate(line_sale_specs_name.split('/')):
                if i == 4 and not name:
                    names.append(product_id.name)
                else:
                    names.append(name)
            line_sale_specs_name = '/'.join(names)

            # split the name
            name = res['name'].split('\n')
            if name[-1] == values.get('product_description_variants'):
                res['name'] = '\n'.join(name[:-1]) + '\n' + line_sale_specs_name
        res['product_description_variants'] = line_sale_specs_name
        # si hay spec y tiene configurado glasses adicionar al nombre
        # if spec and spec.specs_glass_line_ids:
        #     glasses_info = spec._get_glasses_info()
        #     res['name'] = res['name'] + '\n' + "Glasses:" + '\n'.join(v for tinfo in glasses_info for k, v in tinfo.items())
        return res

    def action_update_line_cost_by_specs(self, sale_order_id):
        self.ensure_one()
        product_description_variants = self.product_description_variants
        if self.show_button_update_price and sale_order_id:
            sale_line_id = sale_order_id.order_line.filtered(lambda
                                                                 l: l.product_template_id == self.product_template_id and l.sale_specs_name == product_description_variants)
            specs_cost_total = sale_line_id.sale_specs_id.specs_cost_total
            sale_line_id.sale_specs_id.stage_id = self.env.ref("solt_quarry_door_sale.stage_sale_confirm", raise_if_not_found=False)
            if not float_is_zero(specs_cost_total, precision_rounding=self.currency_id.rounding):
                self.price_unit = sale_line_id.sale_specs_id.specs_cost_total

