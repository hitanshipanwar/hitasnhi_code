from odoo import api , fields , models , tools ,_
from datetime import datetime
from odoo.modules import get_module_resource
import base64
from odoo import modules
from odoo.addons.website.models import ir_http


class MobileOTP(models.Model):
	_name = 'mobile.otp'
	_description="Mobile Otp"

	mobile_no = fields.Char("Mobile No")
	otp = fields.Char("OTP")
	state = fields.Selection([('new','NEW'),('timeout','TimeOut'), ('verify','Verify')], "State")

class MailOtp(models.Model):
	_inherit = 'mail.mail'
	otp = fields.Char("OTP")

class SaleCouponApplyCodeInherite(models.TransientModel):
	_inherit = 'sale.coupon.apply.code'
	
	def apply_coupon(self, order, coupon_code):
		print("appppppppppppppppppppppppppppppppppppppppppppppp")
		error_status = {}
		program = self.env['coupon.program'].search([('promo_code', '=', coupon_code)])
		if program:
			error_status = program._check_promo_code(order, coupon_code)
			if not error_status:
				if program.promo_applicability == 'on_next_order':
					# Avoid creating the coupon if it already exist
					if program.discount_line_product_id.id not in order.generated_coupon_ids.filtered(lambda coupon: coupon.state in ['new', 'reserved']).mapped('discount_line_product_id').ids:
						coupon = order._create_reward_coupon(program)
						return {
							'generated_coupon': {
								'reward': coupon.program_id.discount_line_product_id.name,
								'code': coupon.code,
							}
						}
				else:  # The program is applied on this order
					order._create_reward_line(program)
					order.code_promo_program_id = program
		else:
			coupon = self.env['coupon.coupon'].search([('code', '=', coupon_code)], limit=1)
			if coupon:
				error_status = coupon._check_coupon_code(order)
				if not error_status:
					order._create_reward_line(coupon.program_id)
					order.applied_coupon_ids += coupon
					if not coupon.program_id.is_bid_coupon:
						coupon.write({'state': 'used'})
			else:
				error_status = {'not_found': _('This coupon is invalid (%s).') % (coupon_code)}
		return error_status

class CouponProgram(models.Model):
	_inherit ='coupon.program'
	
	is_bid_coupon=fields.Boolean('Is BID Coupon?')
	bid_product_id=fields.Many2one('product.product',string='Bid Discout Product')

	@api.onchange('is_bid_coupon')
	def _onchange_bid_change_id(self):
		for res in self:
			bid_pro=self.env.ref('airbid_master.product_product_bid_discount').id
			if res.is_bid_coupon:
				res.bid_product_id = bid_pro
			else:
				res.bid_product_id =False

class SaleOrder(models.Model):
	_inherit = "sale.order"

	def action_confirm(self):
		res=super(SaleOrder, self).action_confirm()
		print("dddddddddddSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSS",self.applied_coupon_ids)
		if self.applied_coupon_ids.program_id.is_bid_coupon:
			print("???????????????????====+++")
			self.applied_coupon_ids.write({'state': 'new'})
		return res

	def _create_reward_line(self, program):
		website = ir_http.get_request_website()
		order=website.sale_get_order()
		values=self._get_reward_line_values(program)

		if order:
			total=0
			for line in order.order_line:
				if line.product_id.installer_solar_id:
					total=+line.product_id.list_price

		for jk in values:
			jk['price_unit']= -total
			jk['product_id']=program.bid_product_id.id
			jk['name']=_("Discount: %s", program.name),

		#print("11111111111111111111111----",[(0, False, value) for value in values])
		self.write({'order_line': [(0, False, value) for value in values]})

	def _update_existing_reward_lines(self):
		'''Update values for already applied rewards'''
		def update_line(order, lines, values):
			'''Update the lines and return them if they should be deleted'''
			lines_to_remove = self.env['sale.order.line']
			# Check commit 6bb42904a03 for next if/else
			# Remove reward line if price or qty equal to 0
			if values['product_uom_qty'] and values['price_unit']:
				lines.write(values)
			else:
				if program.reward_type != 'free_shipping':
					# Can't remove the lines directly as we might be in a recordset loop
					lines_to_remove += lines
				else:
					values.update(price_unit=0.0)
					lines.write(values)
			return lines_to_remove

		self.ensure_one()
		order = self
		applied_programs = order._get_applied_programs_with_rewards_on_current_order()
		for program in applied_programs:
			values = order._get_reward_line_values(program)
			lines = order.order_line.filtered(lambda line: line.product_id == program.discount_line_product_id)
			if program.reward_type == 'discount' and program.discount_type == 'percentage':
				lines_to_remove = lines
				# Values is what discount lines should really be, lines is what we got in the SO at the moment
				# 1. If values & lines match, we should update the line (or delete it if no qty or price?)
				# 2. If the value is not in the lines, we should add it
				# 3. if the lines contains a tax not in value, we should remove it
				for value in values:
					value_found = False
					for line in lines:
						# Case 1.
						if not len(set(line.tax_id.mapped('id')).symmetric_difference(set([v[1] for v in value['tax_id']]))):
							value_found = True
							# Working on Case 3.
							lines_to_remove -= line
							lines_to_remove += update_line(order, line, value)
							continue
					# Case 2.
					if not value_found:
						if program.is_bid_coupon:
							website = ir_http.get_request_website()
							order=website.sale_get_order()
							# values=self._get_reward_line_values(program)
							# print(type(values),"dddddddddddddddddddddddddddddd")

							if order:
								total=0
								for line in order.order_line:
									if line.product_id.installer_solar_id:
										total=+line.product_id.list_price
							# for jk in values:
							#	 print("ffffffffffffffff",jk)
							#	 jk['price_unit']= -total
							value['price_unit']=-total
							value['product_id']=program.bid_product_id.id
							value['name']=_("Discount: %s", program.name),
						order.write({'order_line': [(0, False, value)]})
				# Case 3.
				lines_to_remove.unlink()
			else:
				update_line(order, lines, values[0]).unlink()

class UserAdmin(models.Model):
	_inherit='res.users'

	is_admin = fields.Boolean(string="Admin User",default=False)
	old_password=fields.Char(string='Old password',store=True)

class forinherit(models.Model):
	_inherit='res.partner'

	is_supplier = fields.Selection([('customer','Customer'),('supplier','Supplier'),('installer','Installer')],string="Supplier")
	user_lastname = fields.Char(store=True)
	category = fields.Selection(selection=[
				('self', 'Self'),
				('company', 'Company'),
			],string="Category")
	is_check_profile = fields.Boolean('Is Check Profile')

	# Product member ship plan boolean ...........................
	
	per_bid = fields.Boolean(string="PerBid")
	per10_bid = fields.Boolean(string="10Bid")
	per20_bid = fields.Boolean(string="20Bid")
	per30_bid = fields.Boolean(string="30Bid")
	monthly_bid = fields.Boolean(string="MonthlyBid")
	bid_count = fields.Integer(string="Per Bids")
	plan_start_date = fields.Date(string="Plan start date")
	plan_end_date = fields.Date(string="Plan End date")
	old_password=fields.Char(string='Old password',store=True)
	# default image set ........................................
	def _get_default_image():
		with open(modules.get_module_resource('airbid_master', 'static/src/image', 'Download.png'),'rb') as f:
				return base64.b64encode(f.read())

	company_name = fields.Char(string="Company Name")
	abn = fields.Char(string="ABN:")
	year = fields.Selection(selection="year_selection",string="Company Established In:")
	trading_name = fields.Char(string="Trading Name")
	company_logo = fields.Binary(string="Company Logo:",default=_get_default_image())
	about_com = fields.Text(string="About Company:")

	@api.model
	def year_selection(self):
		year = 1950 
		year_list = []
		while year != (datetime.now().year)+1: 
			year_list.append((str(year), str(year)))
			year += 1
		return year_list
	
	# Directors Profile..........................
	director_fname = fields.Char(string="Director First Name")
	director_lname = fields.Char(string="Director Secound Name")
	birth_date = fields.Date(string="Date Of Birth:")
	mobile_no = fields.Char(string="Mobile No:")
	photo = fields.Binary()

	# Certificates...............................
	retailer = fields.Binary(string="CEC Retailer")
	member = fields.Binary(string="CEC member")
	iso = fields.Binary(string="ISO Certification")
	document = fields.Binary(string="Other Document")
	installation = fields.Char(string="How many installations done?")
	residential = fields.Integer(string="Residential")
	commercial = fields.Integer(string="Commercial", store=True)
	retailer_name = fields.Text(string="CEC Retailer Name")
	member_name = fields.Text(string="CEC member Name")
	iso_name = fields.Text(string="ISO Certification Name")
	document_name = fields.Text(string="Other Document Name")

	company_logo_name = fields.Text(string="Company Logo Name")
	photo_name = fields.Text(string="Photo Name")
	service_zip = fields.Text("Service Zip")

	area_operates_ids = fields.One2many('area.operates','area_operates_id',string="Area Operates In")

class AreaOperates(models.Model):
	_name = 'area.operates'
	_description = "Area Operates"

	area_operates_id = fields.Many2one('res.partner',string="Area Operates")
	city_area_name = fields.Char(string="City:")
	radius_name = fields.Integer(string="Radius(In KM):")
	zip_code = fields.Integer(string="Zip Code")

class ReportSolarSystem(models.AbstractModel):
	_name = 'report.airbid_master.notification_email_template'

	@api.model
	def _get_report_values(self, docids, data=None):
		data['record_id'] = data.get('record_id', docids)
		solar_id = self.env['solar.system'].browse(docids)
		return {
			'docs': solar_id,
		}

class ReportSolarSupplierSystem(models.AbstractModel):
	_name = 'report.airbid_master.supplier_email_notification'

	@api.model
	def _get_report_values(self, docids, data=None):
		data['result'] = data.get('result', docids)
		solar_sup_id = self.env['solar.supplier'].browse(docids)
		return {
			'docs': solar_sup_id,
		}
