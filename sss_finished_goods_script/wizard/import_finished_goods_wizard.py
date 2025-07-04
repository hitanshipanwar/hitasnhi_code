from odoo import api, fields, models, _
import base64
import xlrd
from odoo.exceptions import AccessError, MissingError, ValidationError, UserError


class ImportFinishedGoods(models.TransientModel):
    _name = 'import.finished.goods'

    finished_goods = fields.Binary('Finished Goods', required=True)
    ref_tag_id = fields.Many2one('sale.order', "Sale Tag Reference")
    is_custom_selection = fields.Boolean(string="Custom Selection")
    location_id = fields.Many2one('stock.location',string="Source Location", required=True)
    location_dest_id = fields.Many2one('stock.location',string="Destination Location", required=True)

    def import_finished_goods(self):
        wb = xlrd.open_workbook(file_contents=base64.decodebytes(self.finished_goods))
        product_obj = self.env['product.product']
        sale_order_obj = self.env['sale.order']
        res_partner_obj = self.env['res.partner']
        stock_picking_obj = self.env['stock.picking']
        product_packaging_obj = self.env['product.packaging']
        stock_quant_obj = self.env['stock.quant']
        sale_order_line_obj = self.env['sale.order.line']
        picking_val_list_internal = []
        picking_val_list = []
        picking_ids = []
        document_id = False
        customer_id = False
        sale_order_line_list = []
        # stock_move_list = []
        sheet = wb.sheet_by_index(0)
        for row in range(sheet.nrows):
            row_value = sheet.row_values(row)
            if row == 1 and row_value[1]:
                document_id = sale_order_obj.search([('name', '=', row_value[1]), ('is_custom_order', '=', True), ('state','in',('sale','done'))])
                if not document_id:
                    document_id = self.ref_tag_id
                    if not document_id:
                        self.is_custom_selection = True
                        self._cr.commit()
                        raise UserError(_("No matching Sale Document found : %s \n You can either select here from the list", row_value[1]))
                # if row_value[1] and self.ref_tag_id:
                #     raise UserError(_("Both Side Ref Given.........."))
                    # return {
                    #     'type': 'ir.actions.act_window',
                    #     # 'name': _('Print Reports Wizard'),
                    #     'res_model' : 'select.tag.order',
                    #     'view_mode': 'form',
                    #     'view_id': self.env.ref(
                    #         'sss_finished_goods_script.select_tag_order_wiz_view_form').id,
                    #     'target': 'new',
                    #     'context': self.env.context,
                    # }

            if row > 6 and row_value[1] and row_value[2]:
               
                product_id = product_obj.create({
                    'name': row_value[4],
                    'detailed_type': 'product',
                    'barcode': row_value[1],
                    'weight': row_value[3],
                    'default_code': row_value[1],
                })
              
                package_id = product_packaging_obj.create({
                    'name': row_value[1],
                    'product_id': product_id.id,
                    'qty': row_value[2],
                    'package_type_id': self.env.ref('kitchen_purchase_request.package_type_box_custom').id
                })
                picking_val_list_internal.append((0, 0, {
                    'name': product_id.name if product_id else '',
                    'product_id': product_id.id if product_id else False,
                    'product_uom_qty': 1.0,
                    'componants': row_value[2],
                    'location_id': self.location_id.id,
                    'location_dest_id': self.location_dest_id.id,
                    'product_packaging_id': package_id.id,
                }))
                picking_val_list.append((0, 0, {
                    'name': product_id.name if product_id else '',
                    'product_id': product_id.id if product_id else False,
                    'product_uom_qty': 1.0,
                    'componants': row_value[2],
                    'location_id': self.env.ref('stock.stock_location_stock').id,
                    'location_dest_id': self.env.ref('stock.stock_location_customers').id,
                    'product_packaging_id': package_id.id,
                }))


                order_line_id = sale_order_line_obj.create({
                    'name': product_id.name if product_id else '',
                    'product_id': product_id.id if product_id else False,
                    'product_uom_qty': 1.0,
                    'order_id':document_id.id,
                    'product_packaging_id': package_id.id
                    })

                stock_quant_id = stock_quant_obj.create({
                    'location_id' : self.location_id.id,
                    'product_id' : product_id.id,
                    'inventory_quantity' : 0,
                    'inventory_date': fields.Date.today()
                })
                stock_quant_id.action_apply_inventory()
                stock_quant_obj._update_available_quantity(product_id, self.location_id, 1)
        document_id.write({'order_line': [(4, order_line_id.id)]})
        picking_vals_internal = {
            'picking_type_id': self.env.ref('stock.picking_type_internal').id,
            'origin': document_id.name,
            'tag_job_sale_ref': document_id.id,
            'location_id': self.location_id.id,
            'location_dest_id': self.location_dest_id.id,
            'sale_internal_id': document_id.id,
            'move_ids': picking_val_list_internal,
        }
        picking_internal_id = stock_picking_obj.create(picking_vals_internal)
        picking_name = ''
        for picking in document_id.picking_ids:
            picking.write({'location_id':self.location_dest_id.id,
                'location_dest_id': self.env.ref('stock.stock_location_customers').id})
            picking_name = picking.name

        document_id.write({'picking_internal_ids':[((4,picking_internal_id.id))]})
        message = "Finished Goods Imported Successfully...!  Your Picking References are : " + picking_internal_id.name + "," + picking_name
        return {
            'effect': {
                'fadeout': 'slow',
                'message': message,
                'img_url': '/kitchen_purchase_request/static/images/smile.svg',
                'type': 'rainbow_man',
            }
        }