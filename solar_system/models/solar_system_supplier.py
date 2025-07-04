from odoo import fields,api,models
from datetime import datetime

# jaydeep
# from datetime import timedelta
# from pytz import utc
# from random import randint
# TIMEOUT = 60
class SolarSystemBatteryModel(models.Model):
	_name = 'solar.supplier.battery'
	_inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']
	_description = 'Supplier System Battery'

	battery_attchment_id = fields.Many2one('solar.supplier')
	battery_product_Brand = fields.Char(string="Battery Product Brand",tracking=True)
	battery_product_model_no = fields.Float(string="Battery Product Model No",tracking=True)
	battery_product_warranty = fields.Float(string="Battery Product Warranty",tracking=True)
	battery_made_in = fields.Char(string="Battery Made in",tracking=True)	
	battery_attch_img = fields.Binary(string="Battery Attachments")

class SolarSysteminverterModel(models.Model):
	_name = 'solar.supplier.inverter'
	_inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']
	_description = 'Supplier System Inventer'
	
	inverter_attchment_id = fields.Many2one('solar.supplier')
	inverter_product_Brand = fields.Char(string="Inverter Product Brand",tracking=True)
	inverter_product_model_no = fields.Float(string="Inverter Product Model No",tracking=True)
	inverter_product_warranty = fields.Float(string="Inverter Product Warranty",tracking=True)
	inverter_made_in = fields.Char(string="Inverter Made in",tracking=True)	
	inverter_attch_img = fields.Binary(string="Inverter Attachments")	

class SolarAttchment(models.Model):
	_inherit = 'ir.attachment'

	battery_attchment_id = fields.Many2one('solar.supplier')
	# battery_inverter_attchment_id = fields.Many2one('solar.supplier')
	inbuilt_in_box_attchment_id = fields.Many2one('solar.supplier')	
	supplied_sepretly_attchment_id = fields.Many2one('solar.supplier')	
	battery_supplied_sepretly_attchment_id = fields.Many2one('solar.supplier')	
	how_it_work_attchment_id = fields.Many2one('solar.supplier')	

class SolarSystemModel(models.Model):
	_name = 'solar.supplier'
	_inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']
	_description = 'Supplier System'
	_rec_name = 'sequence_no'

	sequence_no = fields.Char(string='Sequence',index=True,copy=False)
	supplier_create_date = fields.Date(string='Date',default=datetime.now(),tracking=True)
	bid_desc = fields.Text(string="Bid Description" ,tracking=True)
	system_size = fields.Float(tracking=True)
	panels_no = fields.Float(tracking=True)
	panels_brand = fields.Char(tracking=True)
	power_class = fields.Float(tracking=True)
	made_country = fields.Char(tracking=True)
	solar_type = fields.Text(tracking=True)
	manu_year = fields.Integer(tracking=True)
	per_year = fields.Integer(tracking=True)
	inverter_brand = fields.Text(tracking=True)
	inverter_size = fields.Float(tracking=True)
	manu_country = fields.Text(tracking=True)
	warranty = fields.Integer(tracking=True)
	work_warranty = fields.Integer(tracking=True)
	full_price = fields.Integer(tracking=True)

	# batt_full_price = fields.Integer(tracking=True)
	final_price = fields.Integer(tracking=True)
	months = fields.Integer(tracking=True)
	finance_cal = fields.Integer(compute='_compute_financeprice',string="Finance Price Total",tracking=True)
	
	project_state = fields.Selection(selection=[
				('open', 'Open'),
				('inprogress', 'InProgress'),
				('won', 'Won'),
				('lost', 'Lost'),
			], string='Status', required=True, readonly=True, default='open',tracking=True)

	supplier_id = fields.Many2one('res.partner',string="Supplier",domain=[('is_supplier','=','supplier')],tracking=True)
	solar_project_id = fields.Many2one('solar.system',string="Project",domain=[('customer_project_state','=','open')],tracking=True)
	solar_ammount = fields.Float('Ammount')
	# NEW field added
	# Battery Field
	battery_size_kwh = fields.Float(string="Size (kwh)",tracking=True)
	
	# battery_product_Brand = fields.Char(string="Battery Product Brand")
	# battery_product_model_no = fields.Float(string="Battery Product Model No")
	# battery_product_warranty = fields.Float(string="Battery Product Warranty")
	# battery_made_in  = fields.Char(string="Battery Made in")
	# battery_doc_attachment_ids = fields.One2many('ir.attachment','battery_attchment_id', string='Battery Attachments')
	battery_doc_attachment_ids = fields.One2many('solar.supplier.battery','battery_attchment_id', string='Battery Attachments',tracking=True)

	# Inverter
	inverter_two_option = fields.Selection(selection=[
				('inbuilt_in_box', 'Inbuilt in box'),
				('supplied_sepretly', 'Supplied sepretly')
			], string='inverter Supplied', default='inbuilt_in_box',tracking=True)

	# inverter_product_Brand = fields.Char(string="Inverter Product Brand")
	# inverter_product_model_no = fields.Float(string="Inverter Product Model No")
	# inverter_product_warranty = fields.Float(string="Inverter Product Warranty")
	# inverter_made_in  = fields.Char(string="Inverter Made in")
	# inverter_doc_attachment_ids = fields.One2many('ir.attachment','battery_inverter_attchment_id', string='Inverter Attachments')
	inverter_doc_attachment_ids = fields.One2many('solar.supplier.inverter','inverter_attchment_id', string='Inverter Attachments',tracking=True)
	# If select option 1 than
	# Inbuilt

	inbuilt_product_Brand = fields.Char(string="Inbuilt Product Brand",tracking=True)
	inbuilt_product_model_no = fields.Float(string="Inbuilt Product Model No",tracking=True)
	inbuilt_product_warranty = fields.Float(string="Inbuilt Product Warranty",tracking=True)
	inbuilt_made_in  = fields.Char(string="Inbuilt Made in",tracking=True)
	inbuilt_doc_attachment_ids = fields.One2many('ir.attachment','inbuilt_in_box_attchment_id', string='inbuilt Attachments',tracking=True)

	# If select option 2 than
	# Supplied sepretly

	supplied_product_Brand = fields.Char(string="Supplied sepretly Product Brand",tracking=True)
	supplied_product_model_no = fields.Float(string="Supplied sepretly Product Model",tracking=True)
	supplied_product_warranty = fields.Float(string="Supplied sepretly Product Warranty",tracking=True)
	supplied_made_in  = fields.Char(string="Supplied sepretly Made in",tracking=True)
	supplied_doc_attachment_ids = fields.One2many('ir.attachment','supplied_sepretly_attchment_id', string='Supplied Attachments',tracking=True)

	battery_brand = fields.Char(string="Supplied Battery Brand",tracking=True)
	battery_model_no = fields.Float(string="Supplied Model",tracking=True)
	battery_warranty = fields.Float(string="Supplied Warranty",tracking=True)
	battery_supplied_made_in  = fields.Char(string="Supplied Made in",tracking=True)
	battery_doc_attachment_supplied_ids = fields.One2many('ir.attachment','battery_supplied_sepretly_attchment_id', string='battery Attachments',tracking=True)

	how_it_attachment_supplied_ids = fields.One2many('ir.attachment','how_it_work_attchment_id', string='How it will look like ?',tracking=True)

	final_price_incl_install_backup_GST_standard = fields.Float(string="Final Price (incl.install & backup & GST) standard installation",tracking=True)

		

	# compute method for finance price calculation.......................
	@api.depends('final_price','months')
	def _compute_financeprice(self):
		for data in self:
			data.finance_cal = 4 * data.final_price * data.months

	# sequence number method...........
	@api.model
	def create(self,vals):
	   if vals.get('sequence_no', 'New') == 'New':
		   vals['sequence_no'] = self.env['ir.sequence'].next_by_code('solar.supplier') or 'New'
	   result = super(SolarSystemModel, self).create(vals)
	   return result

	# status update after approve the supplier Bid 
	def approved_bid(self):
		vals = self.env['solar.supplier'].sudo().search([('solar_project_id','=',self.solar_project_id.id)])
		rec = self.env['solar.system'].sudo().search([('id','=',self.solar_project_id.id)])
		for data in vals:
			data.update({"project_state":"lost"})
			data.solar_project_id.update({"supplier_project_state":"lost"})

		self.update({"project_state":"won"})
		rec.update({"supplier_project_state":"won"})
		rec.update({"customer_project_state":"close"})


class SupplierApprove(models.Model):
	_inherit='res.partner'

	profile_complete = fields.Boolean(string="Profile Complete",default=False)

	# supplier approve or reject state ..........................
	supplier_validate = fields.Selection(selection=[
						('draft','Draft'),
						('approve','Approved'),
						('reject','Rejected')],string="Supplier Validation",required=True,default='draft')
	
	# then show the customer open stage project 
	def supplier_approve(self):
		sms_text = "Your profile Approved by Admin"
		email_from = self.env['ir.mail_server'].sudo().search([],limit=1)
		email_to = self.email

		mail_values_user_check = {
					'subject': 'Approve Profile' ,
					'body_html': sms_text,
					'email_to':email_to,
					'email_from':email_from.smtp_user,
				}
		create_and_send_email = self.env['mail.mail'].sudo().create(mail_values_user_check).sudo().send()
		self.update({"supplier_validate":"approve"})

	
	# open project hide and send them notification by mail  
	def supplier_reject(self):
		sms_text = "Your profile Reject by Admin"
		email_from = self.env['ir.mail_server'].sudo().search([],limit=1)
		email_to = self.email

		mail_values_user_check = {
					'subject': 'Reject Profile',
					'body_html': sms_text,
					'email_to':email_to,
					'email_from':email_from.smtp_user,
				}
		create_and_send_email = self.env['mail.mail'].sudo().create(mail_values_user_check).sudo().send()
		self.update({"supplier_validate":"reject"})

