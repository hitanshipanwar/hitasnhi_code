from odoo import api, fields, models, _
import base64
import xlrd
from odoo.exceptions import AccessError, MissingError, ValidationError,UserError

class ImportFinishedGoods(models.TransientModel):
    _name = 'import.finished.goods'

    finished_goods = fields.Binary('Finished Goods',required=True)
    ref_tag_id = fields.Many2one('sale.order', "Sale Tag Reference")

    def import_finished_goods(self):
        wb = xlrd.open_workbook(file_contents=base64.decodebytes(self.finished_goods))
        product_id = False
        product_obj = self.env['product.product']
        sale_order_obj = self.env['sale.order']
        res_partner_obj = self.env['res.partner']
        stock_picking_obj = self.env['stock.picking']
        product_packaging_obj = self.env['product.packaging']
        picking_val_list = []
        document_id = False
        product_id = False
        customer_id = False
        stock_move_list = []
        index = 0
        sheet = wb.sheet_by_index(0)
        for row in range(sheet.nrows):
            row_value = sheet.row_values(row)
            if row == 1 and row_value[1]:
                document_id = sale_order_obj.search([('name', '=', row_value[1])])
                if not document_id:
                    raise UserError(_("No matching Sale Document found : %s",row_value[1]))
            if row == 2 and row_value[1]:
                customer_id = res_partner_obj.search([('name', '=', row_value[1])])
                if not customer_id:
                    customer_id = res_partner_obj.create({
                        'name': row_value[1]
                        })
            if row > 6 and row_value[1] and row_value[2]:
                # packaging_val_list = []
                # packaging_val_list.append([0,0,{
                #     'name' : row_value[1],
                #     'qty' : row_value[2]
                product_id = product_obj.create({
                    'name': row_value[4],
                    'detailed_type': 'product',
                    # 'packaging_ids' : packaging_val_list
                    })
                #     }])
                package_id = product_packaging_obj.create({
                    'name': row_value[1],
                    'product_id': product_id.id,
                    'qty': row_value[2],
                    'package_type_id': self.env.ref('kitchen_purchase_request.package_type_box_custom').id
                    })
                picking_val_list.append((0, 0, {
                    'name': product_id.name if product_id else '',
                    'product_id': product_id.id if product_id else False,
                    'product_uom_qty': row_value[2],
                    'location_id': self.env.ref('stock.stock_location_stock').id,
                    'location_dest_id': self.env.ref('stock.stock_location_customers').id,
                    'product_packaging_id': package_id.id
                    }))

        picking_vals = {
            'partner_id': customer_id.id,
            'picking_type_id': self.env.ref('stock.picking_type_out').id,
            'origin': document_id.name,
            'tag_job_sale_ref': document_id.id,
            'location_id': self.env.ref('stock.stock_location_stock').id,
            'location_dest_id': self.env.ref('stock.stock_location_customers').id,
            'move_ids': picking_val_list
        }
        picking_id = stock_picking_obj.create(picking_vals)
        message = "Finished Goods Imported Successfully...!  Your Picking Reference is : "+ picking_id.name
        return {
                'effect': {
                    'fadeout': 'slow',
                    'message': message,
                    'img_url': '/kitchen_purchase_request/static/images/smile.svg',
                    'type': 'rainbow_man',
                }
        }
