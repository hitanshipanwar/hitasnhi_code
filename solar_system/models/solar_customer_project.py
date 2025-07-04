from odoo import fields,api,models,_
from odoo.exceptions import UserError, ValidationError
from odoo.addons.adyen_platforms.util import AdyenProxyAuth
from datetime import datetime

# Sunen
from datetime import timedelta
from pytz import utc
from random import randint

TIMEOUT = 60

class SolarSystemModel(models.Model):
	_name = 'solar.system'
	_inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']
	_description = 'Solar System'
	_rec_name = 'sequence_pro_no'

	customer_project_state = fields.Selection(selection=[
				('saveasdraft', 'Draft'),
				('draft', 'Waiting'),
				('open', 'Invite bidders'),
				('inprogress', 'Compare & Select'),
				('close', 'Complete'),
			], string='Status',default='saveasdraft',tracking=True, readonly=True)

	supplier_project_state = fields.Selection(selection=[
				('open', 'Open'),
				('inprogress', 'InProgress'),
				('won', 'Won'),
				('lost', 'Lost'),
			], string='Status supplier',readonly=True, default='open',tracking=True)
	
	suppiler_status_ids = fields.Many2many('solar.supplier') 
	suppiler_intrested_ids = fields.Many2many('res.partner') 
	
	sequence_pro_no = fields.Char(string='Sequence',index=True,copy=False)
	project_create_date = fields.Date(string='Date', default=fields.Date.today())
	hour = fields.Integer('Hours')
	con_hour = fields.Integer('Config Hours')

	project_datetime = fields.Datetime(string='DateTime',compute="_compute_datetime")
	property_option_new = fields.Selection([('yes','Own'),('no','Rent')],tracking=True)
	message = fields.Text(string="Unfortunately the owner of the property needs to make the decision to install solar power.We're sorry we couldn't help you further.", readonly=True, store=True,tracking=True)
	shading_issue = fields.Selection([('yes','Yes'),('no','No')],tracking=True)
	solar_system = fields.Selection([('yes','Yes'),('no','No')],tracking=True)
	property_select = fields.Selection([('exit',' Existing Property'),('under','Property under construction'),('soon','A Property begin construction soon'),('no','No Property or plans as of now')])
	remove_panels = fields.Selection([('yes','Yes'),('no','No')],tracking=True)
	no_panels = fields.Char(tracking=True)
	upgrade_system = fields.Selection([('yes','Yes'),('no','No')],tracking=True)
	add_panels = fields.Selection([('yes','Yes'),('no','No')],tracking=True)
	add_battery = fields.Selection([('yes','Yes'),('no','No')],tracking=True)
	add_battery_new = fields.Selection([('yes','Yes'),('no','No')],tracking=True)
	message_battery = fields.Text(string="We don’t provide only removals of panels. Please contact us again.", readonly=True, store=True)
	existing_solar = fields.Text(string="Size of the existing solar system",tracking=True)
	inverter_brand = fields.Text(tracking=True)
	inverter_phase = fields.Text(tracking=True)
	inverter_capacity = fields.Text(tracking=True)
	storage_size = fields.Text(tracking=True)
	solar_type = fields.Selection([('top','Top Quality (Most expensive)'),('standard','Standard quality at good price'),('select','Please specify choice of your solar panels brand')])
	type_box = fields.Char(tracking=True)
	inverter_type = fields.Selection([('top','Top Quality (Most expensive)'),('std','Standard quality at good price'),('micro','Micro Inverters'),('select','Please specify choice of your Inverter brand')])
	battery_backup = fields.Selection([('yes','Yes'),('no','No')],tracking=True)
	backup_box = fields.Char(tracking=True)
	brand_box = fields.Char(tracking=True)
	property_type = fields.Selection([('stand','Stand-alone home'),('town','Townhouse'),('villa','Villa'),('apart','Apartment'),('commer','Commercial / Business site')],tracking=True)
	story_no = fields.Selection([('singal','Single story'),('double','Double story'),('trippel','Triple  story'),('other','Other')],tracking=True)
	roof_type = fields.Selection([('tin','Tin / Coulourbond'),('terr','Terracotta'),('tile','Tile'),('slate','Slate'),('asbestos','Asbestos'),('flat','Flat'),('other','Other')],tracking=True)
	roof_text_box = fields.Text(tracking=True)
	pay_quarterly = fields.Selection([('less','Less Than $500'),('five','$500-$900'),('nine','$900-$2000'),('over','Over $2000'),('no','Don’t Know')],tracking=True)
	solar_size = fields.Selection([('five','5 KW'),('six','6.6 KW'),('ten','10 kW'),('not','Not Sure'),('specify','Specify system size')],tracking=True)
	specify_box = fields.Float(tracking=True)
	cash_fin = fields.Selection([('cash','Cash'),('finance','Finance (monthly/weekly payments)')],tracking=True)
	comment_box = fields.Char(tracking=True)
	is_finsh_time = fields.Boolean(compute='_compute_finsh_time_data')

	let = fields.Char(string="Let")
	leng = fields.Char(string="Lang")

	# Sunen
	project_end_date = fields.Datetime('Track End Date', compute='_compute_end_date', store=True)
	track_start_remaining = fields.Integer(
		'Minutes before track starts', compute='_compute_track_time_data',
		help="Remaining time before track starts (seconds)")
	track_start_relative = fields.Integer(
		'Minutes compare to track start', compute='_compute_track_time_data',
		help="Relative time compared to track start (seconds)")
	website_cta_start_remaining = fields.Integer(
		'Minutes before CTA starts', compute='_compute_cta_time_data',
		help="Remaining time before CTA starts (seconds)")

	
	@api.depends('project_datetime', 'con_hour')
	def _compute_end_date(self):
		for track in self:
			if track.project_datetime:
				delta = timedelta(minutes=60 * track.con_hour)
				track.project_end_date = track.project_datetime + delta
			else:
				track.project_end_date = False

	@api.depends('project_datetime', 'project_end_date')
	def _compute_track_time_data(self):
		""" Compute start and remaining time for track itself. Do everything in
		UTC as we compute only time deltas here. """
		now_utc = utc.localize(fields.Datetime.now().replace(microsecond=0))
		for track in self:
			if not track.project_datetime:
				track.track_start_relative = track.track_start_remaining = 0
				continue
			date_begin_utc = utc.localize(track.project_datetime, is_dst=False)
			date_end_utc = utc.localize(track.project_end_date, is_dst=False)
			
			if date_begin_utc >= now_utc:
				track.track_start_relative = int((date_begin_utc - now_utc).total_seconds())
				track.track_start_remaining = track.track_start_relative
				# print(track.track_start_remaining,"-----------------",track.track_start_relative,)
			else:
				track.track_start_relative = int((now_utc - date_begin_utc).total_seconds())
				track.track_start_remaining = 0
				
	@api.depends('project_datetime', 'project_end_date')
	def _compute_cta_time_data(self):
		""" Compute start and remaining time for track itself. Do everything in
		UTC as we compute only time deltas here. """
		now_utc = utc.localize(fields.Datetime.now().replace(microsecond=0))
		for track in self:
			
			date_begin_utc = utc.localize(track.project_datetime, is_dst=False) + timedelta(minutes=60 or 0)
			date_end_utc = utc.localize(track.project_end_date, is_dst=False)
				
			td = date_end_utc - (now_utc)
			# total = date_end_utc - td 
			track.website_cta_start_remaining = int(td.total_seconds())	

	@api.depends('website_cta_start_remaining')
	def _compute_finsh_time_data(self):		
		for rec in self:
			if rec.website_cta_start_remaining <= 0:
				rec.is_finsh_time = True
			else:
				rec.is_finsh_time = False

	# project create date depends with project datetime fields
	@api.depends('project_create_date')
	def _compute_datetime(self):
		for rec in self:
			# rec.project_datetime = rec.project_create_date
			rec.project_datetime = datetime.now()

	#cron method for schedule the time periods............
	@api.model
	def cron_job_method(self):
		data = self.env['solar.system'].sudo().search([])
		record = self.env['solar.supplier'].sudo().search([])
		closing_hours = self.env['ir.config_parameter'].sudo().get_param('solar_system.closing_hours')
		email_from = self.env['ir.mail_server'].sudo().search([],limit=1)

		for rec in data:
			# rec.project_datetime = rec.project_create_date
			a = rec.project_datetime
			b = datetime.today()
			c = (b - a).total_seconds()
			hours = round(c,0) // 3600
			c1 = (b - a).days
			rec.hour = hours
			
			value = fields.Date.today()-rec.project_create_date
			if rec.customer_project_state == 'open' and hours >= int(closing_hours):
				rec.customer_project_state = 'inprogress'
				mail_values_user_check = {
					'subject': 'Your Project Status Update' ,
					'body_html': "<div>Your Project Is Now In Compare & Select Stage.<br />You can easily select the supplier for your project now.</div>",
					'email_from': email_from.smtp_user,
					'email_to':self.customer_id.email,
				}
				create_and_send_email = self.env['mail.mail'].sudo().create(mail_values_user_check).sudo().send()

		for rec in record:
			value = fields.Date.today()-rec.supplier_create_date
			if value.days > 3 and rec.project_state == 'open':
				rec.project_state = 'inprogress'

	# sequence number method...........
	@api.model
	def create(self,vals):
		closing_hours = self.env['ir.config_parameter'].sudo().get_param('solar_system.closing_hours')

		if vals.get('sequence_pro_no', 'New') == 'New':
			vals['sequence_pro_no'] = self.env['ir.sequence'].next_by_code('solar.system') or 'New'
		vals['con_hour'] = int(closing_hours)
		result = super(SolarSystemModel, self).create(vals)
		result.cron_job_method()
		return result


	# default set country.....................................
	def _get_default_country(self):
		country = self.env['res.country'].search([('code', '=', 'AU')])
		return country

	# Bids fields for the customer O2M
	customer_id = fields.Many2one('res.partner',string="Customer",domain=[('is_supplier','=','customer')])
	supplier_bids_ids = fields.One2many('solar.supplier','solar_project_id',string="Supplier")

	# Address fields for customer..............
	customer_project_name = fields.Char()
	phone = fields.Char(size=10)
	default_no = fields.Char(default="+61")
	email_id = fields.Char()
	country_id = fields.Many2one('res.country', string='Country',domain=[('code','ilike','AU')],default=_get_default_country)
	country_code = fields.Char(related='country_id.code')
	state_id = fields.Many2one('res.country.state', string='State',domain=[('country_id.code','ilike','AU')])
	state_code = fields.Char(related='state_id.code')
	city = fields.Char('City')
	zip = fields.Char('ZIP')
	street = fields.Char('Street')
	house_number_or_name = fields.Char('House Number Or Name')
	multiple_address = fields.Char('Address')


	# Documents Uploads...................................

	house = fields.Binary(string="House:")
	house_name = fields.Char()
	roof = fields.Binary(string="Roof:")
	roof_name = fields.Char()
	meter_box = fields.Binary(string="Meter Box:")
	meter_name = fields.Char()
	electricity_bill = fields.Binary(string="Copy Of Electricity Bill :")
	electricity_bill_name = fields.Char(string="File Name")
	is_other_img = fields.Boolean(string="Is Roof Image",default=False)
	other_img = fields.Binary(string="Roof Layout:")
	other_img_name = fields.Char()
	inverter_wall = fields.Binary(string="Inverter Wall")
	inverter_wall_name = fields.Char()
	meter_box_2 = fields.Binary(string="Meter Box 2:")
	meter_box_2_name = fields.Char()

	# +++++++++++++++++onchange for if roof layout image upload by admin or not+++
	@api.onchange('other_img')
	def ifroofimage(self):
		if self.other_img:
			self.is_other_img = True


	# project side coustomer list in kanban view...........
	def show_detail(self):
		view_id = self.env.ref('solar_system.solar_system_form_view')
		return {
					'name': _('Project'),
					'res_model': 'solar.system',
					'view_mode': 'form',
					'target': 'new',
					'view_id': view_id.id,
					'type': 'ir.actions.act_window',
					'res_id':self.id,
				}


	def Waiting_state_update(self):
		for data in vals:
			vals.customer_project_state = 'draft'
	
	# on change methods for refreshing the radio buttons...................
	@api.onchange('property_option_new')
	def propertyselect(self):
		for value in self:
			value.shading_issue=''
			value.solar_system=''
			value.remove_panels=''
			value.add_panels=''
			value.add_battery=''
			value.upgrade_system=''
			value.add_battery_new=''
			value.solar_type=''
			value.inverter_type=''
			value.solar_size=''

	@api.onchange('solar_system')
	def refreshoption(self):
		for value in self:
			value.remove_panels=''
			value.add_panels=''
			value.add_battery=''
			value.upgrade_system=''
			value.add_battery_new=''
			value.solar_type=''
			value.inverter_type=''
			value.solar_size=''


	@api.onchange('remove_panels')
	def removeoption(self):
		for value in self:
			value.add_panels=''
			value.add_battery=''
			value.upgrade_system=''
			value.add_battery_new=''
			value.solar_type=''
			value.inverter_type=''
			value.solar_size=''

 
	@api.onchange('upgrade_system')
	def removeoptionnew(self):
		for value in self:
			value.add_battery=''
			value.add_battery_new=''
			value.solar_type=''
			value.inverter_type=''
			value.solar_size=''


	@api.onchange('add_panels')
	def addoption(self):
		for value in self:
			value.add_battery=''
			value.upgrade_system=''
			value.add_battery_new=''
			value.solar_type=''
			value.inverter_type=''
			value.solar_size=''
	

	@api.onchange('customer_project_state')
	def projectdraft(self):
		for value in self:
			if value.customer_project_state == 'saveasdraft':
				for bids in value.supplier_bids_ids:
					bids.write({'solar_project_id':'','project_state':'open'})
					bids.supplier_id.write({'bid_count':bids.supplier_id.bid_count+1})


	def validate_to_open_state(self):
		for rec in self:
			rec.customer_project_state = 'open'
			rec.project_create_date = datetime.now()

			sms_text = "Your project Roof Layout submit and your project state to be changed"
			email_from = self.env['ir.mail_server'].sudo().search([],limit=1)
			admin_user = self.env['res.users'].sudo().search([('is_admin', '=' , True)])
			from_admin = admin_user.partner_id.email
			mail_values_user_check = {
						'subject': 'Request Edit Project' ,
						'body_html': sms_text,
						'email_to':rec.customer_id.email,
						'email_cc':from_admin,
						'email_from':email_from.smtp_user,
					}
			create_and_send_email = self.env['mail.mail'].sudo().create(mail_values_user_check).sudo().send()


class ResConfigSettings(models.TransientModel):
	_inherit = 'res.config.settings'

	closing_hours = fields.Integer('Closing Hours')

	@api.onchange('closing_hours')
	def _onchange_solar_hour(self):
		data = self.env['solar.system'].sudo().search([])
		for rec in data:
			rec.con_hour = self.closing_hours

	@api.model
	def get_values(self):
		res = super(ResConfigSettings, self).get_values()
		ICP_sudo = self.env['ir.config_parameter'].sudo()
		closing_hours = ICP_sudo.get_param('solar_system.closing_hours') 
		res.update(closing_hours =closing_hours)
		return res

	def set_values(self):
		super(ResConfigSettings, self).set_values()
		if hasattr(self, 'closing_hours'):
			self.env['ir.config_parameter'].sudo().set_param('solar_system.closing_hours',self.closing_hours)