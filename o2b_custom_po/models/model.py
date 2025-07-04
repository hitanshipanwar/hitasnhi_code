from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError, ValidationError
import base64
import io
import re



# task HSO-1838 starts

class ResCompany(models.Model):
    _inherit = "res.company"

    purchase_order_notes = fields.Html(string="Default Purchase Order Notes",translate=True)
    purchase_setting_container = fields.Boolean(string="Default Notes")




class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"
    
    purchase_setting_container = fields.Boolean(string="Default Notes",default=lambda self: self.env.company.purchase_setting_container)
    purchase_order_notes = fields.Html(related='company_id.purchase_order_notes', readonly=False ,string="Default Purchase Order Notes")
    

    def set_values(self):
        """ Save purchase_setting_container to company settings """
        super(ResConfigSettings, self).set_values()
        self.env.company.purchase_setting_container = self.purchase_setting_container

    def get_values(self):
        """ Retrieve purchase_setting_container from company settings """
        res = super(ResConfigSettings, self).get_values()
        res.update({
            'purchase_setting_container': self.env.company.purchase_setting_container
        })
        return res


    
class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    @api.onchange('company_id')
    def _onchange_company_id(self):
        if self.company_id and self.company_id.purchase_setting_container:
            self.notes = self.company_id.purchase_order_notes
    

# task HSO-1838 ends

# task HSO-1839 starts

class ResPartner(models.Model):
    _inherit = "res.partner"

    sales_order_notes_enabled = fields.Boolean(string="Enable Sales Order Notes")
    sales_order_notes = fields.Html(string="Sales Order Notes")



class SaleOrder(models.Model):
    _inherit = "sale.order"
    
    @api.onchange('partner_id')
    def onchange_partner_id(self):
        res = super().onchange_partner_id()
        if self.partner_id and self.partner_id.sales_order_notes_enabled:
            self.note = self.partner_id.sales_order_notes
        elif self.sale_order_template_id and self.sale_order_template_id.order_notes_enabled:
            self.note = self.sale_order_template_id.order_notes
        else:
            self.note = self.with_context(lang=self.partner_id.lang).env.company.invoice_terms

        return res

# task HSO-1839 ends


# task HSO-1840 starts

    @api.onchange('sale_order_template_id')
    def _onchange_sale_order_template_id(self):
        if self.partner_id and self.partner_id.sales_order_notes_enabled:
            self.note = self.partner_id.sales_order_notes
        elif self.sale_order_template_id and self.sale_order_template_id.order_notes_enabled:
            self.note = self.sale_order_template_id.order_notes
        else:
            self.onchange_partner_id()


class SaleOrderTemplate(models.Model):
    _inherit = "sale.order.template"

    order_notes_enabled = fields.Boolean(string="Enable Order Notes")
    order_notes = fields.Html(string="Order Notes")

# task HSO-1840 ends