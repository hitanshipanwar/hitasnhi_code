from odoo import api, fields, models
from datetime import timedelta, time


STOCK_CONDITIONS = [
    ('low_stock', 'Low Stock'),
    ('incoming_low_stock', 'Low Stock - Incoming'),
    ('in_stock', 'In Stock'),
    ('out_stock', 'Out Stock'),
    ('incoming_stock', 'Out of Stock - Incoming'),
]

class Product(models.Model):
    _inherit = "product.product"

    us_low_stock_qty = fields.Float('US Low Stock')
    ca_low_stock_qty = fields.Float('CA Low Stock')
    us_stock_condition = fields.Selection(STOCK_CONDITIONS, string='US Stock Condition', readonly=True, default='in_stock')
    ca_stock_condition = fields.Selection(STOCK_CONDITIONS, string='CA Stock Condition', readonly=True, default='in_stock')
    us_sales_estimate = fields.Float('US 3 Month Sales Estimate')
    us_sales_estimate_2wk = fields.Float('US 2-Week Sales Estimate')
    ca_sales_estimate = fields.Float('CA 3 Month Sales Estimate')
    ca_sales_estimate_2wk = fields.Float('CA 2-Week Sales Estimate')
    component_id = fields.Many2one('product.product', string='Component Product')
    # by default, related fields are retrieved with sudo context, aka all 'qty_available'
    # it is not NECESSARY to have it off on the stock_conditions as those are set by cron
    # but it should mean we re-use the related_sudo=False context of the final one for efficiency
    component_us_stock_condition = fields.Selection(string='US Component Stock Condition', store=True,
                                                    related='component_id.us_stock_condition', related_sudo=False)
    component_ca_stock_condition = fields.Selection(string='CA Component Stock Condition', store=True,
                                                    related='component_id.ca_stock_condition', related_sudo=False)
    component_qty_available = fields.Float(string='Component Quantity Available',
                                           related='component_id.qty_available', related_sudo=False)
    us_last_vendor_id = fields.Many2one('res.partner', string='US Last Purchased From')
    ca_last_vendor_id = fields.Many2one('res.partner', string='CA Last Purchased From')
    act_available = fields.Float('Actual Available', compute='_compute_act_available', compute_sudo=True)
    
    def _compute_act_available(self):
        for product in self:
            product.act_available = product.qty_available - product.outgoing_qty
    
    def _cron_compute_stock_conditions_in_om_wh(self, use_manual_qty_categ_id=None):
        products = self.sudo().search([('type', '=', 'product')])
        products._compute_quantities_in_om_wh(use_manual_qty_categ_id=use_manual_qty_categ_id)

    def _compute_quantities_in_om_wh(self, use_manual_qty_categ_id=None):
        if not use_manual_qty_categ_id:
            use_manual_qty_categ_id = 4
        us_warehouses = self.env['stock.warehouse'].search([('code', '=', 'WH-US')])
        us_warehouse_ids = us_warehouses.ids
        ca_warehouses = self.env['stock.warehouse'].search([('code', 'in', ('WH-CA', 'WH-SU'))])
        ca_warehouse_ids = ca_warehouses.ids
        
        us_company_id = us_warehouses.mapped('company_id').ids[0]
        ca_company_id = ca_warehouses.mapped('company_id').ids[0]
        
        for product in self:
            product.act_available = product.qty_available - product.outgoing_qty    
            product.us_stock_condition = 'in_stock'
            product.ca_stock_condition = 'in_stock'     

        self = self.with_context(company_id=us_company_id, warehouse=us_warehouse_ids)
        one_year_sold_group = self._group_sales_count_in_company(us_company_id)
        for product in self:
            # product = product.with_context(warehouse=us_warehouse_ids)
            us_act_available = product.qty_available - product.outgoing_qty
            # product.us_sales_estimate = product._compute_sales_count_in_company(us_company_id) / 4
            product.us_sales_estimate = one_year_sold_group.get(product.id, {}).get('product_uom_qty', 0.0) / 4.0
            product.us_sales_estimate_2wk = product.us_sales_estimate / 6.0
            # category 1 (all)
            compare_qty = product.us_sales_estimate_2wk if product.categ_id.id == 1 else product.us_sales_estimate
            # category 4 (bulk)
            compare_qty = product.us_low_stock_qty if product.categ_id.id == use_manual_qty_categ_id else compare_qty
            if us_act_available > compare_qty:
            	product.us_stock_condition = 'in_stock'
            elif us_act_available <= 0 and product.incoming_qty > 0:
            	product.us_stock_condition = 'incoming_stock'
            elif product.virtual_available <= 0:
            	product.us_stock_condition = 'out_stock'
            elif us_act_available < compare_qty and product.incoming_qty > 0:
            	product.us_stock_condition = 'incoming_low_stock'
            elif product.virtual_available < compare_qty:
            	product.us_stock_condition = 'low_stock'
        
        self = self.with_context(company_id=ca_company_id, warehouse=ca_warehouse_ids)
        one_year_sold_group = self._group_sales_count_in_company(ca_company_id)
        for product in self:
            # product = product.with_context(warehouse=ca_warehouse_ids)
            ca_act_available = product.qty_available - product.outgoing_qty
            # product.ca_sales_estimate = product._compute_sales_count_in_company(ca_company_id) / 4
            product.ca_sales_estimate = one_year_sold_group.get(product.id, {}).get('product_uom_qty', 0.0) / 4.0
            product.ca_sales_estimate_2wk = product.ca_sales_estimate / 6.0
            # category 1 (all)
            compare_qty = product.ca_sales_estimate_2wk if product.categ_id.id == 1 else product.ca_sales_estimate
            # category 4 (bulk)
            compare_qty = product.ca_low_stock_qty if product.categ_id.id == use_manual_qty_categ_id else compare_qty
            if ca_act_available > compare_qty:
            	product.ca_stock_condition = 'in_stock'
            elif ca_act_available <= 0 and product.incoming_qty > 0:
            	product.ca_stock_condition = 'incoming_stock'
            elif product.virtual_available <= 0:
            	product.ca_stock_condition = 'out_stock'
            elif ca_act_available < compare_qty and product.incoming_qty > 0:
            	product.ca_stock_condition = 'incoming_low_stock'
            elif product.virtual_available < compare_qty:
            	product.ca_stock_condition = 'low_stock'

    
    def _group_sales_count_in_company(self, company_id):
        date_from = fields.Datetime.to_string(fields.datetime.combine(fields.datetime.now() - timedelta(days=365),
                                                                      time.min))
        done_states = self.env['sale.report']._get_done_states()
        domain = [
            ('state', 'in', done_states),
            ('date', '>=', date_from),
            ('company_id', '=', company_id),
        ]
        # if we don't include this, we get all products, which is probably ok for what we're trying to do
        if len(self) < 1001:
            domain.append(('product_id', 'in', self.ids))
        # turn it into a big dict
        return {d['product_id'][0]: d for d in self.env['sale.report'].read_group(domain, ['product_id', 'product_uom_qty'], ['product_id'])}

