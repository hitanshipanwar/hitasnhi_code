from odoo import fields, api, models, _


class AccountMove(models.Model):
    _inherit = 'account.move'

    picking_id = fields.Many2one('stock.picking', string="Picking",
                                 domain="[('picking_type_id.code', '=', 'outgoing')]")
    po_number = fields.Char("PO Number")
    rep_template_id = fields.Many2one('report.company', 'Templates to Print') 

    def get_courier_info(self):
        vals = {
            'tracking': '',
            'courier': '',
            'catons': ''
        }
        tracking_list = []
        courier_list = []
        catons = 0.0
        proc_picking_ids = []
        sale_lines = self.invoice_line_ids.sale_line_ids
        stock_moves = sale_lines.move_ids.filtered(lambda r: r.state == 'done')
        picking_ids = stock_moves.picking_id
        stock_move_lines = sale_lines.move_ids.filtered(lambda r: r.state == 'done').move_line_ids
        for picking in picking_ids:
            if picking.carrier_tracking_ref:
                tracking_list.append(picking.carrier_tracking_ref)
            if picking.carrier_id:
                courier_list.append(picking.carrier_id.name)
        for move in stock_move_lines:
            if move.result_package_id and move.result_package_id.package_type_id and move.result_package_id.package_type_id.is_carton == True:
                catons += 1.00
        tracking_list = list(set(tracking_list))
        courier_list = list(set(courier_list))
        vals['tracking'] = ', '.join(tracking_list)
        vals['courier'] = ', '.join(courier_list)
        vals['catons'] = catons
        return vals

    def find_so_items(self, order):
        lines = []
        for rec in order:
            if rec.order_line:
                for line in rec.order_line:
                    if line.qty_invoiced == 0.0:
                        lines.append(line)
        return lines

    def action_invoice_sent(self):
        """ Open a window to compose an email, with the edi invoice template
            message loaded by default
        """
        self.ensure_one()
        template = self.env.ref(self._get_mail_template(), raise_if_not_found=False)
        lang = False
        if template:
            # Todo [Dhaval]: add custom email from
            if self.partner_id and self.partner_id.rep_template_id and self.partner_id.rep_template_id.email_from_invoice:
                template.email_from = self.partner_id.rep_template_id.email_from_invoice
            else:
                template.email_from = self.user_id.email_formatted or self.env.user.email_formatted

            lang = template._render_lang(self.ids)[self.id]
        if not lang:
            lang = get_lang(self.env).code
        compose_form = self.env.ref('account.account_invoice_send_wizard_form', raise_if_not_found=False)
        ctx = dict(
            default_model='account.move',
            default_res_id=self.id,
            # For the sake of consistency we need a default_res_model if
            # default_res_id is set. Not renaming default_model as it can
            # create many side-effects.
            default_res_model='account.move',
            default_use_template=bool(template),
            default_template_id=template and template.id or False,
            default_composition_mode='comment',
            mark_invoice_as_sent=True,
            custom_layout="mail.mail_notification_paynow",
            model_description=self.with_context(lang=lang).type_name,
            force_email=True,
        )
        return {
            'name': _('Send Invoice'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'account.invoice.send',
            'views': [(compose_form.id, 'form')],
            'view_id': compose_form.id,
            'target': 'new',
            'context': ctx,
        }


# class AccountMoveLine(models.Model):
#     _inherit = 'account.move.line'

#     def get_employee_names(self):
#         employee = []
#         for line in self.sale_line_ids:
#             name = line.employee_name
#             if name and name not in employee:
#                 employee.append(name)
#         if employee:
#             return ','.join(employee)
#         else:
#             return ''

#     # def get_additional_info(self):
#     #     info = []
#     #     for line in self.sale_line_ids:
#     #         name = line.x_studio_additional_information
#     #         if name and name not in info:
#     #             info.append(name)
#     #     return info and ','.join(info) or ''

#     def find_bo_status(self,order,product_id):
#         pending = "yes"
#         done_picking = []
#         if order.picking_ids:
#             for picking in order.picking_ids:
#                 done_picking.append(picking.state)
#         list_new = list(set(done_picking))
#         if len(list_new) > 1:
#             pending = "yes"
#         else:
#              pending = "no"
#         return pending


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    def get_employee_names(self):
        employee = []
        for line in self.sale_line_ids:
            name = line.employee_name
            if name and name not in employee:
                employee.append(name)
        if employee:
            return ','.join(employee)
        else:
            return ''

    def get_additional_info(self):
        info = []
        for line in self.sale_line_ids:
            name = line.x_studio_additional_information
            if name and name not in info:
                info.append(name)
        return info and ','.join(info) or ''

    delivered_qty = fields.Float(string='Delivered', compute="_compute_delivered_qty", store=True)
    order_qty = fields.Float(string='Order Qty', compute="_compute_delivered_qty", store=True)
    backorder_qty = fields.Float(string='Backorder Qty', compute="_compute_delivered_qty", store=True)

    @api.depends('sale_line_ids', 'product_id')
    def _compute_delivered_qty(self):
        for line in self:
            delivered_qty = 0
            order_qty = 0
            backorder_qty = 0

            for sale_line in line.sale_line_ids:
                delivered_qty += sale_line.qty_delivered
                order_qty += sale_line.product_uom_qty
                backorder_qty += order_qty - delivered_qty

            line.delivered_qty = delivered_qty
            line.order_qty = order_qty
            line.backorder_qty = backorder_qty

    def find_bo_status(self, order, product_id):
        pending = "yes"
        done_picking = []
        if order.picking_ids:
            for picking in order.picking_ids:
                done_picking.append(picking.state)
        list_new = list(set(done_picking))
        if len(list_new) > 1:
            pending = "yes"
        else:
            pending = "no"
        return pending


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    employee_name = fields.Char('Employee Name')
    x_studio_additional_information = fields.Text('Additional Information')

    def find_bo_status(self, order, product_id):
        pending = "yes"
        done_picking = []
        if order.picking_ids:
            for picking in order.picking_ids:
                done_picking.append(picking.state)
        list_new = list(set(done_picking))
        if len(list_new) > 1:
            pending = "yes"
        else:
            pending = "no"
        return pending
