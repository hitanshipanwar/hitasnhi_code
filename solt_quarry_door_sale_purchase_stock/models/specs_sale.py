# -*- coding: utf-8 -*-

from collections import defaultdict
from markupsafe import Markup
from odoo import api, models, _


class SpecsSale(models.Model):
    _inherit = 'specs.sale'

    def action_update_cost(self):
        self.ensure_one()
        # find and update the price unit the sale order line
        order_line_to_update_price = self.specs_sale_id.order_line.filtered(lambda l: l.sale_specs_id == self.id or l.sale_specs_name == self.name)
        order_line_to_update_price.write({'price_unit': self.specs_cost_total})

        # find the purchase order
        client_order_ref = self.specs_sale_id.client_order_ref
        purchase_order = self.env['purchase.order'].sudo().search([('name', '=', client_order_ref)])
        purchase_order_line_id = purchase_order.order_line.filtered(lambda l: l.product_description_variants == self.name)
        old_price_unit = purchase_order_line_id.price_unit
        purchase_order_line_id.sudo().write({'price_unit': self.specs_cost_total})

        # if specs_glass_line_ids find the PO for glasses
        po_dict = defaultdict(list)
        if self.specs_glass_line_ids:
            for glass in self.specs_glass_line_ids:
                po_line_ids = self.env['purchase.order.line'].sudo().search([
                    ('product_description_variants', '=', self.name)
                ])
                if po_line_ids:
                    pol = po_line_ids.filtered(lambda l: any(self.name in line for line in l.name.split('\n')) and
                                                        glass.glass_type_id.name in l.name and glass.glass_piece_id.name in l.name
                                              and glass.handing_glass_id.name in l.name and glass.radius_id.name in l.name
                                              )
                    glasses_info = self._get_glasses_info(glass_line=glass)
                    piece_info = ''.join(v for tinfo in glasses_info for k, v in tinfo.items() if k == 'piece')
                    name = '\n'.join(v for tinfo in glasses_info for k, v in tinfo.items() if
                                               k != 'piece') + '\n' + 'LABEL: ' + pol.product_description_variants + ' ' + piece_info
                    if pol and pol.name != name:
                        po_dict[pol.order_id].append((pol.name, name))
                    pol.write({'name': name})
        self.can_show_button_update_cost = False

        # notificar que se actualizo el costo
        common_msg = Markup("<b>%s</b><ul>") % _(
            f"The total cost of the spec {self.name} was updated by user {self.env.user.name}.")
        msg = common_msg
        if purchase_order and old_price_unit != purchase_order_line_id.price_unit:
            msg += Markup("<li> %s: <br/>") % purchase_order_line_id.name
            msg += _(
                "Price unit: %(old_qty)s -> %(new_qty)s",
                old_name=old_price_unit,
                new_name=purchase_order_line_id.price_unit
            ) + Markup("<br/>")
            msg += Markup("</ul>")
            purchase_order.message_post(body=msg)

        # notificar que se actualizaron los vidrios en el specs
        for po, values in po_dict.items():
            msg = Markup("<b>%s</b><ul>") % _(f"The glass specifications of the spec {self.name} were updated by user {self.env.user.name}")
            msg += Markup("<li> %s: <br/>") % _('Lines')
            for tval in values:
                old_name, new_name = tval
                msg += _(
                    "Name: %(old_name)s -> %(new_name)s",
                    old_name=old_name.replace('\n', ','),
                    new_name=new_name.replace('\n', ',')
                ) + Markup("<br/>")
            msg += Markup("</ul>")
            po.message_post(body=msg)

        return True