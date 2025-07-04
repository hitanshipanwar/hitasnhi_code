from odoo import fields,api,models
# JAYDEEP
from datetime import datetime
from datetime import timedelta
from pytz import utc
from random import randint

class InstallationSolarSystem(models.Model):
	_name = 'installation.solar.system'
	_inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']
	_description = 'Installation Solar'
	_rec_name = 'sequence_pro_no'

	sequence_pro_no = fields.Char(string='Sequence',index=True,copy=False)
	supplier_id = fields.Many2one('solar.supplier' ,string="installer")
	supplier_customer_id = fields.Many2one('res.partner',string="Customer",domain=[('is_supplier','=','supplier')])

	remove_existing_solar = fields.Selection([('yes','Yes'),('no','No')],tracking=True,string="Do you want to remove existing solar panels ?")
	panels_remove = fields.Integer(string="How many panels you want to remove?")
	size_of_solar_system = fields.Integer(string="Size of solar system")
	remove_inverter_solar = fields.Selection([('yes','Yes'),('no','No')],tracking=True,string="Do you want to remove inverter ?")
	
	# PV FLOW+++++++++++
	pv_system_solar = fields.Selection([('yes','Yes'),('no','No')],tracking=True,string="Do you want to upgrade PV system ?")
	# NO CONDITION =======
	house_pic = fields.Binary(string="House Pic")
	house_name = fields.Char()
	roof_title_pic = fields.Binary(string="Roof tile pic")
	roof_name = fields.Char()
	roof_layout = fields.Binary(string="Roof Layout")
	meter_name=fields.Char()

	# 2 flow start ==========

	# NEW PV System installation
	new_pv_system_installation = fields.Selection([('yes','Yes'),('no','No')],tracking=True, string="NEW PV System Installation")
	panels_need = fields.Integer(string="How many panels you need")
	panels_power_class = fields.Integer(string="panels power class") 		
	single_three_ph = fields.Char(string="Single ph or three ph") 		
	inverter_size = fields.Char(string="Inverter Size") 		

	export_device = fields.Selection([('yes','Yes'),('no','No')],tracking=True, string="Export Device")

	panels_tilts = fields.Selection([('yes','Yes'),('no','No')],tracking=True, string="Panels Tilts")
	how_many_tilts = fields.Float(string="How Many")

	clip_locks = fields.Selection([('yes','Yes'),('no','No')],tracking=True, string="Clip Locks")
	how_many_clip_locks = fields.Float(string="How Many")

	storey = fields.Selection([('single','Single'),('double','Double')],tracking=True, string="Storey")

	# Documents Uploads...................................

	# tin_doc = fields.Binary(string="Tin Document:")
	# tile_doc = fields.Binary(string="Tile Document:")
	# flat_doc = fields.Binary(string="Flat Document:")
	# terracotta_doc = fields.Binary(string="Terracotta Document:")


	# BATTERY BACKUP =============================
	battery_backup = fields.Selection([('yes','Yes'),('no','No')],tracking=True, string="Battery Backup")

	# NO IMAGE +++++++++
	# Documents Uploads...................................
	hours_timer=fields.Integer(string='Hours Time')
	house = fields.Binary(string="House Pic:")
	house_name_up=fields.Char()
	roof = fields.Binary(string="Roof Layout:")
	roof_nm=fields.Char()
	meter_box = fields.Binary(string="Meter box pic Zoom in:")
	meter_box_up=fields.Char()
	meter_box_2 = fields.Binary(string="Meter box pic Zoom out:")
	meter_box_2_name=fields.Char()
	roof_tile_pic = fields.Binary(string="Roof Tile Pic:")
	roof_name_up=fields.Char()
	inverter_wall = fields.Binary(string="Meter box wall pic:")
	inverter_wall_name =fields.Char()
	battery_need_install = fields.Binary(string="Pic where battery need to install")
	battery_need_install_name=fields.Char()

	battery_backup_second = fields.Selection([('yes','Yes'),('no','No')],tracking=True, string="Battery Backup")
	battery_size = fields.Float(string="Battery Size")
	battery_model_no = fields.Float(string="Battery Model No")
	battery_brand = fields.Char(string="Battery Brand")

	let = fields.Char(string="Let")
	leng = fields.Char(string="Lang")
	address_line_1=fields.Char()
	address_line_2=fields.Char()
	
	roof_type = fields.Selection([('tin','Tin / Coulourbond'),('terr','Terracotta'),('tile','Tile'),('slate','Slate'),('asbestos','Asbestos'),('flat','Flat'),('other','Other')])
	panels_tile_need=fields.Char()
	clip_locks_need=fields.Char()
	is_complate=fields.Boolean()
	paid_order_id=fields.Many2one('sale.order')
	bid_paid_order_id=fields.Many2one('sale.order')
	# INSTALLER ADDRESS +++++++++++++++

	# default set country.....................................
	def _get_default_country(self):
		country = self.env['res.country'].search([('code', '=', 'AU')])
		return country

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

	installer_project_state = fields.Selection(selection=[
				('saveasdraft', 'Draft'),
				('draft', 'Waiting'),
				('open', 'Invite bidders'),
				('inprogress', 'Compare & Select'),
				('close', 'Complete'),
			], string='Status',default='saveasdraft',tracking=True, readonly=True)

	project_state = fields.Selection(selection=[
				('open', 'Open'),
				('inprogress', 'InProgress'),
				('won', 'Won'),
				('lost', 'Lost'),
			], string='Status', required=True, readonly=True, default='open',tracking=True)

	installer_bids_ids = fields.One2many('installer.bid','project_id',string="Installer")
	suppiler_status_ids = fields.Many2many('installer.bid') 
	installer_intrested_ids = fields.Many2many('res.partner') 

	# JAYDEEP
	project_create_date = fields.Date(string='Date', default=fields.Date.today())
	hour = fields.Integer('Hours')
	con_hour = fields.Integer('Config Hours')
	project_datetime = fields.Datetime(string='DateTime',compute="_compute_datetime")
	
	is_finsh_time = fields.Boolean(compute='_compute_finsh_time_data')
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
		data = self.env['installation.solar.system'].sudo().search([])
		record = self.env['installer.bid'].sudo().search([])
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
			if rec.installer_project_state == 'open' and hours >= int(closing_hours):
				rec.installer_project_state = 'inprogress'
				rec.project_state = 'inprogress'
				mail_values_user_check = {
					'subject': 'Your Project Status Update' ,
					'body_html': "<div>Your Project Is Now In Compare & Select Stage.<br />You can easily select the supplier for your project now.</div>",
					'email_from': email_from.smtp_user,
					'email_to':self.customer_id.email,
				}
				create_and_send_email = self.env['mail.mail'].sudo().create(mail_values_user_check).sudo().send()

		for rec in record:
			value = fields.Date.today() - rec.installer_create_date
			if value.days > 3 and rec.project_state == 'open':
				rec.project_state = 'inprogress'			

	# sequence number method...........
	@api.model
	def create(self,vals):
		closing_hours = self.env['ir.config_parameter'].sudo().get_param('solar_system.closing_hours')
		if vals.get('sequence_pro_no', 'New') == 'New':
			vals['sequence_pro_no'] = self.env['ir.sequence'].next_by_code('installation.solar.system') or 'New'
		vals['con_hour'] = int(closing_hours)
		result = super(InstallationSolarSystem, self).create(vals)
		result.cron_job_method()
		return result

	@api.onchange('installer_project_state')
	def projectdraft(self):
		for value in self:
			if value.installer_project_state == 'saveasdraft':
				for bids in value.installer_bids_ids:
					bids.write({'project_id':'','project_state':'open'})
					bids.customer_id.write({'bid_count':bids.customer_id.bid_count+1})	

	def installer_validate_to_open_state(self):
		for rec in self:
			rec.installer_project_state = 'open'
			rec.project_create_date = datetime.now()

			sms_text = "Your project submit and your project state to be changed"
			email_from = self.env['ir.mail_server'].sudo().search([],limit=1)
			admin_user = self.env['res.users'].sudo().search([('is_admin', '=' , True)])
			from_admin = admin_user.partner_id.email
			mail_values_user_check = {
						'subject': 'Approve Bid' ,
						'body_html': sms_text,
						'email_to':rec.supplier_customer_id.email,
						'email_cc':from_admin,
						'email_from':email_from.smtp_user,
					}
			create_and_send_email = self.env['mail.mail'].sudo().create(mail_values_user_check).sudo().send()