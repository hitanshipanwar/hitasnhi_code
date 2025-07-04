from odoo import fields,api,models
from datetime import datetime
from odoo.modules import get_module_resource
import base64
from odoo import modules

class InstallerProfile(models.Model):
	_inherit = 'res.partner'

	
	def _get_default_image():
		with open(modules.get_module_resource('airbid_master', 'static/src/image', 'Download.png'),'rb') as f:
				return base64.b64encode(f.read())

	ins_company_name = fields.Char(string="Company Name")
	ins_abn = fields.Char(strings="ABN:")
	ins_year = fields.Selection(selection="year_selection",string="Company Established In:")
	ins_trading_name = fields.Char(string="Trading Name")
	ins_company_logo = fields.Binary(string="Company Logo:",default=_get_default_image())
	ins_about_com = fields.Text(string="About Company:")

	@api.model
	def year_selection(self):
		year = 1950 
		year_list = []
		while year != (datetime.now().year)+1: 
			year_list.append((str(year), str(year)))
			year += 1
		return year_list

	# Directors Profile....
	ins_director_fname = fields.Char(string="Director First Name")
	ins_director_lname = fields.Char(string="Director Second Name")
	ins_birth_date = fields.Date(string="Date of Birth:")
	ins_mobile_no = fields.Char(string="Mobile No:")
	ins_photo = fields.Binary()
	ins_photo_name = fields.Text(string="Photo Name")

	# Certificates.......
	ins_retailer = fields.Binary(string="CEC Retailer")
	ins_member = fields.Binary(string="CEC member")
	ins_iso = fields.Binary(string="ISO Certification")
	ins_iso_name = fields.Text(string="ISO Certification Name")
	ins_document = fields.Binary(string="Other Document")
	ins_document_name = fields.Text(string="Other Document Name")
	ins_service_zip = fields.Text("Service Zip")
	ins_residential = fields.Integer(string="Residential ?")
	ins_commercial = fields.Integer(string="Commercial ?")
	ins_member_name = fields.Text(string="CEC member Name")
	ins_retailer_name = fields.Text(string="CEC Retailer Name")
	ins_company_logo_name = fields.Text(string="Company Logo Name")
	ins_area_operates_ids = fields.One2many('area.operates','area_operates_id',string="Area Operates In")

class AreaOperates(models.Model):
	_name = 'area.operates'
	_description = "Area Operates"

	area_operates_id = fields.Many2one('res.partner',string="Area Operates")
	city_area_name = fields.Char(string="City:")
	radius_name = fields.Integer(string="Radius(In KM):")
	zip_code = fields.Integer(string="Zip Code")

