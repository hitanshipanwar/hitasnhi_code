from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class ExceptionRule(models.Model):
    _inherit = 'exception.rule'

    model = fields.Selection(
        selection_add=[
            ('mrp.production', 'Production'),
        ],
        ondelete={
            'mrp.production': 'cascade',
        },
    )
    production_ids = fields.Many2many(
        'mrp.production',
        string="Productions")


class MrpProduction(models.Model):
    _inherit = ['mrp.production', 'base.exception']
    _name = 'mrp.production'

    po_lot_id = fields.Many2one('purchase.order','PO/Lot#')

    label_type = fields.Selection([
        ('ORG', 'Print Organic Label'), 
        ('NON-ORG', 'Print Non-Organic Label')],
        default='ORG', compute='_compute_label_type', store=True, readonly=False)

    po_country = fields.Many2one('res.country', string='Country of Origin', compute='_compute_po_info', store=True)
    inventory_reconciled = fields.Boolean()
    purchase_order_notes = fields.Text('PO Notes', compute='_compute_po_info', compute_sudo=True)
    
    @api.depends('po_lot_id')
    def _compute_label_type(self):
        for production in self:
            if production.po_lot_id:
                product_po_lines = production.po_lot_id.order_line.filtered(lambda l: l.product_id in production.move_raw_ids.product_id)
                if not product_po_lines:
                    raise ValidationError(_('The PO/Lot# referenced does not contain any products needed for this Manufacturing Order.'))
                if production.company_id.country_id.code == 'CA' and any(product_po_lines.mapped(lambda l: l.organic_status == 'NON-ORG')):
                    production.label_type = 'NON-ORG'

    @api.depends('po_lot_id.order_line.country_of_origin', 'po_lot_id.order_line.purchase_order_notes')
    def _compute_po_info(self):
        for production in self:
            production.po_country = False
            production.purchase_order_notes = False
            if production.move_raw_ids and production.move_raw_ids[0].product_id:
                product = production.move_raw_ids[0].product_id
                line = production.po_lot_id.order_line.filtered(lambda l: l.product_id == product)
                if line:
                    production.po_country = line.country_of_origin
                    production.purchase_order_notes = line.purchase_order_notes

    @api.model
    def _exception_rule_eval_context(self, rec):
        res = super(MrpProduction, self)._exception_rule_eval_context(rec)
        res['production'] = rec
        return res

    @api.model
    def _reverse_field(self):
        return 'production_ids'

    @api.model
    def _get_popup_action(self):
        return self.env.ref('omf_mrp.action_mrp_production_exception_confirm')

    def action_confirm(self):
        if len(self) == 1:
            if self.detect_exceptions():
                return self._popup_exceptions()
            else:
                return super().action_confirm()
        valid = self.filtered(lambda p: not p.detect_exceptions())
        return super(MrpProduction, valid).action_confirm()

    def action_open_quants(self):
        action = self.product_id.action_open_quants()
        action["name"] = 'Reconcile Inventory'
        return action

    @api.model
    def _migrate_studio_fields(self):
        sql = """
        update mrp_production
        set po_country = x_studio_field_oQcb9,
            po_lot_id = x_studio_po_lot,
            label_type = 'ORG';
        update purchase_order_line
        set country_of_origin = x_studio_country_of_origin;
        """
        self.env.cr.execute(sql)
