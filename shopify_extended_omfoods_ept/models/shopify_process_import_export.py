from odoo import models, fields, api, _

class shopify_process_import_export(models.TransientModel):
    _inherit = 'shopify.process.import.export'

    # @api.multi
    def update_product_tracks(self):
        product_tmpl_obj=self.env['product.template']
        shopify_product_tmpl_obj = self.env['shopify.product.template.ept']

        product_ids=self._context.get('active_ids')
        instances=self.shopify_instance_ids

        for instance in instances:
            if product_ids:
                odooo_products=product_tmpl_obj.search([('id','in',product_ids)])
                products = shopify_product_tmpl_obj.search([('shopify_instance_id', '=', instance.id), ('product_tmpl_id', 'in', odooo_products.ids), ('exported_in_shopify', '=', True)])
                products and shopify_product_tmpl_obj.update_product_tracks_in_shopify(instance,products)
        return True