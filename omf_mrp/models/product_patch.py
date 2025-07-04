from odoo.addons.mrp.models.product import ProductTemplate, ProductProduct

def _compute_template_is_kits(self):
    domain = [('product_tmpl_id', 'in', self.ids), ('type', '=', 'phantom'), ('company_id', 'in', [False, self.env.company.id])]
    bom_mapping = self.env['mrp.bom'].search_read(domain, ['product_tmpl_id'])
    kits_ids = set(b['product_tmpl_id'][0] for b in bom_mapping)
    for template in self:
        template.is_kits = (template.id in kits_ids)

ProductTemplate._compute_is_kits = _compute_template_is_kits


def _compute_variant_is_kits(self):
    domain = ['&', ('type', '=', 'phantom'),
              '&', ('company_id', 'in', [False, self.env.company.id]),
                    '|', ('product_id', 'in', self.ids),
                        '&', ('product_id', '=', False),
                                ('product_tmpl_id', 'in', self.product_tmpl_id.ids)]
    bom_mapping = self.env['mrp.bom'].search_read(domain, ['product_tmpl_id', 'product_id'])
    kits_template_ids = set([])
    kits_product_ids = set([])
    for bom_data in bom_mapping:
        if bom_data['product_id']:
            kits_product_ids.add(bom_data['product_id'][0])
        else:
            kits_template_ids.add(bom_data['product_tmpl_id'][0])
    for product in self:
        product.is_kits = (product.id in kits_product_ids or product.product_tmpl_id.id in kits_template_ids)

ProductProduct._compute_is_kits = _compute_variant_is_kits
