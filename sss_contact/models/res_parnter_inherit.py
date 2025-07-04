from odoo import fields, models, api


class ResPartnerInherit(models.Model):
	_inherit = "res.partner"

	vendor_certificate = fields.Many2many('ir.attachment', 'ir_attachment_vendor_cert_ref', 'partner_id_cert', 'attachment_id_cert', 
		string="Select File")
