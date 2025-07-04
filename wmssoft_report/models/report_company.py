from odoo import fields, models

class ReportCompany(models.Model):
    _name = 'report.company'
    _description = 'Company Details in Report'
    
    name = fields.Char('Name', required=True)
    address = fields.Text('Invoice Address', required=True)
    address_sale = fields.Text('Sale Address', required=True)
    address_delivery = fields.Text('Delivery Address', required=True)
    address_purchase = fields.Text('Purchase Address', required=True)
    bank = fields.Text('Bank Details', required=True)
    email_from_sale = fields.Char('Send Email From(Quotations/SO)')
    email_from_invoice = fields.Char('Send Email From(Invoice)')
