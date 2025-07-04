from random import randint
from odoo import api, fields, models,_
from odoo import http
from odoo.http import request
import json
import requests
import urllib.request
import odoo
import base64
import os
from odoo.http import request
from odoo.addons.website.controllers.main import Website
from odoo.addons.website_sale.controllers.main import WebsiteSale
from odoo.http import content_disposition, Controller, request, route
from datetime import datetime,date
from dateutil.relativedelta import relativedelta
from operator import itemgetter
import ast
from odoo.addons.payment.controllers.portal import PaymentProcessing


class ChangeUserProfile(Controller):	
	@http.route('/user', type='http', auth="public", website=True, sitemap=True)
	def user_detail_website(self,**post):
		user_id = request.env.user.partner_id
		if post or post.get('profile_supp'):
			if not post.get('current_paswd'):
				image = base64.encodestring(post.get('profile_supp').read()) or user_id.image_1920
			else:
				image = user_id.image_1920
		else:
			image = user_id.image_1920

		if post.get('is_detele') == 'true':
			image=False
		# else:
		# 	image_1920=base64.encodestring(post.get('profile_supp').read()) or user_id.image_1920

		user_id.sudo().write({'name':post.get('name') or request.env.user.name,
			'user_lastname':post.get('user_lastname') or request.env.user.user_lastname,
			'image_1920':image,
			'email':post.get('login') or request.env.user.email,
			'phone':post.get('phone') or request.env.user.phone})

		if post.get('current_paswd'):
			request.env['res.users'].change_password(post.get('current_paswd'), post.get('new_paswd'))
		
		return request.render('airbid_master.user_profile_form',{"menu_customer_user":True})

# class WebsiteSalearbid(WebsiteSale):
# 	@http.route(['/shop/confirmation'], type='http', auth="public", website=True, sitemap=False)
# 	def payment_confirmation(self, **post):
# 		print("gggggggggggggggggggggggggggggg")
# 		""" End of checkout process controller. Confirmation is basically seing
# 		the status of a sale.order. State at this point :

# 		 - should not have any context / session info: clean them
# 		 - take a sale.order id, because we request a sale.order and are not
# 		   session dependant anymore
# 		"""
# 		sale_order_id = request.session.get('sale_last_order_id')
# 		if sale_order_id:
# 			order = request.env['sale.order'].sudo().browse(sale_order_id)
# 			for line in sale_order_id:
# 				print("??????????????????????????????????????????????????",line.product_id.installer_solar_id)
# 				if line.product_id.installer_solar_id:
# 					installer_solar_id.update({"installer_project_state":"draft"})
# 			return request.render("website_sale.confirmation", {'order': order})
# 		else:
# 			return request.redirect('/shop')

class WebsiteModule(Website):

	URL = 'https://cellcast.com.au/api/v3/send-sms'
	
	@http.route('/mobile/verify', auth='public', type='json', website=True,  csrf=False)
	def mobile_verify_website(self,mobile_num):
		otp = randint(100000, 999999)

		api_key = 'CELLCASTcc004b5a13c75eb8515e814cb9fc28d1'
		sms_text = str(otp)+" is your AIRBID code. Do not share the OTP with anyone."
		headers = {
				'APPKEY': 'CELLCASTcc004b5a13c75eb8515e814cb9fc28d1',
				'Content-Type': "application/json",
				'Cache-Control': "no-cache",
			}
		urls = "https://cellcast.com.au/api/v3/send-sms?sms_text="+str(sms_text)+"&numbers="+mobile_num+"&source=odoo&custom_string=Odoo Signup SMS"
		request.env['mobile.otp'].sudo().create({'otp':otp, 'state':'new', 'mobile_no':mobile_num})
		response = requests.request("POST", urls,headers=headers)
		print("SMS otpppppppppppppppp",sms_text)
		if response.status_code == 200:
			request.session['otp'] = str(otp)
			return str(otp)			
		return True


	@http.route('/verifyOTP', type='json', auth="public", website=True)
	def check_otp(self, otp, mobile_num):
		if otp and mobile_num:
			mobile_otp_rec = request.env['mobile.otp'].sudo().search([("state","=","new"),
				('mobile_no','=',mobile_num), ('otp','=', otp)])
			if mobile_otp_rec:
				mobile_otp_rec.write({'state':"verify"})
				return True
			else:
				return False


	@http.route('/email/verify', auth='public', type='json', website=True,  csrf=False)
	def email_verify_website(self,email_id):
		otp = randint(100000, 999999)
		sms_text = str(otp)+" is your AIRBID code. Do not share the OTP with anyone."
		print("EMAl otpppppppppppppppp",sms_text)
		email_from = request.env['ir.mail_server'].sudo().search([],limit=1)
		mail_values_user_check = {
					'subject': 'Email Verification' ,
					'body_html': sms_text,
					'email_to':email_id,
					'email_from':email_from.smtp_user,
					'otp':otp
				}
		create_and_send_email = request.env['mail.mail'].sudo().create(mail_values_user_check).sudo().send()
		return True

	@http.route('/verifyemailOTP', type='json', auth="public", website=True)
	def check_email_otp(self, otp, email_id):
		if otp and email_id:
			email_otp_rec = request.env['mail.mail'].sudo().search([('email_to','=',email_id),('otp','=',otp)])
			return True
		else:
			return False

class WebsiteSaleController(http.Controller):
	@http.route('/project/data', auth='public', type='http',website=True)
	def project_detail_website(self,**post):
		return request.render('airbid_master.solar_system_form_view',{})

	@http.route('/my/project', auth='public', type='http',website=True)
	def my_project_website(self,**post):
		user_id = request.env.user.partner_id
		if post.get('sort'):
			data = request.env['solar.system'].sudo().search([('customer_id', '=', user_id.id)],order="project_create_date asc")
		else:
			data = request.env['solar.system'].sudo().search([('customer_id', '=', user_id.id)],order="project_create_date desc")
		return request.render('airbid_master.my_project_form',{"menu_customer_project":True,"data":data,'record_id':data,'rec_id':data})

	@http.route('/address/data', auth='public', type='http',website=True)
	def project_address_website(self,record_id=None,*args,**post):
		model_id = request.env['solar.system']
		user_id = request.env.user.partner_id
		countries = request.env['res.country'].sudo().search([])
		states = request.env['res.country.state'].sudo().search([('country_id.code','ilike','AU')])
		if record_id:
			rec_id = request.env['solar.system'].search([('id','=',record_id)])
			record_id = rec_id
			request.session['address'] = record_id.multiple_address
			address = record_id.multiple_address
		else:
			request.session['address'] = ''
			record_id = model_id.sudo().create({'customer_id' : user_id.id})
			rec_id = record_id
		
		return request.render('airbid_master.customer_address_form',{'record_id':record_id.id,'states': states,'rec_id':rec_id})

	@http.route(["/solar/system"], auth='public', type='http',website=True)
	def solar_system_form(self,record_id=None,**post):
		if post:
			state_id = request.env['res.country.state'].sudo().search([('code','ilike',post.get('state')),('country_id','=','AU')],limit=1)
			record_id = request.env['solar.system'].search([('id','=',record_id)])
			record_id.write({'customer_project_name': post.get('project_name') or record_id.customer_project_name,
				'email_id':post.get('customer_email') or record_id.email_id,
				'phone':post.get('phone') or record_id.phone,
				'multiple_address':post.get('multiple_address') or record_id.multiple_address,
				'street':post.get('address_line_1') or record_id.street,
				'house_number_or_name':post.get('address_line_2') or record_id.house_number_or_name,
				'state_id':state_id.id or record_id.state_id,
				'city':post.get('customer_city') or record_id.city,
				'zip':post.get('customer_zip') or record_id.zip,
				'let':post.get('let_address') or record_id.let,
				'leng':post.get('long_address') or record_id.leng
			})
		
		else:
			state_id = {}
			record_id = request.env['solar.system'].search([('id','=',record_id)])
		
		if record_id:
			request.session['address'] = record_id.multiple_address
			address = record_id.multiple_address
		else:
			request.session['address'] = ''
		#request.session['address'] = record_id.multiple_address

		return request.render('airbid_master.customer_project_form',{'record_id':record_id.id,'rec_id':record_id,'long_address':post.get('long_address'),'let_address':post.get('let_address'),'address':record_id.multiple_address})

	@http.route('/solar/shadding', auth='public', type='http',website=True)
	def solar_system_form_que2(self,**post):
		record_id = request.env['solar.system'].search([('id','=',post.get('record_id'))])
		record_id.write({'property_option_new': post.get('property') or record_id.property_option_new})
		return request.render('airbid_master.customer_project_form_que2',{'record_id':record_id.id,'rec_id':record_id})

	@http.route('/solar/systemhave', auth='public', type='http',website=True)
	def solar_system_form_que3(self,*args,**post):
		record_id = request.env['solar.system'].search([('id','=',post.get('record_id'))])
		record_id.write({'shading_issue': post.get('shadding') or record_id.shading_issue})
		return request.render('airbid_master.customer_project_form_que3',{'record_id':record_id.id,'rec_id':record_id})
		
	@http.route('/remove/panels', auth='public', type='http',website=True)
	def solar_system_form_removepanel(self,*args,**post):
		record_id = request.env['solar.system'].search([('id','=',post.get('record_id'))])
		record_id.write({'shading_issue': post.get('shadding') or record_id.shading_issue})
		return request.render('airbid_master.customer_project_form_remove_panel',{'record_id':record_id.id,'rec_id':record_id})

	@http.route('/existing/panels', auth='public', type='http',website=True)
	def customer_project_form_existingpanel(self,*args,**post):
		record_id = request.env['solar.system'].search([('id','=',post.get('record_id'))])
		record_id.write({'remove_panels': post.get('remove_panels') or record_id.remove_panels})
		if post.get('remove_panels')=='yes' or record_id.remove_panels == 'yes':
			return request.render('airbid_master.customer_project_form_existing_panels',{'record_id':record_id.id,'rec_id':record_id})
		else:
			return request.render('airbid_master.customer_project_form_upgrade_system',{'record_id':record_id.id,'rec_id':record_id})

	@http.route('/add/panels', auth='public', type='http',website=True)
	def solar_system_form_addpanels(self,*args,**post):
		record_id = request.env['solar.system'].search([('id','=',post.get('record_id'))])
		record_id.write({'no_panels': post.get('panels') or record_id.no_panels})
		return request.render('airbid_master.customer_project_form_add_panels',{'record_id':record_id.id,'rec_id':record_id})

	@http.route('/upgrade/system', auth='public', type='http',website=True)
	def solar_system_form_upgrade(self,*args,**post):
		record_id = request.env['solar.system'].search([('id','=',post.get('record_id'))])
		record_id.write({'shading_issue': post.get('shadding') or record_id.shading_issue})
		return request.render('airbid_master.customer_project_form_upgrade_system',{'record_id':record_id.id,'rec_id':record_id})

	@http.route('/battery/storage', auth='public', type='http',website=True)
	def solar_system_form_battery(self,*args,**post):
		record_id = request.env['solar.system'].search([('id','=',post.get('record_id'))])
		record_id.write({'add_panels': post.get('add_panels') or record_id.add_panels,
						'add_battery': post.get('add_battery') or record_id.add_battery,
						'add_battery_new': post.get('add_battery') or record_id.add_battery_new,
						'existing_solar': post.get('existing_solar') or record_id.existing_solar,
						'inverter_brand': post.get('inverter_brand') or record_id.inverter_brand,
						'inverter_phase': post.get('inverter_phase') or record_id.inverter_phase,
						'inverter_capacity': post.get('inverter_capacity') or record_id.inverter_capacity,
						'upgrade_system': post.get('upgrade_system') or record_id.upgrade_system,
						'storage_size': post.get('storage_size') or record_id.storage_size})
		if post.get('upgrade_system')=='yes' or record_id.upgrade_system == 'yes':
			return request.render('airbid_master.customer_project_form_que4',{'record_id':record_id.id,'rec_id':record_id})
		elif post.get('upgrade_system')=='no' or post.get('add_panels')=='no' or record_id.upgrade_system == 'no' or record_id.add_panels == 'no':
			return request.render('airbid_master.customer_project_form_battery_storage',{'record_id':record_id.id,'rec_id':record_id})
		elif post.get('add_panels')=='yes' or record_id.add_panels == 'yes':
			img_data = request.env['image.selection'].sudo().search([('ques_id','=','five')])
			return request.render('airbid_master.customer_project_form_que5',{'record_id':record_id.id,'rec_id':record_id,'img_data':img_data})
		
	@http.route('/solar/property', auth='public', type='http',website=True)
	def solar_system_form_que4(self,*args,**post):
		record_id = request.env['solar.system'].search([('id','=',post.get('record_id'))])
		record_id.write({'solar_system': post.get('question3') or record_id.solar_system})
		if post.get('question3')=='yes' or record_id.solar_system == 'yes':
			return request.render('airbid_master.customer_project_form_remove_panel',{'record_id':record_id.id,'rec_id':record_id})
		else:
			return request.render('airbid_master.customer_project_form_que4',{'record_id':record_id.id,'rec_id':record_id})

	@http.route('/panels/type', auth='public', type='http',website=True)
	def solar_system_form_que5(self,*args,**post):
		record_id = request.env['solar.system'].search([('id','=',post.get('record_id'))])
		record_id.write({'property_select': post.get('question4') or record_id.property_select,
						'add_battery': post.get('add_battery') or record_id.add_battery,
						'add_battery_new': post.get('add_battery') or record_id.add_battery_new,
						'existing_solar': post.get('existing_solar') or record_id.existing_solar,
						'inverter_brand': post.get('inverter_brand') or record_id.inverter_brand,
						'inverter_phase': post.get('inverter_phase') or record_id.inverter_phase,
						'inverter_capacity': post.get('inverter_capacity') or record_id.inverter_capacity,
						'storage_size': post.get('storage_size') or record_id.storage_size})
		img_data = request.env['image.selection'].sudo().search([('ques_id','=','five')])
		return request.render('airbid_master.customer_project_form_que5',{'record_id':record_id.id,'rec_id':record_id,'img_data':img_data})

	@http.route('/inverter/type', auth='public', type='http',website=True)
	def solar_system_form_que6(self,*args,**post):
		record_id = request.env['solar.system'].search([('id','=',post.get('record_id'))])
		record_id.write({'solar_type': post.get('solar_panels') or record_id.solar_type,
			'type_box': post.get('panel_brand') or record_id.type_box})
		img_data = request.env['image.selection'].sudo().search([('ques_id','=','six')])
		return request.render('airbid_master.customer_project_form_que6',{'record_id':record_id.id,'rec_id':record_id,'img_data':img_data})

	@http.route('/property/type', auth='public', type='http',website=True)
	def solar_system_form_que7(self,*args,**post):
		record_id = request.env['solar.system'].search([('id','=',post.get('record_id'))])
		record_id.write({'inverter_type': post.get('inverter_type') or record_id.inverter_type,
			'brand_box': post.get('inverter_brand') or record_id.brand_box,
			'battery_backup': post.get('battery_backup') or record_id.battery_backup,
			'backup_box': post.get('battery_box') or record_id.backup_box})
		img_data = request.env['image.selection'].sudo().search([('ques_id','=','seven')])
		return request.render('airbid_master.customer_project_form_que7',{'record_id':record_id.id,'rec_id':record_id,'img_data':img_data})

	@http.route('/story/number', auth='public', type='http',website=True)
	def solar_system_form_que8(self,*args,**post):
		record_id = request.env['solar.system'].search([('id','=',post.get('record_id'))])
		record_id.write({'property_type': post.get('property_type') or record_id.property_type})
		img_data = request.env['image.selection'].sudo().search([('ques_id','=','eight')])
		return request.render('airbid_master.customer_project_form_que8',{'record_id':record_id.id,'rec_id':record_id,'img_data':img_data})

	@http.route('/roof/type', auth='public', type='http',website=True)
	def solar_system_form_que9(self,*args,**post):
		record_id = request.env['solar.system'].search([('id','=',post.get('record_id'))])
		record_id.write({'story_no': post.get('story_no') or record_id.story_no})
		img_data = request.env['image.selection'].sudo().search([('ques_id','=','nine')])
		return request.render('airbid_master.customer_project_form_que9',{'record_id':record_id.id,'rec_id':record_id,'img_data':img_data})

	@http.route('/electricity/pay', auth='public', type='http',website=True)
	def solar_system_form_que10(self,*args,**post):
		record_id = request.env['solar.system'].search([('id','=',post.get('record_id'))])
		record_id.write({'roof_type': post.get('roof') or record_id.roof_type,
						'roof_text_box': post.get('roof_text_box') or record_id.roof_text_box})
		return request.render('airbid_master.customer_project_form_que10',{'record_id':record_id.id,'rec_id':record_id})

	@http.route('/solar/size', auth='public', type='http',website=True)
	def solar_system_form_que11(self,*args,**post):
		record_id = request.env['solar.system'].search([('id','=',post.get('record_id'))])
		record_id.write({'pay_quarterly': post.get('electricity_pay') or record_id.pay_quarterly})
		return request.render('airbid_master.customer_project_form_que11',{'record_id':record_id.id,'rec_id':record_id})

	@http.route('/cash/finance', auth='public', type='http',website=True)
	def solar_system_form_que12(self,*args,**post):
		record_id = request.env['solar.system'].search([('id','=',post.get('record_id'))])
		record_id.write({'solar_size': post.get('system_size') or record_id.solar_size,
						'add_battery': post.get('add_battery') or record_id.add_battery,
						'add_battery_new': post.get('add_battery') or record_id.add_battery_new,
						'existing_solar': post.get('existing_solar') or record_id.existing_solar,
						'inverter_brand': post.get('inverter_brand') or record_id.inverter_brand,
						'inverter_phase': post.get('inverter_phase') or record_id.inverter_phase,
						'inverter_capacity': post.get('inverter_capacity') or record_id.inverter_capacity,
						'storage_size': post.get('storage_size') or record_id.storage_size,
						'specify_box': post.get('systemsize') or record_id.specify_box})
		return request.render('airbid_master.customer_project_form_que12',{'record_id':record_id.id,'rec_id':record_id})

	@http.route('/comment/box', auth='public', type='http',website=True)
	def solar_system_form_que13(self,*args,**post):
		record_id = request.env['solar.system'].search([('id','=',post.get('record_id'))])
		record_id.write({'cash_fin': post.get('payment') or record_id.cash_fin})
		return request.render('airbid_master.customer_project_form_que13',{'record_id':record_id.id,'rec_id':record_id})


	@http.route('/upload/documents', auth='public', type='http',website=True)
	def solar_system_form_que14(self,*args,**post):
		record_id = request.env['solar.system'].search([('id','=',post.get('record_id'))])
		record_id.write({'comment_box': post.get('comment') or record_id.comment_box})
		return request.render('airbid_master.customer_project_form_que14',{'record_id':record_id.id,'rec_id':record_id})

	@http.route('/project/details', auth='public', type='http',website=True)
	def review_project_page(self, **post):
		record_id = request.env['solar.system'].sudo().search([('id','=',post.get('record_id'))])
		if record_id.add_battery == 'yes' or record_id.add_battery_new == 'yes':
			record_id.write({'house':base64.encodestring(post.get('house_attachment').read()) or record_id.house,
						'meter_box':base64.encodestring(post.get('image_of_meter_box').read()) or record_id.meter_box,
						'inverter_wall':base64.encodestring(post.get('inverter_wall').read()) or record_id.inverter_wall,
						'meter_box_2':base64.encodestring(post.get('meter_box_2').read()) or record_id.meter_box_2,
						'electricity_bill':base64.encodestring(post.get('image_of_electricity_bill').read()) or record_id.electricity_bill,
						'house_name':post.get('house_name')or record_id.house_name,
						'roof_name':post.get('roof_name')or record_id.roof_name,
						'meter_name':post.get('meter_name')or record_id.meter_name,
						'inverter_wall_name':post.get('inverter_wall_name')or record_id.inverter_wall_name,
						'meter_box_2_name':post.get('meter_box_2_name')or record_id.meter_box_2_name,
						'electricity_bill_name':post.get('electricity_bill_name')or record_id.electricity_bill_name,})
		else:
			record_id.write({'house':base64.encodestring(post.get('house_attachment').read()) or record_id.house,
						'roof':base64.encodestring(post.get('image_of_roof').read()) or record_id.roof,
						'meter_box':base64.encodestring(post.get('image_of_meter_box').read()) or record_id.meter_box,
						'electricity_bill':base64.encodestring(post.get('image_of_electricity_bill').read()) or record_id.electricity_bill,
						'house_name':post.get('house_name')or record_id.house_name,
						'roof_name':post.get('roof_name')or record_id.roof_name,
						'meter_name':post.get('meter_name')or record_id.meter_name,
						'inverter_wall_name':post.get('inverter_wall_name')or record_id.inverter_wall_name,
						'meter_box_2_name':post.get('meter_box_2_name')or record_id.meter_box_2_name,
						'electricity_bill_name':post.get('electricity_bill_name') or record_id.electricity_bill_name})

		img_data = request.env['image.selection'].sudo().search([])
		return request.render('airbid_master.project_review_page',{'record_id':record_id,'img_data':img_data,'rec_id':record_id})

	@http.route('/submit/data', auth='public', type='http',website=True)
	def submit_website(self,**post):
		record_id = request.env['solar.system'].search([('id','=',post.get('record_id'))])
		pdf = request.env.ref('airbid_master.action_report_solar_system').sudo()._render_qweb_pdf([record_id.id])[0]
		
		# if pdf_data:
		attachment_value = {
			'name': 'Solar Information',
			'datas': base64.encodebytes(pdf),
			'res_model': 'solar.system',
			'res_id': record_id.id
		}
		# Create Attachment
		attchment_email = request.env['ir.attachment'].sudo().create(attachment_value)

		record_id.update({"customer_project_state":"draft"})
		content = request.env.user.name+" is create a new project"
		email_from = request.env['ir.mail_server'].sudo().search([],limit=1)
		admin_user = request.env['res.users'].sudo().search([('is_admin','=',True)],limit=1)
		mail_values_user_check = {
					'subject': 'Create A New Project' ,
					'body_html': content,
					'email_to':email_from.smtp_user,
					'email_from': request.env.user.login,
					'email_cc':admin_user.partner_id.email,
					'attachment_ids': [(4, attchment_email.id)]
				}
		create_and_send_email = request.env['mail.mail'].sudo().create(mail_values_user_check).sudo().send()
		return request.render('airbid_master.submit_project_form',{"ref_no":record_id.sequence_pro_no})

	@http.route('/bid/submit', auth='public', type='http',website=True)
	def bid_submit_website(self,**post):
		user_id = request.env.user.partner_id
		user_id.write({'bid_count':user_id.bid_count-1})
		record_id = request.env['solar.supplier']
		project_id = request.env['solar.system'].sudo().search([('id','=', post.get('record_id'))])
		vals = {
			'solar_project_id':int(post.get('record_id')) if post.get('record_id') else False,
			'supplier_id' : user_id.id,
			'system_size': post.get('system'),
			'bid_desc': post.get('supplier_choose_supplier_comment'),
			'panels_no': post.get('no_panel'),
			'panels_brand': post.get('brand_panel'),
			'power_class': post.get('power'),
			'made_country': post.get('country_panel'),
			'solar_type': post.get('type_panel'),
			'manu_year': post.get('manu_panel'),
			'per_year': post.get('panel_per'),
			'inverter_brand': post.get('brand_inverter'),
			'inverter_size': post.get('size_int'),
			'manu_country': post.get('country_inverter'),
			'warranty': post.get('manu_inverter'),
			'work_warranty': post.get('inverter_per'),
			'full_price': post.get('price'),
			'final_price': post.get('price_finance'),
			'months': post.get('months'),
			'project_state':'inprogress',
			
			'battery_size_kwh':post.get('battery_system_size_name'),

			'inverter_two_option':post.get('pets'),

			'inbuilt_product_Brand':post.get('inbuilt_product_brand'),
			'inbuilt_product_model_no':post.get('inbuilt_product_model_no'),
			'inbuilt_product_warranty':post.get('inbuilt_product_warranty'),
			'inbuilt_made_in':post.get('inbuilt_made_in'),

			'supplied_product_Brand':post.get('supplied_sepretly_brand'),
			'supplied_product_model_no':post.get('supplied_sepretly_size'),
			'supplied_product_warranty':post.get('supplied_sepretly_inverter_warranty'),
			'supplied_made_in':post.get('supplied_sepretly_made_in'),

			'battery_brand':post.get('supplied_sepretly_battery_brand'),
			'battery_model_no':post.get('supplied_sepretly_battery_model'),
			'battery_warranty':post.get('supplied_sepretly_battery_warranty'),
			'battery_supplied_made_in':post.get('supplied_sepretly_battery_made_in'),
		}

		result = record_id.sudo().create(vals)

		count = post.get('count')
		for i in range(1,int(count)+1):
			name = 'file_'+ str(i)
			f_name = 'file_name_'+ str(i)

			battery_name = 'battery_name_'+ str(i)
			battery_model = 'battery_model_'+ str(i)
			battery_made_in = 'battery_made_in_'+ str(i)
			battery_warranty = 'battery_warranty_'+ str(i)

			file = post.get(name)
			file_name = post.get(f_name)

			battery_name_name = post.get(battery_name)
			battery_model_name = post.get(battery_model)
			battery_made_in_name = post.get(battery_made_in)
			battery_warranty_name = post.get(battery_warranty)

			if battery_name_name:
				attachment_value_img = {
					# 'name': file_name,
					'battery_attch_img':file,
					'battery_product_Brand':battery_name_name,
					'battery_product_model_no':battery_model_name,
					'battery_made_in':battery_made_in_name,
					'battery_product_warranty':battery_warranty_name,
					# 'res_model': 'solar.supplier',
					'battery_attchment_id': result.id,
					}
				# Create Attachment
				attachment_id =  request.env['solar.supplier.battery'].sudo().create(attachment_value_img)

		# INVERTER ++++++++++++++
		count_inv = post.get('count_inv')
		for i in range(1,int(count_inv)+1):
			inv_name = 'inv_file_'+ str(i)
			inv_f_name = 'inv_file_name_'+ str(i)

			inverter_name = 'inverter_name_'+ str(i)
			inverter_model = 'inverter_model_'+ str(i)
			inverter_made_in = 'inverter_made_in_'+ str(i)
			inverter_warranty = 'inverter_warranty_'+ str(i)

			inv_file = post.get(inv_name)
			inv_file_name = post.get(inv_f_name)

			inverter_name_name = post.get(inverter_name)
			inverter_model_name = post.get(inverter_model)
			inverter_made_in_name = post.get(inverter_made_in)
			inverter_warranty_name = post.get(inverter_warranty)

			if inverter_name_name:
				inverter_value_img = {
					'inverter_attch_img':file,
					'inverter_product_Brand':inverter_name_name,
					'inverter_product_model_no':inverter_model_name,
					'inverter_made_in':inverter_made_in_name,
					'inverter_product_warranty':inverter_warranty_name,
					'inverter_attchment_id': result.id,
					}
				# Create Attachment
				attachment_id =  request.env['solar.supplier.inverter'].sudo().create(inverter_value_img)

		# Inbuilt ++++++++++++++
		count_inbuilt = post.get('count_inbuilt')
		for i in range(1,int(count_inbuilt)+1):
			inbuilt_name = 'inbuilt_file_'+ str(i)
			inbuilt_f_name = 'inbuilt_file_name_'+ str(i)
			inbuilt_file = post.get(inbuilt_name)
			inbuilt_file_name = post.get(inbuilt_f_name)
			if inbuilt_file:
				attachment_inbuilt_value_img = {
					'name': inbuilt_file_name,
					'datas':inbuilt_file,
					# 'res_model': 'solar.supplier',
					'inbuilt_in_box_attchment_id': result.id,
					}
				# Create Attachment
				attachment_id =  request.env['ir.attachment'].sudo().create(attachment_inbuilt_value_img)

		# Supplied sepretly ++++++++++++++
		count_supplied_sepretly = post.get('count_supplied_sepretly')
		for i in range(1,int(count_supplied_sepretly)+1):
			supplied_sepretly_name = 'supplied_sepretly_file_'+ str(i)
			supplied_sepretly_f_name = 'supplied_sepretly_file_name_'+ str(i)
			supplied_sepretly_file = post.get(supplied_sepretly_name)
			supplied_sepretly_file_name = post.get(supplied_sepretly_f_name)
			if supplied_sepretly_file:
				attachment_supplied_sepretly_value_img = {
					'name': supplied_sepretly_file_name,
					'datas':supplied_sepretly_file,
					'supplied_sepretly_attchment_id': result.id,
					}
				# Create Attachment
				attachment_id =  request.env['ir.attachment'].sudo().create(attachment_supplied_sepretly_value_img)

		# Supplied sepretly Battary++++++++++++++
		count_supplied_sepretly_battery = post.get('count_supplied_sepretly_battery')
		for i in range(1,int(count_supplied_sepretly_battery)+1):
			supplied_sepretly_battary_name = 'supplied_sepretly_battery_file_'+ str(i)
			supplied_sepretly_battary_f_name = 'supplied_sepretly_battery_file_name_'+ str(i)
			supplied_sepretly_file_battary = post.get(supplied_sepretly_battary_name)
			supplied_sepretly_file_battary_name = post.get(supplied_sepretly_battary_f_name)
			if supplied_sepretly_file_battary:
				attachment_supplied_sepretly_battary_value_img = {
					'name': supplied_sepretly_file_battary_name,
					'datas':supplied_sepretly_file_battary,
					'battery_supplied_sepretly_attchment_id': result.id,
				}
				# Create Attachment
				attachment_id =  request.env['ir.attachment'].sudo().create(attachment_supplied_sepretly_battary_value_img)

		# Supplied sepretly Battary++++++++++++++
		count_how_it_works = post.get('count_how_it_works')
		for i in range(1,int(count_how_it_works)+1):
			how_it_work_name = 'how_it_work_file_'+ str(i)
			how_it_work_f_name = 'how_it_work_file_name_'+ str(i)
			how_it_work = post.get(how_it_work_name)
			how_it_work_name = post.get(how_it_work_f_name)
			if how_it_work:
				attachment_how_it_work_value_img = {
					'name': how_it_work_name,
					'datas':how_it_work,
					'how_it_work_attchment_id': result.id,
				}
				# Create Attachment
				attachment_id =  request.env['ir.attachment'].sudo().create(attachment_how_it_work_value_img)										


		content = "You are biding on the "+project_id.customer_project_name+" project"
		result.solar_project_id.sudo().write({'supplier_project_state':'inprogress','suppiler_status_ids':[(6,0, result.ids)]})
		# result.solar_project_id.sudo().write({})[(4, attchment_email.id)],

		pdf = request.env.ref('airbid_master.action_report_supplier_system').sudo()._render_qweb_pdf([result.id])[0]
		
		# if pdf_data:
		attachment_value = {
			'name': 'supplier Information',
			'datas': base64.encodebytes(pdf),
			'res_model': 'solar.supplier',
			'res_id': result.id
		}
		# Create Attachment
		attchment_email = request.env['ir.attachment'].sudo().create(attachment_value)
		admin_user = request.env['res.users'].sudo().search([('is_admin','=',True)],limit=1)

		mail_values_user_check = {
					'subject': 'Supplier Bid Question' ,
					'body_html': "<div>%s</div>" %(content),
					'email_to': request.env.user.partner_id.email,
					'email_cc':admin_user.partner_id.email,
					'attachment_ids': [(4, attchment_email.id)]
				}
		create_and_send_email = request.env['mail.mail'].sudo().create(mail_values_user_check).sudo().send()
		return request.render('airbid_master.submit_bid_form',{"ref_sup_no":result.sequence_no})


	@http.route('/supplier/bid/review', auth='public', type='http',website=True)
	def supplier_review_template(self,**post):

		area_operates_counter = post.get('battery_information_count')
		if area_operates_counter:
			all_doc_attachment = []
			att_img = []
			for d in range(1,int(area_operates_counter) + 1):
				battery_name = post.get("battery_information_brand"+str(d))
				battery_model = post.get("battery_information_model"+str(d))
				battery_made_in = post.get("battery_information_made_in"+str(d))
				battery_warranty = post.get("battery_information_product_warranty"+str(d))
				# BATTERY ATTCHMENT
				attached_files = request.httprequest.files.getlist('battery_information_product_datasheet_img'+str(d))
				for file in attached_files:
					attachment_value = {
						'name': file.filename,
						'datas': base64.encodebytes(file.read()),
						'battery_name':battery_name,
						'battery_model':battery_model,
						'battery_made_in':battery_made_in,
						'battery_warranty':battery_warranty,
						}
					att_img.append(attachment_value)		
			post.update({'attached_files':att_img,
						})
		# BATTERY ATTCHMENT END

		# INVERTER ATT
		inventor_area_operates_counter = post.get('inventor_area_operates_counter')
		if inventor_area_operates_counter:
			att_inverter_img = []
			for d in range(1,int(inventor_area_operates_counter) + 1):
				inverter_name = post.get("supllier_inverter_brand"+str(d))
				inverter_model = post.get("supllier_inverter_size"+str(d))
				inverter_made_in = post.get("made_in_sup"+str(d))
				inverter_warranty = post.get("supllier_inverter_warranty"+str(d))
				# BATTERY ATTCHMENT
				attached_inverter_files = request.httprequest.files.getlist('attchment_photo_multi_inverter'+str(d))
				for file in attached_inverter_files:
					attachment_inverter_value = {
						'name': file.filename,
						'datas': base64.encodebytes(file.read()),
						'inverter_name':inverter_name,
						'inverter_model':inverter_model,
						'inverter_made_in':inverter_made_in,
						'inverter_warranty':inverter_warranty,
						}
					att_inverter_img.append(attachment_inverter_value)		
			post.update({'attached_inverter_files':att_inverter_img,
						})

		# Inbuilt in box INVERTER ATTCHMENT 
		attached_inbuilt_files = request.httprequest.files.getlist('inbuilt_attchment_photo_multi')
		att_inbuilt_img = []
		for file in attached_inbuilt_files:
			attachment_inbuilt_value = {
				'name': file.filename,
				'datas': base64.encodebytes(file.read()),
				}
			att_inbuilt_img.append(attachment_inbuilt_value)	
		post.update({'attached_inbuilt_files':att_inbuilt_img,'attached_inbuilt_files_img':attached_inbuilt_files})
		# Inbuilt in box INVERTER ATTCHMENT END

		# Supplied sepretly ++++++++++
		attached_sepretly_files = request.httprequest.files.getlist('supplied_sepretly_attchment_photo_multi')
		att_sepretly_img = []
		for file in attached_sepretly_files:
			attachment_sepretly_value = {
				'name': file.filename,
				'datas': base64.encodebytes(file.read()),
				}
			att_sepretly_img.append(attachment_sepretly_value)	
		post.update({'attached_sepretly_files':att_sepretly_img,'attached_sepretly_files_img':attached_sepretly_files})
		# Supplied sepretly end++++++++++

		# Supplied sepretly ++++++++++
		attached_sepretly_battery_files = request.httprequest.files.getlist('supplied_sepretly_battery_datasheet')
		att_sepretly_battary_img = []
		for file in attached_sepretly_battery_files:
			attachment_sepretly_battary_value = {
				'name': file.filename,
				'datas': base64.encodebytes(file.read()),
				}
			att_sepretly_battary_img.append(attachment_sepretly_battary_value)	
		post.update({'attached_sepretly_battery_files':att_sepretly_battary_img,'attached_sepretly_battery_files_img':attached_sepretly_battery_files})
		# Supplied sepretly end++++++++++

		# Supplied sepretly ++++++++++
		attached_how_it_work_files = request.httprequest.files.getlist('how_it_look_attchment_photo_multi')
		att_how_it_work_img = []
		for file in attached_how_it_work_files:
			attachment_how_it_work_value = {
				'name': file.filename,
				'datas': base64.encodebytes(file.read()),
				}
			att_how_it_work_img.append(attachment_how_it_work_value)	
		post.update({'attached_how_it_work_files':att_how_it_work_img,'attached_how_it_work_files_img':attached_how_it_work_files})
		# Supplied sepretly end++++++++++

		post = dict(post)

		record_id = request.env['solar.system'].sudo().search([('id','=',post.get('record_id'))])
		return request.render('airbid_master.bid_review_template',{'data':post,'record_id':record_id})
	
	@http.route('/supplier/edit/bid', auth='public', type='http',website=True)
	def supplier_edit(self,bid_id=None,**post):
		record_id = request.env['solar.system'].sudo().search([('id','=',post.get('record_id'))])
		bid_data = request.env['solar.supplier'].sudo().search([('supplier_id','=',request.env.user.partner_id.id),('solar_project_id','=',int(bid_id))])
		return request.render('airbid_master.supplier_edit_bid_detail',{'record_id':record_id,'bid_data':bid_data})


	@http.route('/edit/bid', auth='public', type='http',website=True)
	def edit_bid_website(self,**post):
		user_id = request.env.user.partner_id
		record_id = request.env['solar.supplier']
		if post.get('bid_id'):
			result = record_id.search([('id','=',post.get('bid_id'))])
			vals = {
				'system_size': post.get('system'),
				'bid_desc': post.get('supplier_choose_supplier_comment'),
				'panels_no': post.get('no_panel'),
				'panels_brand': post.get('brand_panel'),
				'power_class': post.get('power'),
				'made_country': post.get('country_panel'),
				'solar_type': post.get('type_panel'),
				'manu_year': post.get('manu_panel'),
				'per_year': post.get('panel_per'),
				'inverter_brand': post.get('brand_inverter'),
				'inverter_size': post.get('size_int'),
				'manu_country': post.get('country_inverter'),
				'warranty': post.get('manu_inverter'),
				'work_warranty': post.get('inverter_per'),
				'full_price': post.get('price'),
				# 'batt_full_price': post.get('batt_price'),
				'final_price': post.get('price_finance'),
				'months': post.get('months'),
				'project_state':'inprogress',

				'battery_size_kwh':post.get('battery_system_size_name'),
				'inverter_two_option':post.get('pets'),

				'inbuilt_product_Brand':post.get('inbuilt_product_brand'),
				'inbuilt_product_model_no':post.get('inbuilt_product_model_no'),
				'inbuilt_product_warranty':post.get('inbuilt_product_warranty'),
				'inbuilt_made_in':post.get('inbuilt_made_in'),

				'supplied_product_Brand':post.get('supplied_sepretly_brand'),
				'supplied_product_model_no':post.get('supplied_sepretly_size'),
				'supplied_product_warranty':post.get('supplied_sepretly_inverter_warranty'),
				'supplied_made_in':post.get('supplied_sepretly_made_in'),

				'battery_brand':post.get('supplied_sepretly_battery_brand'),
				'battery_model_no':post.get('supplied_sepretly_battery_model'),
				'battery_warranty':post.get('supplied_sepretly_battery_warranty'),
				'battery_supplied_made_in':post.get('supplied_sepretly_battery_made_in'),
			}
			result.sudo().write(vals)
			content = "In your project bid is Edited by "+request.env.user.name+""

			# inb Image delete--------------------------------------------
			# inbuilt_doc_attachment_ids
			if post.get('inb_removed_list'):
				inb_removed_list = post.get('inb_removed_list')
				# inbuilt_doc_list_ids = inb_removed_list.split(',')
				list_ids = list(filter(None,  inb_removed_list.split(',')))
				inbuilt_doc_list_ids = list(filter(None, [int(x) for x in list_ids]))

				ir_attachment = request.env['ir.attachment'].browse(inbuilt_doc_list_ids)
				if ir_attachment:
					ir_attachment.sudo().unlink()

			inbuilt_attchment_photo_multi_files = request.httprequest.files.getlist('inbuilt_attchment_photo_multi')
			att_inbuilt_img = []
			for file in inbuilt_attchment_photo_multi_files:
				if file.filename:
					inbuilt_attchment_photo_multi_value = (0,0,{
						'name': file.filename,
						'datas': base64.encodebytes(file.read()),
						})
					att_inbuilt_img.append(inbuilt_attchment_photo_multi_value)	
			
			result.sudo().write({'inbuilt_doc_attachment_ids':att_inbuilt_img})
			# inb Image delete----

			# SUPPLIER INVENER DETAIL ===
			if post.get('inv_removed_list'):
				inv_removed_list = post.get('inv_removed_list')
				# inbuilt_doc_list_ids = inv_removed_list.split(',')
				inv_list_ids = list(filter(None,  inv_removed_list.split(',')))
				inbuilt_doc_inv_list_ids = list(filter(None, [int(x) for x in inv_list_ids]))

				inbuilt_ir_attachment = request.env['ir.attachment'].browse(inbuilt_doc_inv_list_ids)
				if inbuilt_ir_attachment:
					inbuilt_ir_attachment.sudo().unlink()

			supplied_sepretly_attchment_photo_multi_files = request.httprequest.files.getlist('supplied_sepretly_attchment_photo_multi')
			att_invertar_img = []
			for file in supplied_sepretly_attchment_photo_multi_files:
				if file.filename:
					supplied_sepretly_attchment_photo_multi_value = (0,0,{
						'name': file.filename,
						'datas': base64.encodebytes(file.read()),
						})
					att_invertar_img.append(supplied_sepretly_attchment_photo_multi_value)	
			
			result.sudo().write({'supplied_doc_attachment_ids':att_invertar_img})
			# SUPPLIER INVENER DETAIL end===

			# SUPPLIER BATTERY DETAIL ===
			if post.get('bat_removed_list'):
				bat_removed_list = post.get('bat_removed_list')
				# inbuilt_doc_list_ids = bat_removed_list.split(',')
				bat_list_ids = list(filter(None,  bat_removed_list.split(',')))
				inbuilt_doc_bat_list_ids = list(filter(None, [int(x) for x in bat_list_ids]))

				bat_ir_attachment = request.env['ir.attachment'].browse(inbuilt_doc_bat_list_ids)
				if bat_ir_attachment:
					bat_ir_attachment.sudo().unlink()

			supplied_sepretly_battery_datasheet_files = request.httprequest.files.getlist('supplied_sepretly_battery_datasheet')
			att_batt_img = []
			for file in supplied_sepretly_battery_datasheet_files:
				if file.filename:
					supplied_sepretly_battery_datasheet_value = (0,0,{
						'name': file.filename,
						'datas': base64.encodebytes(file.read()),
						})
					att_batt_img.append(supplied_sepretly_battery_datasheet_value)	
			
			result.sudo().write({'battery_doc_attachment_supplied_ids':att_batt_img})
			# SUPPLIER BATTERY DETAIL END===

			# how_it_attachment_supplied_ids DETAIL ===
			if post.get('look_removed_list'):
				look_removed_list = post.get('look_removed_list')
				# inbuilt_doc_list_ids = look_removed_list.split(',')
				look_list_ids = list(filter(None,  look_removed_list.split(',')))
				inbuilt_doc_look_list_ids = list(filter(None, [int(x) for x in look_list_ids]))

				look_ir_attachment = request.env['ir.attachment'].browse(inbuilt_doc_look_list_ids)
				if look_ir_attachment:
					look_ir_attachment.sudo().unlink()

			how_it_look_attchment_photo_multi_files = request.httprequest.files.getlist('how_it_look_attchment_photo_multi')
			att_batt_look_img = []
			for file in how_it_look_attchment_photo_multi_files:
				if file.filename:
					how_it_look_attchment_photo_multi_value = (0,0,{
						'name': file.filename,
						'datas': base64.encodebytes(file.read()),
						})
					att_batt_look_img.append(how_it_look_attchment_photo_multi_value)	
			
			result.sudo().write({'how_it_attachment_supplied_ids':att_batt_look_img})
			# how_it_attachment_supplied_ids DETAIL END===

		
		result.solar_project_id.sudo().write({'supplier_project_state':'inprogress'})
		result.solar_project_id.sudo().write({'suppiler_status_ids':[(6,0,result.ids)]})

		# Sunen Start
		# Battery Attachments
		battry_counter = post.get('battery_information_count')
		if battry_counter:
			battry_info_list = []
			for d in range(1,int(battry_counter)+1):
				# if post.get("area_operates_city"+str(d)) and post.get("redius_profile"+str(d)) and post.get("zip_code_no"+str(d)):
				battry_info = {}
				battry_info['battery_product_Brand'] = post.get("battery_information_brand"+str(d)) 	 
				battry_info['battery_product_model_no'] = post.get("battery_information_model"+str(d)) 	 
				battry_info['battery_made_in'] = post.get("battery_information_made_in"+str(d)) 	 
				battry_info['battery_product_warranty'] = post.get("battery_information_product_warranty"+str(d))
				attachment = post.get("battery_information_product_datasheet_img"+str(d))
				img_file = post.get("battery_information_product_datasheet_file"+str(d))
				battary_attach = None
				if attachment:
					battary_attach =  base64.encodestring(attachment.read())
				if img_file and not attachment:
					battary_attach = img_file

				battry_info['battery_attch_img'] = battary_attach

				battry_info_list.append((0, 0,battry_info))
			for battry in result.sudo().battery_doc_attachment_ids:
				battry.sudo().unlink()
			result.sudo().write({'battery_doc_attachment_ids':battry_info_list})

		# Invertor Attachments
		invertor_counter = post.get('inventor_area_operates_counter')
		if invertor_counter:
			invertor_info_list = []
			for d in range(1,int(invertor_counter)+1):
				# if post.get("area_operates_city"+str(d)) and post.get("redius_profile"+str(d)) and post.get("zip_code_no"+str(d)):
				invertor_info = {}
				invertor_info['inverter_product_Brand'] = post.get("supllier_inverter_brand"+str(d)) 	 
				invertor_info['inverter_product_model_no'] = post.get("supllier_inverter_size"+str(d)) 	 
				invertor_info['inverter_made_in'] = post.get("made_in_sup"+str(d)) 	 
				invertor_info['inverter_product_warranty'] = post.get("supllier_inverter_warranty"+str(d))
				# invertor_info['inverter_attch_img'] = post.get("attchment_photo_multi_inverter"+str(d))

				attachment = post.get("attchment_photo_multi_inverter"+str(d))
				img_file = post.get("attchment_photo_multi_inverter_file"+str(d))
				inventar_attach = None
				if attachment:
					inventar_attach =  base64.encodestring(attachment.read())
				if img_file and not attachment:
					inventar_attach = img_file

				invertor_info['inverter_attch_img'] = inventar_attach

				invertor_info_list.append((0, 0,invertor_info))
			for inventar in result.sudo().inverter_doc_attachment_ids:
				inventar.sudo().unlink()
			result.sudo().write({'inverter_doc_attachment_ids':invertor_info_list})

		# Sunen End

		pdf = request.env.ref('airbid_master.action_report_supplier_system').sudo()._render_qweb_pdf([result.id])[0]
		
		# if pdf_data:
		attachment_value = {
			'name': 'supplier Information',
			'datas': base64.encodebytes(pdf),
			'res_model': 'solar.supplier',
			'res_id': result.id
		}
		# Create Attachment
		attchment_email = request.env['ir.attachment'].sudo().create(attachment_value)
		admin_user = request.env['res.users'].sudo().search([('is_admin','=',True)],limit=1)
		
		mail_values_user_check = {
					'subject': 'Supplier Bid Question' ,
					'body_html': "<div>%s</div>" %(content),
					'email_to':request.env.user.login,
					# 'email_from': request.env.user.login,
					'email_cc':admin_user.partner_id.email,
					'attachment_ids': [(4, attchment_email.id)]
				}
		create_and_send_email = request.env['mail.mail'].sudo().create(mail_values_user_check).sudo().send()
		# ss_record_id = request.env['solar.system'].sudo().search([('id','=',post.get('record_id'))])
		# print(post.get('record_id'),'sssssssssssssssssss',ss_record_id)
		return request.render('airbid_master.submit_bid_form',{"ref_sup_no":result.sequence_no})

	@http.route(['/dashboard'], type='http', auth="public", website=True, sitemap=True)
	def Dashboard(self, **post):
		user_id = request.env.user.partner_id
		if post.get('sort'):
			data = request.env['solar.system'].sudo().search([('customer_id', '=', user_id.id)],order="create_date asc")
		else:
			data = request.env['solar.system'].sudo().search([('customer_id', '=', user_id.id)],order="create_date desc")
		return request.render('airbid_master.dashboard_project',{"data":data, "menu_customer_dashboard":True})

	@http.route(['/dashboard/project'], type='http', auth="public", website=True, sitemap=True)
	def DashboardProject(self, **post):
		return request.render('airbid_master.project_detail')

	@http.route(['/review'], type='http', auth="public", website=True, sitemap=True,csrf=False)
	def DashboardProject(self,sort=None,record_id=None ,**post):
		data = request.env['solar.system'].sudo().search([('id','=',record_id)])
		supplier_ids = request.env['solar.supplier'].sudo().search([('solar_project_id','=',data.id)])
		img_data = request.env['image.selection'].sudo().search([])
		if sort == 'low_to_high':
			data = request.env['solar.system'].sudo().search([('id','=',record_id)])
			supplier_ids = request.env['solar.supplier'].sudo().search([('solar_project_id','=',data.id)],order="system_size asc")
			img_data = request.env['image.selection'].sudo().search([])

		if sort == 'high_to_low':
			data = request.env['solar.system'].sudo().search([('id','=',record_id)])
			supplier_ids = request.env['solar.supplier'].sudo().search([('solar_project_id','=',data.id)],order="system_size desc")
			img_data = request.env['image.selection'].sudo().search([])

		if sort == 'low_price':
			data = request.env['solar.system'].sudo().search([('id','=',record_id)])
			if data.cash_fin == 'cash':
				supplier_ids = request.env['solar.supplier'].sudo().search([('solar_project_id','=',data.id)],order="full_price asc")
			else:
				supplier_ids = request.env['solar.supplier'].sudo().search([('solar_project_id','=',data.id)],order="full_price desc")
			img_data = request.env['image.selection'].sudo().search([])

		if sort == 'high_price':
			data = request.env['solar.system'].sudo().search([('id','=',record_id)])
			if data.cash_fin == 'finance':
				supplier_ids = request.env['solar.supplier'].sudo().search([('solar_project_id','=',data.id)],order="final_price asc")
			else:
				supplier_ids = request.env['solar.supplier'].sudo().search([('solar_project_id','=',data.id)],order="final_price desc")
			img_data = request.env['image.selection'].sudo().search([])

		return request.render('airbid_master.review_page',{"data":data,"img_data":img_data,'bid_ids':supplier_ids})

	@http.route('/request/project', auth='public', type='http', website=True, csrf=False)
	def request_peoject_website(self,sort=None,record_id=None ,**post):
		data = request.env['solar.system'].sudo().search([('id','=',record_id)])

		supplier_ids = request.env['solar.supplier'].sudo().search([('solar_project_id','=',data.id)])
		img_data = request.env['image.selection'].sudo().search([])
		if sort == 'low_to_high':
			data = request.env['solar.system'].sudo().search([('id','=',record_id)])
			supplier_ids = request.env['solar.supplier'].sudo().search([('solar_project_id','=',data.id)],order="system_size asc")
			img_data = request.env['image.selection'].sudo().search([])

		if sort == 'high_to_low':
			data = request.env['solar.system'].sudo().search([('id','=',record_id)])
			supplier_ids = request.env['solar.supplier'].sudo().search([('solar_project_id','=',data.id)],order="system_size desc")
			img_data = request.env['image.selection'].sudo().search([])

		if sort == 'low_price':
			data = request.env['solar.system'].sudo().search([('id','=',record_id)])
			if data.cash_fin == 'cash':
				supplier_ids = request.env['solar.supplier'].sudo().search([('solar_project_id','=',data.id)],order="full_price asc")
			else:
				supplier_ids = request.env['solar.supplier'].sudo().search([('solar_project_id','=',data.id)],order="full_price desc")
			img_data = request.env['image.selection'].sudo().search([])

		if sort == 'high_price':
			data = request.env['solar.system'].sudo().search([('id','=',record_id)])
			if data.cash_fin == 'finance':
				supplier_ids = request.env['solar.supplier'].sudo().search([('solar_project_id','=',data.id)],order="final_price asc")
			else:
				supplier_ids = request.env['solar.supplier'].sudo().search([('solar_project_id','=',data.id)],order="final_price desc")
			img_data = request.env['image.selection'].sudo().search([])

		uploaded_files = request.httprequest.files.getlist('attchment_photo_multi')
		attachment_ids = []
		for file in uploaded_files:
			attachment_value = {
				'name': file.filename,
				'datas': base64.encodebytes(file.read()),
				'res_model': 'solar.system',
				'res_id': data.id
				}
			# Create Attachment
			attachment_id =  request.env['ir.attachment'].sudo().create(attachment_value)
			if attachment_id.id not in attachment_ids:
				attachment_ids.append(attachment_id.id)

		if attachment_ids:
			sms_text = "Request Project Name"+post.get('req_project_name')+" " "and Customer Name "+post.get('req_customer_name')+" " " and Email : "+post.get('login_name')+" And Phone Number "+post.get('phone_cust_no')+" and Commant "+ post.get('about_the_project_comment') +""
			email_from = request.env['ir.mail_server'].sudo().search([],limit=1)
			admin_user = request.env['res.users'].sudo().search([('is_admin', '=' , True)])
			from_admin = admin_user.partner_id.email
			emails_list=[]
			emails_list.append(request.env.ref('base.partner_admin').sudo().email)
			emails_list.append(request.env.user.partner_id.email)
			mail_values_user_check = {
						'subject': 'Request Edit Project' ,
						'body_html': sms_text,
						'email_cc':", ".join(emails_list),
						'email_to':", ".join(emails_list),
						'email_from':email_from.smtp_user,
						'attachment_ids': [(6,0, attachment_ids)]
					}
			create_and_send_email = request.env['mail.mail'].sudo().create(mail_values_user_check).sudo().send()	
		return request.render("airbid_master.review_page",{"data":data,"img_data":img_data,'bid_ids':supplier_ids})	
	
	@http.route('/request/project/installer', auth='public', type='http', website=True, csrf=False)
	def request_peoject_websiteinstaller(self,sort=None,record_id=None ,**post):
		bid_data=[]
		user_id = request.env.user.partner_id
		is_edit=False
		if user_id.is_supplier == 'installer':
			is_edit=True
		
		data = request.env['installation.solar.system'].sudo().search([('id','=',record_id)])
		for bid in data.installer_bids_ids:
			bid_data.append({'supplier':bid.customer_id.name,'id':bid.id,'des':bid.bid_description,'price':bid.price,'retailer':bid.customer_id.retailer,'member':bid.customer_id.member,'iso':bid.customer_id.iso,'document':bid.customer_id.document})
		# if sort == 'low_price':
		# 	bid_data=sorted(bid_data, key = itemgetter('price'))
		# elif sort == 'high_price':
		# 	bid_data=sorted(bid_data, key = itemgetter('price'),reverse=True)
		# else:
		# 	pass

		uploaded_files = request.httprequest.files.getlist('attchment_photo_multi')
		attachment_ids = []
		for file in uploaded_files:
			attachment_value = {
				'name': file.filename,
				'datas': base64.encodebytes(file.read()),
				'res_model': 'solar.system',
				'res_id': data.id
				}
			# Create Attachment
			attachment_id =  request.env['ir.attachment'].sudo().create(attachment_value)
			if attachment_id.id not in attachment_ids:
				attachment_ids.append(attachment_id.id)


		if attachment_ids:
			sms_text = "Request Project Name "+post.get('req_project_name')+" " "and Customer Name "+post.get('req_customer_name')+" " " and Email : "+post.get('login_name')+" And Phone Number "+post.get('phone_cust_no')+" and Commant "+ post.get('about_the_project_comment') +""
			email_from = request.env['ir.mail_server'].sudo().search([],limit=1)
			admin_user = request.env['res.users'].sudo().search([('is_admin', '=' , True)])
			from_admin = admin_user.partner_id.email
			emails_list=[]
			emails_list.append(request.env.ref('base.partner_admin').sudo().email)
			emails_list.append(request.env.user.partner_id.email)
			mail_values_user_check = {
						'subject': 'Request Edit Project' ,
						'body_html': sms_text,
						'email_cc':", ".join(emails_list),
						'email_to':", ".join(emails_list),
						'email_from':email_from.smtp_user,
						'attachment_ids': [(6,0, attachment_ids)]
					}
			create_and_send_email = request.env['mail.mail'].sudo().create(mail_values_user_check).sudo().send()	
		return request.render("airbid_master.my_solar_information",{'is_edit':is_edit,'is_customer': True,'record_id':data,'rec_id':data,'bid_data':bid_data})

	@http.route(['/request/edit'], type='http', auth="public", website=True, sitemap=True)
	def RequestProjectEdit(self,record_id=None, **post):
		data = request.env['solar.system'].sudo().search([('id','=',int(record_id))])
		admin_user = request.env['res.users'].sudo().search([('is_admin', '=' , True)])
		email_from = request.env['ir.mail_server'].sudo().search([],limit=1)

		for res in admin_user:
			from_mail = res.partner_id.email
			mail_values_user_check = {
				'subject': 'Request for Edit Bid' ,
				'email_to':data.customer_id.email,
				'email_cc':from_mail,
				'email_from':email_from.smtp_user,
				'body_html': "<div>%s is Requesting for the edit in the project</div>" %(request.env.user.name),
			}
			create_and_send_email = request.env['mail.mail'].sudo().create(mail_values_user_check).sudo().send()
		return request.render('airbid_master.review_page',{"data":data})

	@http.route(['/compair/supplier'], type='http', auth="public", website=True, sitemap=True)
	def CompareSupplier(self, **post):
		value = post.get('supplier_data')
		domain = []
		if value:
			record = value.split(",")
			for i in range(0, len(record)):
				record[i] = int(record[i])
		
		data = request.env['solar.supplier'].sudo().search([('id','in',record)])
		img_id = request.env['solar.system'].sudo().search([('id','=',post.get('project_img'))])
		return request.render('airbid_master.compare_supplier',{"data":data,'img_id':img_id})

	@http.route(['/compair/installer'], type='http', auth="public", website=True, sitemap=True)
	def CompareInstaller(self, **post):
		print("66666666666666666666666666",post)
		value = post.get('supplier_data')
		domain = []
		if value:
			record = value.split(",")
			for i in range(0, len(record)):
				record[i] = int(record[i])
		
		data = request.env['installer.bid'].sudo().search([('id','in',record)])
		print("DDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDD",data)
		#img_id = request.env['solar.system'].sudo().search([('id','=',post.get('project_img'))])
		return request.render('airbid_master.compare_installer',{"data":data})
		# print("")
		# value = post.get('supplier_data')
		# domain = []
		# if value:
		# 	record = value.split(",")
		# 	for i in range(0, len(record)):
		# 		record[i] = int(record[i])
		
		# data = request.env['solar.supplier'].sudo().search([('id','in',record)])
		# img_id = request.env['solar.system'].sudo().search([('id','=',post.get('project_img'))])
		# return request.render('airbid_master.compare_supplier',{"data":data,'img_id':img_id})

	@http.route(['/Aboutus'], type='http', auth="public", website=True, sitemap=True)
	def AboutUs(self, **post):
		return request.render('airbid_master.about_us_form')

	@http.route(['/Howitswork'], type='http', auth="public", website=True, sitemap=True)
	def HowitsWork(self, **post):
		return request.render('airbid_master.how_its_work_form')

	@http.route(['/Faqs'], type='http', auth="public", website=True, sitemap=True)
	def Faqs(self, **post):
		return request.render('airbid_master.faqs_questation_page')
	
	@http.route(['/supplier/dashboard'], type='http', auth="public", website=True, sitemap=True)
	def SupplierDashboard(self,bid_id=None, **post):
		user_id = request.env.user.partner_id
		customer_close = {}
		if user_id.is_supplier == 'installer':
			res=[]
			data=[]
			solar_id = []
			if user_id.service_zip:
				res = json.loads(user_id.service_zip)
			customer_close = request.env['installation.solar.system'].sudo().search([('zip','in',res)],order="create_date desc")
			# total_open = 0
			# total_open = request.env['solar.system'].sudo().search_count([('customer_project_state','=','open'),('suppiler_status_ids','not in',data.ids)])
			# installer_ids = request.env['installer.bid'].sudo().search([])
			# print('INSTALLER SUPPLIER ----================',installer_ids.customer_id)
			# print('INSTALLER PARTNER ----================',request.env.user.partner_id.id)
			# total_open = request.env['installer.bid'].sudo().search_count([
			# 	('customer_id','=',request.env.user.partner_id.id),('project_state','=','open')])
			
			total_open = request.env['installation.solar.system'].sudo().search_count([
				('project_state','=','open'),
				('zip','in',res)])

			total_inprogress = request.env['installer.bid'].sudo().search_count([('customer_id','=',request.env.user.partner_id.id),('project_state','=','inprogress')])
			total_won = request.env['installer.bid'].sudo().search_count([('customer_id','=',request.env.user.partner_id.id),('project_state','=','won')])
			total_lost = request.env['installer.bid'].sudo().search_count([('customer_id','=',request.env.user.partner_id.id),('project_state','=','lost')])
		else:
			if bid_id:
				data = request.env['solar.supplier'].sudo().search([('supplier_id','=',request.env.user.partner_id.id),('solar_project_id','=',int(bid_id))],order="create_date desc")
				customer_data = {}
				# customer_close = {}
			else:
				res=[]
				if user_id.service_zip:
					res = json.loads(user_id.service_zip)

				if post.get('sort'):
					data = request.env['solar.supplier'].sudo().search([('supplier_id','=',request.env.user.partner_id.id)],order="create_date asc")
					customer_data = request.env['solar.system'].sudo().search([('customer_project_state','=','open'),
						('suppiler_status_ids','not in',data.ids)],order="create_date asc")
					# customer_close = request.env['installation.solar.system'].sudo().search([('zip','in',res)],order="create_date desc")
					solar_id = []
					for data_cd in customer_data:
						if user_id.service_zip:
							if data_cd.zip in user_id.service_zip:
								solar_id.append(data_cd)
				else:
					data = request.env['solar.supplier'].sudo().search([('supplier_id','=',request.env.user.partner_id.id)],order="create_date desc")
					# customer_close = request.env['installation.solar.system'].sudo().search([('zip','in',res)],order="create_date desc")	
					customer_data = request.env['solar.system'].sudo().search([('customer_project_state','=','open'),
						('suppiler_status_ids','not in',data.ids)],order="create_date desc")
					solar_id = []

					for data_cd in customer_data:
						if user_id.service_zip:
							if data_cd.zip in user_id.service_zip:
								solar_id.append(data_cd)

				total_open = len(solar_id)
				# total_open = request.env['solar.system'].sudo().search_count([('customer_project_state','=','open'),('suppiler_status_ids','not in',data.ids)])
				total_inprogress = request.env['installer.bid'].sudo().search_count([('customer_id','=',request.env.user.partner_id.id),('project_state','=','inprogress')])
				total_won = request.env['installer.bid'].sudo().search_count([('customer_id','=',request.env.user.partner_id.id),('project_state','=','won')])
				total_lost = request.env['installer.bid'].sudo().search_count([('project_id.supplier_customer_id.id','=',request.env.user.partner_id.id),('customer_id.is_supplier','=','installer'),('project_state','=','won')])
				#.is_supplier
		return request.render('airbid_master.supplier_dashboard_page',{"data":data,"total_open":total_open,"total_inprogress":total_inprogress,"total_won":total_won,"total_lost":total_lost,'customer_close':customer_close,"customer_data":solar_id,'menu_dashboard':True})

	@http.route(['/open'], type='http', auth="public", website=True, sitemap=True)
	def SupplierDashboardOpen(self, **post):
		user_id= request.env.user.partner_id
		if post.get('sort'):
			data = request.env['solar.supplier'].sudo().search([('supplier_id','=',request.env.user.partner_id.id)],order="solar_project_id asc")
			customer_data = request.env['solar.system'].sudo().search([('customer_project_state','=','open'),('suppiler_status_ids','not in',data.ids)],order="project_create_date asc")
			solar_id = []
			for data_cd in customer_data:
				if user_id.service_zip:
					if data_cd.zip in user_id.service_zip:
						solar_id.append(data_cd)			
		else:
			data = request.env['solar.supplier'].sudo().search([('supplier_id','=',request.env.user.partner_id.id)],order="solar_project_id desc")
			customer_data = request.env['solar.system'].sudo().search([('customer_project_state','=','open'),('suppiler_status_ids','not in',data.ids)],order="project_create_date desc")
			solar_id = []
			for data_cd in customer_data:
				if user_id.service_zip:
					if data_cd.zip in user_id.service_zip:
						solar_id.append(data_cd)				

		return request.render('airbid_master.open_supplier_dashboard_page',{"data":data,"customer_data":solar_id})

	@http.route(['/open/installer'], type='http', auth="public", website=True, sitemap=True)
	def InstallerDashboardOpen(self, **post):
		user_id= request.env.user.partner_id
		customer_close = {}
		if user_id.is_supplier == 'installer':
			res=[]
			# data=[]
			solar_id = []
			if user_id.service_zip:
				res = json.loads(user_id.service_zip)
				
			customer_close = request.env['installation.solar.system'].sudo().search([('project_state','=','open'),
				('zip','in',res)],order="create_date desc")
			solar_id = []
			for data_cd in customer_close:
				if user_id.service_zip:
					if data_cd.zip in user_id.service_zip:
						solar_id.append(data_cd)	

		return request.render('airbid_master.open_installer_dashboard_page',{"customer_close":solar_id})	

	@http.route(['/intrested'], type='json', auth="public", website=True, sitemap=True)
	def SupplierIntrestedProject(self,project_id, **post):
		user_id = request.env.user.partner_id
		data = request.env['solar.system'].sudo().search([('id','=',project_id)])
		if user_id.id in data.suppiler_intrested_ids.ids:
			data.suppiler_intrested_ids = [(3, user_id.id)] 
		else:
			data.suppiler_intrested_ids = [(4, user_id.id)] 
		return "value"	
	
	@http.route(['/filter'], type='http', auth="public", website=True, sitemap=True)
	def IntrestedFilter(self,project=None, **post):
		user_id = request.env.user.partner_id
		if project == 'intrested':
			customer_data = request.env['solar.system'].search([('suppiler_intrested_ids','in',user_id.ids)])
		else:
			data = request.env['solar.supplier'].sudo().search([('supplier_id','=',request.env.user.partner_id.id)])
			customer_data = request.env['solar.system'].search([('customer_project_state','=','open'),('suppiler_status_ids','not in',data.ids),('suppiler_intrested_ids','not in',user_id.ids)])
		return request.render('airbid_master.open_supplier_dashboard_page',{"customer_data":customer_data})	


	@http.route(['/inprogress'], type='http', auth="public", website=True, sitemap=True)
	def SupplierDashboardInProgress(self, **post):
		if post.get('sort'):
			supplier_id = request.env['solar.supplier'].sudo().search([('supplier_id','=',request.env.user.partner_id.id)],order="solar_project_id asc")
			data = request.env['solar.system'].sudo().search([('supplier_project_state','=','inprogress'),('supplier_bids_ids','in',supplier_id.ids)])
		else:
			supplier_id = request.env['solar.supplier'].sudo().search([('supplier_id','=',request.env.user.partner_id.id)],order="solar_project_id desc")
			data = request.env['solar.system'].sudo().search([('supplier_project_state','=','inprogress'),('supplier_bids_ids','in',supplier_id.ids)])
		return request.render('airbid_master.inprogress_supplier_dashboard_page',{"data":data})

	@http.route(['/inprogress/installer'], type='http', auth="public", website=True, sitemap=True)
	def InstallerDashboardInProgress(self, **post):
		# if post.get('sort'):
		# 	supplier_id = request.env['installer.bid'].sudo().search([('customer_id','=',request.env.user.partner_id.id)],order="project_id asc")
		# 	# data = request.env['installation.solar.system'].sudo().search([('project_state','=','inprogress'),('installer_bids_ids','in',supplier_id.ids)])
		# 	data = request.env['installation.solar.system'].sudo().search([('project_state','=','inprogress'),('installer_bids_ids','in',supplier_id.ids)])
		# 	print('55555555555555555555555555555555555555555555555',data)
		# 	print('8888888888888888888888888888888',supplier_id.ids)
		# else:
		# 	supplier_id = request.env['installer.bid'].sudo().search([('customer_id','=',request.env.user.partner_id.id)],order="project_id desc")
		# 	data = request.env['installation.solar.system'].sudo().search([('project_state','=','inprogress'),('installer_bids_ids','in',supplier_id.ids)])
		# 	print('66666666666666666666666666666666666666666666666666',data)
		# 	print('44444444444444444444444444444',supplier_id.ids)
		res=[]
		solar_id = []
		user_id= request.env.user.partner_id
		if user_id.service_zip:
			res = json.loads(user_id.service_zip)
		#customer_close = request.env['installation.solar.system'].sudo().search([('project_state','=','won'),('zip','in',res)],order="create_date desc")
		total_inprogress = request.env['installer.bid'].sudo().search([('customer_id','=',request.env.user.partner_id.id),('project_state','=','inprogress')])
		data=total_inprogress.mapped('project_id')
		return request.render('airbid_master.inprogress_installer_dashboard_page',{"data":data})

	@http.route(['/won'], type='http', auth="public", website=True, sitemap=True)
	def SupplierDashboardWon(self, **post):
		if post.get('sort'):
			data = request.env['solar.supplier'].sudo().search([('supplier_id','=',request.env.user.partner_id.id),('project_state','=','won')],order="solar_project_id asc")
		else:	
			data = request.env['solar.supplier'].sudo().search([('supplier_id','=',request.env.user.partner_id.id),('project_state','=','won')],order="solar_project_id desc")
		return request.render('airbid_master.won_supplier_dashboard_page',{"data":data})

	@http.route(['/won/installer'], type='http', auth="public", website=True, sitemap=True)
	def InstallerDashboardWoninstaller(self, **post):
		res=[]
		solar_id = []
		user_id= request.env.user.partner_id
		if user_id.service_zip:
			res = json.loads(user_id.service_zip)
		#customer_close = request.env['installation.solar.system'].sudo().search([('project_state','=','won'),('zip','in',res)],order="create_date desc")
		total_won = request.env['installer.bid'].sudo().search([('customer_id','=',request.env.user.partner_id.id),('project_state','=','won')])
		system_ids=total_won.mapped('project_id')
		return request.render('airbid_master.won_installer_dashboard_page',{"data":system_ids})	

	@http.route(['/lost'], type='http', auth="public", website=True, sitemap=True)
	def SupplierDashboardLost(self, **post):
		data = request.env['solar.supplier'].sudo().search([('supplier_id','=',request.env.user.partner_id.id),('project_state','=','lost')],order="solar_project_id asc")
		return request.render('airbid_master.lost_supplier_dashboard_page',{"data":data})

	@http.route(['/lost/installer'], type='http', auth="public", website=True, sitemap=True)
	def InstallerDashboardLost(self, **post):
		total_lost = request.env['installer.bid'].sudo().search([('customer_id','=',request.env.user.partner_id.id),('project_state','=','lost')])
		#request.env['installer.bid'].sudo().search([('customer_id','=',request.env.user.partner_id.id),('project_state','=','won')])
		data=total_lost.mapped('project_id')
		#data = request.env['installer.bid'].sudo().search([('customer_id','=',request.env.user.partner_id.id),('project_state','=','lost')],order="project_id asc")
		return request.render('airbid_master.lost_installer_dashboard_page',{"data":data})	

	@http.route(['/supplier/review'], type='http', auth="public", website=True, sitemap=True)
	def SupplierDashboardReview(self, **post):
		record_id = request.env['solar.system'].sudo().search([('id','=',post.get('record_id'))])
		img_data = request.env['image.selection'].sudo().search([])
		return request.render('airbid_master.supplier_review_page',{'record_id':record_id,'status':post.get('status'),'img_data':img_data})

	@http.route(['/supplier/bid'], type='http', auth="public", website=True, sitemap=True)
	def SupplierBidDetail(self,bid_id=None, **post):
		user_id = request.env.user.partner_id
		# per bid membership plan.................................
		if user_id.per_bid:
			if user_id.bid_count > 0 or user_id.bid_count == 1:
				bid_data = {}
				if bid_id:
					record_id = request.env['solar.system'].sudo().search([('id','=',post.get('record_id'))])
					bid_data = request.env['solar.supplier'].sudo().search([('supplier_id','=',request.env.user.partner_id.id),('solar_project_id','=',int(bid_id))])

				else:
					record_id = request.env['solar.system'].sudo().search([('id','=',post.get('record_id'))])
				mail_values_user_check = {
							'subject': 'Request for New Bid' ,
							'body_html': "<div>%s is Requesting a new bid in your project <br />After a few moments,you will get to know about the bid of %s.</div>" %(request.env.user.name,request.env.user.name),
							'email_to':record_id.customer_id.email,
							'email_from': request.env.user.login,
						}
				create_and_send_email = request.env['mail.mail'].sudo().create(mail_values_user_check).sudo().send()
				return request.render('airbid_master.supplier_bid_detail',{'record_id':record_id,'bid_data':bid_data,'status':post.get('status')})
			else:
				user_id = request.env.user.partner_id
				user_id.write({'per_bid':False,
						'per10_bid':False,
						'per20_bid':False,
						'per30_bid':False})
				return request.redirect("/membership")

		
		# 10 bid membership plan ...........................................
		elif user_id.per10_bid:
			if user_id.bid_count > 0 or user_id.bid_count <= 10:
				bid_data = { }
				if bid_id:
					record_id = request.env['solar.system'].sudo().search([('id','=',post.get('record_id'))])
					bid_data = request.env['solar.supplier'].sudo().search([('supplier_id','=',request.env.user.partner_id.id),('solar_project_id','=',int(bid_id))])

				else:
					record_id = request.env['solar.system'].sudo().search([('id','=',post.get('record_id'))])
				mail_values_user_check = {
							'subject': 'Request for New Bid' ,
							'body_html': "<div>%s is Requesting a new bid in your project <br />After a few moments,you will get to know about the bid of %s.</div>" %(request.env.user.name,request.env.user.name),
							'email_to':record_id.customer_id.email,
							'email_from': request.env.user.login,
						}
				create_and_send_email = request.env['mail.mail'].sudo().create(mail_values_user_check).sudo().send()
				return request.render('airbid_master.supplier_bid_detail',{'record_id':record_id,'bid_data':bid_data,'status':post.get('status')})
			else:
				user_id = request.env.user.partner_id
				user_id.write({'per_bid':False,
						'per10_bid':False,
						'per20_bid':False,
						'per30_bid':False})
				return request.redirect("/membership")
		

		# 20 bid membership plan...........................................
		elif user_id.per20_bid:
			if user_id.bid_count > 0 or user_id.bid_count <= 20:
				bid_data = { }
				if bid_id:
					record_id = request.env['solar.system'].sudo().search([('id','=',post.get('record_id'))])
					bid_data = request.env['solar.supplier'].sudo().search([('supplier_id','=',request.env.user.partner_id.id),('solar_project_id','=',int(bid_id))])

				else:
					record_id = request.env['solar.system'].sudo().search([('id','=',post.get('record_id'))])
				mail_values_user_check = {
							'subject': 'Request for New Bid' ,
							'body_html': "<div>%s is Requesting a new bid in your project <br />After a few moments,you will get to know about the bid of %s.</div>" %(request.env.user.name,request.env.user.name),
							'email_to':record_id.customer_id.email,
							'email_from': request.env.user.login,
						}
				create_and_send_email = request.env['mail.mail'].sudo().create(mail_values_user_check).sudo().send()
				return request.render('airbid_master.supplier_bid_detail',{'record_id':record_id,'bid_data':bid_data,'status':post.get('status')})
			else:
				user_id = request.env.user.partner_id
				user_id.write({'per_bid':False,
						'per10_bid':False,
						'per20_bid':False,
						'per30_bid':False})
				return request.redirect("/membership")
		
		
		# 30 bid membership plan.....................................
		elif user_id.per30_bid:
			if user_id.bid_count > 0 or user_id.bid_count <= 30:
				bid_data = { }
				if bid_id:
					record_id = request.env['solar.system'].sudo().search([('id','=',post.get('record_id'))])
					bid_data = request.env['solar.supplier'].sudo().search([('supplier_id','=',request.env.user.partner_id.id),('solar_project_id','=',int(bid_id))])

				else:
					record_id = request.env['solar.system'].sudo().search([('id','=',post.get('record_id'))])
				mail_values_user_check = {
							'subject': 'Request for New Bid' ,
							'body_html': "<div>%s is Requesting a new bid in your project <br />After a few moments,you will get to know about the bid of %s.</div>" %(request.env.user.name,request.env.user.name),
							'email_to':record_id.customer_id.email,
							'email_from': request.env.user.login,
						}
				create_and_send_email = request.env['mail.mail'].sudo().create(mail_values_user_check).sudo().send()
				return request.render('airbid_master.supplier_bid_detail',{'record_id':record_id,'bid_data':bid_data,'status':post.get('status')})
			else:
				user_id = request.env.user.partner_id
				user_id.write({'per_bid':False,
						'per10_bid':False,
						'per20_bid':False,
						'per30_bid':False})
				return request.redirect("/membership")
		

		# monthly plan for biding.......................................
		elif user_id.monthly_bid:
			if date.today() <= user_id.plan_end_date:
				bid_data = { }
				if bid_id:
					record_id = request.env['solar.system'].sudo().search([('id','=',post.get('record_id'))])
					bid_data = request.env['solar.supplier'].sudo().search([('supplier_id','=',request.env.user.partner_id.id),('solar_project_id','=',int(bid_id))])

				else:
					record_id = request.env['solar.system'].sudo().search([('id','=',post.get('record_id'))])
				mail_values_user_check = {
							'subject': 'Request for New Bid' ,
							'body_html': "<div>%s is Requesting a new bid in your project <br />After a few moments,you will get to know about the bid of %s.</div>" %(request.env.user.name,request.env.user.name),
							'email_to':record_id.customer_id.email,
							'email_from': request.env.user.login,
						}
				create_and_send_email = request.env['mail.mail'].sudo().create(mail_values_user_check).sudo().send()
				return request.render('airbid_master.supplier_bid_detail',{'record_id':record_id,'bid_data':bid_data,'status':post.get('status')})
			else:
				user_id = request.env.user.partner_id
				user_id.write({'per_bid':False,
						'per10_bid':False,
						'per20_bid':False,
						'per30_bid':False})
				return request.redirect("/membership")
		
		else:
			return request.redirect("/membership")


	@http.route(['/membership'], type='http', auth="public", website=True, sitemap=True)
	def SupplierMembership(self, **post):
		user_id = request.env.user.partner_id
		if user_id.bid_count <0:
			user_id.write({'per_bid':False,
				'per10_bid':False,
				'per20_bid':False,
				'per30_bid':False})
		if user_id.plan_end_date and  user_id.plan_end_date+relativedelta(days=1) == date.today():
			user_id.write({'monthly_bid':False})
		ppb_product = request.env['product.product'].search([('name','=','Pay Per Bid')])
		bb10_product = request.env['product.product'].search([('name','=','10 Bid Bulk')])
		bb20_product = request.env['product.product'].search([('name','=','20 Bid Bulk')])
		bb30_product = request.env['product.product'].search([('name','=','30 Bid Bulk')])
		monthly_product = request.env['product.product'].search([('name','=','Monthly Billing Plan')])
		is_approve=False
		if user_id.supplier_validate == 'approve':
			is_approve=True

		return request.render('airbid_master.supplier_membership',{'is_approve':is_approve,'user_id':user_id,'menu_sup_member':True,'ppb_product':ppb_product,'bb10_product':bb10_product.id,'bb20_product':bb20_product,'bb30_product':bb30_product,'monthly_product':monthly_product})

	@http.route(['/my/profile'], type='http', auth="public", website=True, sitemap=True)
	def SupplierProfile(self, **post):
		user_id = request.env.user.partner_id
		countries = request.env['res.country'].sudo().search([])
		sale_order = request.env['sale.order'].search([('partner_id','=',user_id.id)])
		states = request.env['res.country.state'].sudo().search([('country_id.code','ilike','AU')])

		if user_id.bid_count < 0:
			user_id.write({'per_bid':False,
				'per10_bid':False,
				'per20_bid':False,
				'per30_bid':False})
		if user_id.plan_end_date and  user_id.plan_end_date+relativedelta(days=1) == date.today():
			user_id.write({'monthly_bid':False})
		ppb_product = request.env['product.product'].sudo().search([('name','=','Pay Per Bid')])
		bb10_product = request.env['product.product'].sudo().search([('name','=','10 Bid Bulk')])
		bb20_product = request.env['product.product'].sudo().search([('name','=','20 Bid Bulk')])
		bb30_product = request.env['product.product'].sudo().search([('name','=','30 Bid Bulk')])
		monthly_product = request.env['product.product'].sudo().search([('name','=','Monthly Billing Plan')])

		data = request.env['solar.supplier'].sudo().search([('supplier_id','=',request.env.user.partner_id.id),('project_state','in',['won','inprogress','lost'])])	
		
		is_customer = False 
		if post.get('type') == 'customer':
			is_customer = True 
		print("CVVVVVVVVVVVVVVVVVVVVVVV",is_customer)
		return request.render('airbid_master.supplier_profile',{'is_customer':is_customer,'data':data,'states': states,'sale_order':sale_order,'menu_profile':True,'user_id':user_id,'ppb_product':ppb_product,'bb10_product':bb10_product.id,'bb20_product':bb20_product,'bb30_product':bb30_product,'monthly_product':monthly_product})

	@http.route(['/supplier/details'], type='http', auth="public", website=True, sitemap=True)
	def SupplierDataDetail(self,bid_id=None, **post):
		if bid_id:
			img_id = {}
			data = request.env['solar.supplier'].sudo().search([('id','=',int(bid_id))])
		else:
			data = request.env['solar.supplier'].sudo().search([('id','=',int(post.get('record_id')))])
			img_id = request.env['solar.system'].sudo().search([('id','=',int(post.get('project_img')))])
		return request.render('airbid_master.supplier_data_detail',{'data':data,'img_id':img_id})

	@http.route(['/delete/project'], type='http', auth="public", website=True, sitemap=True)
	def DeleteCustomerProject(self, **post):
		rec = request.env['solar.system'].sudo().search([('id', '=', int(post.get('record_id')))])
		rec.sudo().unlink()
		user_id = request.env.user.partner_id
		data = request.env['solar.system'].sudo().search([('customer_id', '=', user_id.id)])
		return request.redirect('/dashboard')

	@http.route(['/delete/project/installer'], type='http', auth="public", website=True, sitemap=True)
	def DeleteCustomerProjectInstaller(self, **post):
		rec = request.env['installation.solar.system'].sudo().search([('id', '=', int(post.get('record_id')))])
		is_product=request.env['product.template'].sudo().search([('installer_solar_id','=',rec.id)])
		rec.sudo().unlink()
		if is_product:
			is_product.sudo().unlink()
		user_id = request.env.user.partner_id
		#data = request.env['solar.system'].sudo().search([('customer_id', '=', user_id.id)])
		return request.redirect('/installer/customer')

	@http.route(['/confirm/supplier'], type='http', auth="public", website=True, sitemap=True)
	def ConfirmSupplier(self, **post):
		rec = request.env['solar.supplier'].sudo().search([('id', '=', int(post.get('record_id')))])
		user_id = request.env.user.partner_id
		data = request.env['res.partner'].sudo().search([('id', '=', user_id.id)])
		admin_user = request.env['res.users'].sudo().search([('is_admin', '=' , True)])
		rec.approved_bid()
		email_from = request.env['ir.mail_server'].sudo().search([],limit=1)
		email_template = request.env.ref('airbid_master.supplier_details_template')
		if email_template:
			ctx = {
			'email_to':request.env.user.login,
			'email_from':email_from.smtp_user,
			'email_cc':admin_user.partner_id.email,	
			}
			email_template.with_context(**ctx).sudo().send_mail(rec.id, force_send = True)

		
		# create_and_send_email = request.env['mail.mail'].sudo().create(mail_values_user_check).sudo().send()
		house_number_or_name = False
		if rec.solar_project_id.house_number_or_name:
			house_number_or_name = rec.solar_project_id.house_number_or_name	
			
		# ctx = request.env.context.copy()
		# template = request.env.ref('airbid_master.customer_address_detail', raise_if_not_found=False)
		# print('')
		# if template:
		# 	ctx = {
		# 		'email_to': rec.solar_project_id.customer_id.email,
		# 		'email_from': email_from.smtp_user,
		# 		'project_name':rec.solar_project_id.customer_project_name,
		# 		'customer_phone':rec.solar_project_id.phone,
		# 		'customer_email':rec.solar_project_id.email_id,
		# 		'street':rec.solar_project_id.street,
		# 		'street2':house_number_or_name,
		# 		'city':rec.solar_project_id.city,
		# 		'state':rec.solar_project_id.state_id.name,
		# 		'zip':rec.solar_project_id.zip,
		# 		'country':rec.solar_project_id.country_id.name,
		# 	}
		# 	print('ALL CUSTOMER ADDRESS -------',template)
		# 	template.with_context(**ctx).sudo().send_mail(rec.id, force_send = True)

		from_mail = email_from.smtp_user
		from_to = rec.solar_project_id.email_id
		project_name = rec.solar_project_id.customer_project_name
		customer_phone=rec.solar_project_id.phone
		customer_email = rec.solar_project_id.email_id
		street = rec.solar_project_id.street
		street2 = house_number_or_name
		city = rec.solar_project_id.city
		state = rec.solar_project_id.state_id.name if rec.solar_project_id.state_id else '' 
		zip_list = rec.solar_project_id.zip
		country = rec.solar_project_id.country_id.name

		
		mail_values_user_check = {
			'subject': 'Customer Address' ,
			'email_from':from_mail,
			'email_to':from_to,
			'email_cc':admin_user.partner_id.email,
			'body_html': "<div> <b>Project </b>:- "+project_name+"<br/><b>Phone </b>:-"+custmer_phone+"<br/><b>Email </b>:-"+customer_email+"<br/><b>Contact Detail </b>:-"+street+", "+street2+", "+city+", "+state+", "+zip_list+", "+country+"</div>"
		}
		create_and_send_email = request.env['mail.mail'].sudo().create(mail_values_user_check).sudo().send()
		# if template:
		# 	mail = template.with_context(ctx).sudo().send_mail(rec.id,raise_exception=True)
		# 	mail_id = request.env['mail.mail'].sudo().search([('id','=',mail)])
		# 	if mail_id:
		# 		try:
		# 			res = mail_id.sudo().send()
		# 		except e:
		# 			print('\n mail sending Error ---')
			
		return request.redirect('/final/choosed')

	@http.route(['/final/choosed'], type='http', auth="public", website=True, sitemap=True)
	def FinalScreenProject(self, **post):
		return request.render('airbid_master.chosse_supplier_template',{})


	@http.route(['/supplier/profile'], type='http', auth="public", website=True, sitemap=True)
	def SupplierProfileUpdate(self,**post):
		print("SSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSs",post)
		user_id = request.env.user.partner_id
		state_id = request.env['res.country.state'].sudo().search([('code','ilike',post.get('profile_state')),('country_id','=','AU')],limit=1)
		if not post.get('current_paswd'):
			if post.get('is_detele') == 'true':
				print("ddvvvvvvvvvvvvvvvvvvvv")
				image_1920=False
			else:
				print("ssssssssssssvvvvvvvvvvvvvvvvvvvv")
				image_1920=base64.encodestring(post.get('profile_supp').read()) or user_id.image_1920
			print("saaaaaaaaaaaaaaaaaaaaaaaa",image_1920)

			user_id.sudo().write({'name':post.get('name') or request.env.user.name,
				'user_lastname':post.get('user_lastname') or request.env.user.user_lastname,
				'email':post.get('email') or request.env.user.email,
				'phone':post.get('phone') or request.env.user.phone,
				'abn':str(post.get('ABN')) or request.env.user.abn,
				'company_name':post.get('company_name') or request.env.user.company_name,
				'year':post.get('yearpicker') or request.env.user.year,
				'trading_name':post.get('trading_name') or request.env.user.trading_name,
				'about_com':post.get('about_the_company') or request.env.user.about_com,
				'website':post.get('website') or request.env.user.website,
				'city':post.get('profile_city') or request.env.user.city,
				'street':post.get('head_office_address') or request.env.user.street,
				'street2':post.get('head_office_address_more') or request.env.user.street2,
				'zip':post.get('profile_postal_code') or request.env.user.zip,
				'state_id':state_id.id or request.env.user.state_id,
				'residential':post.get('directors_residential') or request.env.user.residential,
				'commercial':post.get('directors_commercial') or request.env.user.commercial,
				'director_fname':post.get('directors_supplier_firstname') or request.env.user.director_fname,
				'director_lname':post.get('directors_supplier_lastname') or request.env.user.director_lname,
				'birth_date':post.get('date_of_birth') or request.env.user.birth_date,
				'mobile_no':post.get('directors_mobile') or request.env.user.mobile_no,
				'company_logo':base64.encodestring(post.get('comapany_logo').read()) or request.env.user.company_logo,
				'photo':base64.encodestring(post.get('directors_photo').read()) or request.env.user.photo,
				'retailer':base64.encodestring(post.get('cec_retailer').read()) or request.env.user.retailer,
				'member':base64.encodestring(post.get('cec_member').read()) or request.env.user.member,
				'iso':base64.encodestring(post.get('ios_certification').read()) or request.env.user.iso,
				'document':base64.encodestring(post.get('other_certification').read()) or request.env.user.document,
				# 'image_1920':base64.encodestring(post.get('profile_supp').read()) or user_id.image_1920,
				'image_1920':image_1920,
				'company_type':post.get('category') or request.env.user.company_type,
				'retailer_name':post.get('input_name') or request.env.user.retailer_name,			
				'member_name':post.get('member_name') or request.env.user.member_name,
				'iso_name':post.get('iso_name') or request.env.user.iso_name,
				'document_name':post.get('document_name') or request.env.user.document_name,
				'company_logo_name':post.get('company_logo_name') or request.env.user.company_logo_name,
				'photo_name':post.get('company_photo_name') or request.env.user.photo_name,
				})
			user_id.update({"profile_complete":True})

			area_operates_counter = post.get('area_operates_counter')
			if area_operates_counter:
				area_operates_list = []
				for d in range(1,int(area_operates_counter)+1):
					if post.get("area_operates_city"+str(d)) and post.get("redius_profile"+str(d)) and post.get("zip_code_no"+str(d)):
						area_operates_dist = {}
						area_operates_dist['city_area_name'] = post.get("area_operates_city"+str(d)) 	 
						area_operates_dist['radius_name'] = post.get("redius_profile"+str(d))
						area_operates_dist['zip_code'] = post.get("zip_code_no"+str(d))

						area_operates_list.append((0, 0,area_operates_dist))
				for area in user_id.area_operates_ids:
					area.sudo().unlink()
				user_id.sudo().write({'area_operates_ids':area_operates_list})
			zip_list = [ ]
			for area in user_id.area_operates_ids:
				headers = { 
				  "apikey": "57369f00-7e6a-11ec-ad8d-593482b86200"}

				params = (
				   ("code",area.zip_code),
				   ("radius",area.radius_name),
				   ("country","Au"),
				);
				response = requests.get('https://app.zipcodebase.com/api/v1/radius', headers=headers, params=params);
				dic = json.loads(response.text)
				for res in dic['results']:
					if not isinstance(res, str):
						if int(res.get('code')) not in zip_list:
							zip_list.insert(0,int(res.get('code')))
			user_id.sudo().write({'service_zip':zip_list})
			return request.redirect('/my/profile')

		else:	
			# if post.get('current_paswd'):
			request.env['res.users'].change_password(post.get('current_paswd'), post.get('new_paswd'))
			return request.redirect('/web/login')

	@http.route(['/contactus'], type='http', auth="public", website=True, sitemap=True)
	def SupplierContactDetail(self, **post):
		is_customer = False 
		if post.get('type') == 'customer':
			is_customer = True 
		return request.render('airbid_master.contact_us_detail',{"is_customer":is_customer,"contact_us_detail":True})		

	@http.route(['/send/contact'], type='http', auth="public", website=True, sitemap=True)
	def ContactDetail(self, **post):
		admin_user = request.env['res.users'].sudo().search([('is_admin', '=' , True)])

		for res in admin_user:
			from_mail = res.partner_id.email
			mail_values_user_check = {
				'subject': 'Contact Us' ,
				'email_to':from_mail,
				'email_from':post.get('contact_email_address'),
				'body_html': "<div> "+post.get('contact_first_name')+" "+post.get('contact_last_name')+" has contacted you. Their email is "+post.get('contact_email_address')+" and contact detail is "+post.get('contact_phone_number')+" <br></br> And the user message for you is ,  "+post.get('contact_your_message')+" </div>",
			}
			create_and_send_email = request.env['mail.mail'].sudo().create(mail_values_user_check).sudo().send()
		return request.redirect('/contactus')
	
	@http.route('/shop/payment/validate', type='http', auth="public", website=True, sitemap=False)
	def payment_validate(self, transaction_id=None, sale_order_id=None, **post):
		""" Method that should be called by the server when receiving an update
		for a transaction. State at this point :

		 - UDPATE ME
		"""
		if sale_order_id is None:
			order = request.website.sale_get_order()
		else:
			order = request.env['sale.order'].sudo().browse(sale_order_id)
			assert order.id == request.session.get('sale_last_order_id')

		if transaction_id:
			tx = request.env['payment.transaction'].sudo().browse(transaction_id)
			assert tx in order.transaction_ids()
		elif order:
			tx = order.get_portal_last_transaction()
		else:
			tx = None

		if not order or (order.amount_total and not tx):
			return request.redirect('/shop')

		if order and not order.amount_total and not tx:
			order.with_context(send_email=True).action_confirm()
			for line in order.order_line:
				if line.product_id.installer_solar_id:
					state='draft'
					if line.product_id.bid_data:
						bid_data = ast.literal_eval(line.product_id.bid_data)
						bid=request.env['installer.bid'].sudo().create(bid_data)
						emails_list=[]
						emails_list.append(request.env.ref('base.partner_admin').sudo().email)
						emails_list.append(request.env.user.email)
						mail_values = {
							'subject': 'BID Created with Project( '+str(line.product_id.name) +')' ,
							# 'partner_to' :  self.partner_id.name,
							'body_html': "BID description:= " + str(bid_data['bid_description']) + " Price:= " + str(bid_data['price']) + ".",
							#'record_name': record_id.customer_project_name,
							#'email_to':'ritisha.spellbound@gmail.com',
							'email_cc':", ".join(emails_list),
							'email_to':", ".join(emails_list),
							'email_from': request.env.user.email,
						}
						create_and_send_email = request.env['mail.mail'].sudo().create(mail_values)
						create_and_send_email.sudo().send()
						state="open"
						line.product_id.installer_solar_id.project_state = "inprogress"
						line.product_id.installer_solar_id.bid_paid_order_id = order.id
					else:
						emails_list=[]
						emails_list.append(request.env.ref('base.partner_admin').sudo().email)
						emails_list.append(request.env.user.email)
						mail_values = {
							'subject': str(line.product_id.installer_solar_id.customer_project_name) ,
							# 'partner_to' :  self.partner_id.name,
							'body_html': "Project " + str(line.product_id.installer_solar_id.customer_project_name) + " is Publish by " + str(request.env.user.name) + ".",
							#'record_name': record_id.customer_project_name,
							#'email_to':'ritisha.spellbound@gmail.com',
							'email_cc':", ".join(emails_list),
							'email_to':", ".join(emails_list),
							'email_from': request.env.user.email,
						}
						create_and_send_email = request.env['mail.mail'].sudo().create(mail_values)
						create_and_send_email.sudo().send()
					line.product_id.installer_solar_id.update({"project_state":"inprogress","installer_project_state":state,"paid_order_id":order.id})
			return request.redirect(order.get_portal_url())

		# clean context and session, then redirect to the confirmation page
		request.website.sale_reset()
		if tx and tx.state == 'draft':
			return request.redirect('/shop')

		PaymentProcessing.remove_payment_transaction(tx)
		return request.redirect('/shop/confirmation')

	@http.route(['/shop/confirmation'], type='http', auth="public", website=True, sitemap=False)
	def payment_confirmation(self, **post):
		print("<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<")
		sale_order_id = request.session.get('sale_last_order_id')
		if sale_order_id:
			sale_order = request.env['sale.order'].search([('id','=',sale_order_id)])
			user_id = request.env.user.partner_id
			for sale in sale_order.order_line:
				product_id = sale.product_id.id
			ppb_product = request.env['product.product'].search([('name','=','Pay Per Bid')])
			bb10_product = request.env['product.product'].search([('name','=','10 Bid Bulk')])
			bb20_product = request.env['product.product'].search([('name','=','20 Bid Bulk')])
			bb30_product = request.env['product.product'].search([('name','=','30 Bid Bulk')])
			monthly_product = request.env['product.product'].search([('name','=','Monthly Billing Plan')])
			bid_count = user_id.bid_count
			if int(product_id) == ppb_product.id:
				if user_id.bid_count > 0:
					user_id.sudo().write({'per_bid':True,'per10_bid':False,'per20_bid':False,'per30_bid':False,'bid_count':bid_count+1})
				else:
					user_id.sudo().write({'per_bid':True,'bid_count':1})


			elif int(product_id) == bb10_product.id:
				if user_id.bid_count > 0:
					user_id.sudo().write({'per10_bid':True,'per_bid':False,'per20_bid':False,'per30_bid':False,'bid_count':bid_count+10})
				else:
					user_id.sudo().write({'per10_bid':True,'bid_count':10})

			elif int(product_id) == bb20_product.id:
				if user_id.bid_count > 0:
					user_id.sudo().write({'per20_bid':True,'per_bid':False,'per10_bid':False,'per30_bid':False,'bid_count':bid_count+20})
				else:
					user_id.sudo().write({'per20_bid':True,'bid_count':20})

			elif int(product_id) == bb30_product.id:
				if user_id.bid_count > 0:
					user_id.sudo().write({'per30_bid':True,'per_bid':False,'per10_bid':False,'per20_bid':False,'bid_count':bid_count+30})
				else:
					user_id.sudo().write({'per30_bid':True,'bid_count':30})

			elif int(product_id) == monthly_product.id:
				user_id.sudo().write({'monthly_bid':True,'plan_start_date':date.today(),'plan_end_date':date.today()+relativedelta(months=1)})

			order = request.env['sale.order'].sudo().browse(sale_order_id)
			for line in order.order_line:
				if line.product_id.installer_solar_id:
					state='draft'
					if line.product_id.bid_data:
						bid_data = ast.literal_eval(line.product_id.bid_data)
						bid=request.env['installer.bid'].sudo().create(bid_data)
						emails_list=[]
						emails_list.append(request.env.ref('base.partner_admin').sudo().email)
						emails_list.append(request.env.user.email)
						mail_values = {
							'subject': 'BID Created with Project( '+str(line.product_id.name) +')' ,
							# 'partner_to' :  self.partner_id.name,
							'body_html': "BID description:= " + str(bid_data['bid_description']) + " Price:= " + str(bid_data['price']) + ".",
							#'record_name': record_id.customer_project_name,
							#'email_to':'ritisha.spellbound@gmail.com',
							'email_cc':", ".join(emails_list),
							'email_to':", ".join(emails_list),
							'email_from': request.env.user.email,
						}
						create_and_send_email = request.env['mail.mail'].sudo().create(mail_values)
						create_and_send_email.sudo().send()
						state="open"
						line.product_id.installer_solar_id.project_state = "inprogress"
						line.product_id.installer_solar_id.bid_paid_order_id = order.id
					else:
						emails_list=[]
						emails_list.append(request.env.ref('base.partner_admin').sudo().email)
						emails_list.append(request.env.user.email)
						mail_values = {
							'subject': str(line.product_id.installer_solar_id.customer_project_name) ,
							# 'partner_to' :  self.partner_id.name,
							'body_html': "Project " + str(line.product_id.installer_solar_id.customer_project_name) + " is Publish by " + str(request.env.user.name) + ".",
							#'record_name': record_id.customer_project_name,
							#'email_to':'ritisha.spellbound@gmail.com',
							'email_cc':", ".join(emails_list),
							'email_to':", ".join(emails_list),
							'email_from': request.env.user.email,
						}
						create_and_send_email = request.env['mail.mail'].sudo().create(mail_values)
						create_and_send_email.sudo().send()
					line.product_id.installer_solar_id.update({"installer_project_state":state,"paid_order_id":order.id})
										
			return request.render("website_sale.confirmation", {'order': order})
		else:
			return request.redirect('/shop')

	@http.route('/timer/out/state', type='json', auth="public")
	def Timeoutsate(self,proid):
		data = request.env['solar.system'].sudo().search([('id', '=', int(proid))])
		if data:
			data.sudo().write({'customer_project_state':'inprogress'})
			return True

	@http.route('/geo/long_late/postal', type='json', auth="public")
	def _geo_long_late_postal(self,address_detail):
		""" Map Circle Radius"""
		geocoder_obj = request.env['base.geocoder']
		add_detail_lon_lat = []
		for add in address_detail:
			city = add.get('city')
			zip = add.get('zipcode')
			country = 'AU'

			search = geocoder_obj.sudo().geo_query_address(street=None, zip=zip, state=None, country=country)
			# search = geocoder_obj.sudo().geo_query_address(street=None, zip=zip, city=city, state=None, country=country)
			geo = geocoder_obj.sudo().geo_find(search)

			if geo:
				add['lat'] = geo[0] if geo else 0
				add['lng'] = geo[1] if geo else 0
			else:
				search = geocoder_obj.sudo().geo_query_address(street=None, zip=None, city=None, state=None, country=None)
				geo = geocoder_obj.sudo().geo_find(search)
				add['lat'] = geo[0] if geo else 0
				add['lng'] = geo[1] if geo else 0

			add_detail_lon_lat.append(add)											

		# Updating Area Address On user Customer --
		user_id = request.env.user.partner_id
		for area in user_id.area_operates_ids:
			area.sudo().unlink()

		area_operates_list = []
		for area_op in add_detail_lon_lat:
			area_op_dict = {}
			area_op_dict['city_area_name'] = area_op.get('city') 
			area_op_dict['radius_name'] = area_op.get('km')
			area_op_dict['zip_code'] = area_op.get('zipcode')
			area_operates_list.append((0, 0,area_op_dict))

		user_id.sudo().write({'area_operates_ids':area_operates_list})
		# Updating Area Address On user Customer --

		return {'address_detail':add_detail_lon_lat}

	@http.route(['/supplier/view/bid'], type='http', auth="public", website=True, sitemap=True)
	def SupplierDataDetailBID(self,bid_id=None, **post):
		if bid_id:
			img_id = {}
			data = request.env['solar.supplier'].sudo().search([('id','=',int(bid_id))])
		else:
			data = request.env['solar.supplier'].sudo().search([('id','=',int(post.get('record_id')))])
			img_id = request.env['solar.system'].sudo().search([('id','=',int(post.get('project_img')))])
		return request.render('airbid_master.supplier_data_detail_only_bid',{'data':data,'img_id':img_id})

	# ++++++++++++SUPPLIER AS CUSTOMER +++++++++++++==
	
	@http.route(['/installer/customer'], type='http', auth="public", website=True, sitemap=False,csrf=False)
	def supplier_as_customer(self, **post):
		user_id= request.env.user.partner_id
		order = request.website.sale_get_order()
		if order.state == 'draft':
			for line in order.order_line:
				if line.product_id.installer_solar_id:
					line.sudo().unlink()
		else:
			request.website.sale_reset()
				#order._cart_update(product_id=line.product_id.id, set_qty=0)
		data = request.env['installation.solar.system'].sudo().search([('supplier_customer_id.id','=',request.env.user.partner_id.id)],order="create_date desc")
		return request.render("airbid_master.supplier_as_customer_deshboard", {'is_customer': True,'data':data})

	@http.route(['/installer/review/bid'], type='http', auth="public", website=True, sitemap=False,csrf=False)
	def supplier_as_customer_review_bid(self,record_id=None, **post):
		data = request.env['installation.solar.system'].sudo().search([('id','=',record_id)])
		is_alredy_bid=False
		for bid in data.installer_bids_ids:
			if bid.customer_id.id == request.env.user.partner_id.id:
				is_alredy_bid=bid.id
				#bid_id=bid.id
		return request.render("airbid_master.my_solar_information_bid",{'is_alredy_bid': is_alredy_bid,'record_id':data,'rec_id':data})

	@http.route(['/installer/review'], type='http', auth="public", website=True, sitemap=False,csrf=False)
	def supplier_as_customer_review(self,sort=None,record_id=None, **post):
		bid_data=[]
		user_id = request.env.user.partner_id
		is_edit=False
		if user_id.is_supplier == 'installer':
			is_edit=True
		
		data = request.env['installation.solar.system'].sudo().search([('id','=',record_id)])
		for bid in data.installer_bids_ids:
			bid_data.append({'supplier':bid.customer_id.name,'id':bid.id,'des':bid.bid_description,'price':bid.price,'retailer':bid.customer_id.retailer,'member':bid.customer_id.member,'iso':bid.customer_id.iso,'document':bid.customer_id.document})
		if sort == 'low_price':
			bid_data=sorted(bid_data, key = itemgetter('price'))
		elif sort == 'high_price':
			bid_data=sorted(bid_data, key = itemgetter('price'),reverse=True)
		else:
			pass
		return request.render("airbid_master.my_solar_information",{'is_edit':is_edit,'is_customer': True,'record_id':data,'rec_id':data,'bid_data':bid_data})
		#return request.render("airbid_master.supplier_as_customer_deshboard", {'is_customer': True,'data':data})	
	
	@http.route(['/submit/state/bid'], type='http', auth="public", website=True, sitemap=False,csrf=False)
	def BidDetailssubmit(self, **post):
		pro_id=request.env['installer.bid'].sudo().search([('id','=',int(post.get('record_id')))])
		pro_id.project_id.update({'installer_project_state':'close'})
		pro_id.update({'project_state':'won'})
		for pro in pro_id.project_id.installer_bids_ids:
			if pro.id != int(post.get('record_id')):
				pro.update({'project_state':'lost'})

		emails_list=[]
		user=request.env.user
		emails_list.append(request.env.ref('base.partner_admin').sudo().email)
		emails_list.append(user.email)
		emails_list.append(pro_id.customer_id.email)
		mail_values = {
			'subject': 'BID Submited ...( '+str(pro_id.bid_description) +')' ,
			'body_html': "<div><h3><u>BID installer Details</u></h3>Name     := " + str(pro_id.customer_id.name) + ".</br> Address := "+str('%s, %s %s, %s' % (pro_id.customer_id.street or '', pro_id.customer_id.city or '', pro_id.customer_id.zip or '', pro_id.customer_id.country_id and pro_id.customer_id.country_id.display_name or ''))+".</br>Phone   := "+str(pro_id.customer_id.phone)+".</br> Email     := "+str(pro_id.customer_id.email)+".</br></br><h3><u>Supplier Details</u></h3></br>Name     := "+str(user.name)+" </br>Address := "+str('%s, %s %s, %s' % (user.street or '', user.city or '', user.zip or '', user.country_id and user.country_id.display_name or ''))+".</br>Phone   := "+str(user.phone)+".</br>Email     := "+str(user.email)+"</div>",
			'email_cc':", ".join(emails_list),
			'email_to':", ".join(emails_list),
			'email_from': user.email,
		}
		create_and_send_email = request.env['mail.mail'].sudo().create(mail_values)
		create_and_send_email.sudo().send()
		return request.render('airbid_master.submit_project_bid_form')

	
	@http.route(['/bid/details'], type='http', auth="public", website=True, sitemap=False,csrf=False)
	def BidDetails(self, **post):
		data=request.env['installer.bid'].sudo().search([('id','=',int(post.get('record_id')))])
		is_installer=False
		if post.get('is_installer'):
			is_installer=True
		return request.render('airbid_master.bid_data_details',{'data':data,'is_installer':is_installer,'record_id':data.project_id.id})
	
	@http.route(['/customer/project'], type='http', auth="public", website=True, sitemap=False,csrf=False)
	def supplier_as_customer_project(self, **post):
		return request.render("airbid_master.my_project_form_as_customer",{'is_customer': True})

	@http.route(['/customer/address'], type='http', auth="public", website=True, sitemap=False,csrf=False)
	def supplier_customer_address_form(self, record_id=None,*args,**post):
		model_id = request.env['installation.solar.system']
		user_id = request.env.user.partner_id
		countries = request.env['res.country'].sudo().search([])
		states = request.env['res.country.state'].sudo().search([('country_id.code','ilike','AU')])
		if record_id:
			rec_id = request.env['installation.solar.system'].sudo().search([('id','=',record_id)])
			record_id = rec_id
			request.session['address'] = record_id.multiple_address
			address = record_id.multiple_address
		else:
			request.session['address'] = ''
			record_id = model_id.sudo().create({'supplier_customer_id' : user_id.id})
			rec_id = record_id
		# return request.render('airbid_master.customer_address_form',{'record_id':record_id.id,'states': states,'rec_id':rec_id})
		return request.render("airbid_master.supplier_customer_address_form",{'is_customer': True,'record_id':record_id.id,'states': states,'rec_id':rec_id})

	@http.route(['/solar/panels'], type='http', auth="public", website=True, sitemap=False,csrf=False)
	def my_solar_panals(self,record_id=None, **post):
		if post:
			state_id = request.env['res.country.state'].sudo().search([('code','ilike',post.get('state')),('country_id','=','AU')],limit=1)
			record_id = request.env['installation.solar.system'].sudo().search([('id','=',record_id)])
			record_id.write({'customer_project_name': post.get('project_name') or record_id.customer_project_name,
				'email_id':post.get('customer_email') or record_id.email_id,
				'phone':post.get('phone') or record_id.phone,
				'multiple_address':post.get('multiple_address') or record_id.multiple_address,
				'street':post.get('address_line_1') or record_id.street,
				'house_number_or_name':post.get('address_line_2') or record_id.house_number_or_name,
				'state_id':state_id.id or record_id.state_id,
				'city':post.get('customer_city') or record_id.city,
				'zip':post.get('customer_zip') or record_id.zip,
				'let':post.get('let_address') or record_id.let,
				'leng':post.get('long_address') or record_id.leng,
				'address_line_1':post.get('address_line_1') or record_id.address_line_1,
				'address_line_2':post.get('address_line_2') or record_id.address_line_2,
			})
		
		else:
			state_id = {}
			record_id = request.env['installation.solar.system'].sudo().search([('id','=',record_id)])
		request.session['address'] = record_id.multiple_address

		return request.render("airbid_master.my_solar_panals",{'is_customer': True,'record_id':record_id.id,'rec_id':record_id,'address':record_id.multiple_address})

	@http.route(['/panals/inventer'], type='http', auth="public", website=True, sitemap=False,csrf=False)
	def my_solar_panals_inventer(self,record_id=None, **post):
		record_id = request.env['installation.solar.system'].sudo().search([('id','=',record_id)])
		record_id.write({'remove_existing_solar': post.get('int_remove_existing') or record_id.remove_existing_solar})
		# if post.get('int_remove_existing') == 'yes' or record_id.remove_existing_solar:
		img_data = request.env['image.selection'].sudo().search([('ques_id','=','nine')])
		if post.get('int_remove_existing') == 'yes':
			print("rrrrrrrrrrrrrrrrrrrrr")
			return request.render("airbid_master.my_solar_panals_inventer",{'is_customer': True,'record_id':record_id.id,'rec_id':record_id,'img_data':img_data})
		else:
			print("ddddddddddddddddddd")
			return request.render("airbid_master.my_solar_pv_installation",{'is_timer':True,'is_customer': True,'record_id':record_id.id,'rec_id':record_id,'img_data':img_data})

	@http.route(['/PV/installation'], type='http', auth="public", website=True, sitemap=False,csrf=False)
	def pv_installation(self,record_id=None, **post):
		print("lllllllllllllllllllllllllllllllllllllllllll",post)
		if post.get('pv_system') == 'no':
			if not post.get('recordback_id'):
				print("1111111")
				record_id = request.env['installation.solar.system'].sudo().search([('id','=',record_id)])
				record_id.write({'panels_remove': post.get('panels_remove') or record_id.panels_remove,
					# 'size_of_solar_system': post.get('size_of_solar_system') or record_id.size_of_solar_system,
					'remove_inverter_solar': post.get('inverter_property') or record_id.remove_inverter_solar,
					'pv_system_solar': post.get('pv_system') or record_id.pv_system_solar,
					'house_pic':base64.encodestring(post.get('ins_house_attachment').read()) or record_id.house_pic,
					'house_name':post.get('house_name') or record_id.house_name,
					'roof_layout':base64.encodestring(post.get('ins_image_of_roof').read()) or record_id.roof_layout,
					'roof_name':post.get('roof_name') or record_id.roof_name,
					'roof_title_pic':base64.encodestring(post.get('ins_image_of_meter_box').read()) or record_id.roof_title_pic,
					'meter_name':post.get('meter_name') or record_id.meter_name,
					'is_complate':True,

					})
				img_data = request.env['image.selection'].sudo().search([('ques_id','=','nine')])
				return request.render("airbid_master.my_solar_information",{'is_project': True,'record_id':record_id,'rec_id':record_id,'img_data':img_data})
			else:
				img_data = request.env['image.selection'].sudo().search([('ques_id','=','nine')])
				record_id = request.env['installation.solar.system'].sudo().search([('id','=',int(post.get('recordback_id')))])
				return request.render("airbid_master.my_solar_pv_installation",{'is_customer': True,'record_id':record_id.id,'rec_id':record_id,'img_data':img_data})
		else:
			print("FFFFFFFFFFFFFFFFFF/////////////*********")
			img_data = request.env['image.selection'].sudo().search([('ques_id','=','nine')])
			record_id = request.env['installation.solar.system'].sudo().search([('id','=',record_id)])
			record_id.write({'panels_remove': post.get('panels_remove') or record_id.panels_remove,
				# 'size_of_solar_system': post.get('size_of_solar_system') or record_id.size_of_solar_system,
				'hours_timer':post.get('hours_timer') or record_id.hours_timer,
				'remove_inverter_solar': post.get('inverter_property') or record_id.remove_inverter_solar,
				'pv_system_solar': post.get('pv_system') or record_id.pv_system_solar,
				})
			if post.get('hours_timer'):
				record_id.write({
					'con_hour':int(post.get('hours_timer')) * 24,
			    })
			return request.render("airbid_master.my_solar_pv_installation",{'is_customer': True,'record_id':record_id.id,'rec_id':record_id,'img_data':img_data})

	@http.route(['/battery/backup'], type='http', auth="public", website=True, sitemap=False,csrf=False)
	def my_solar_battery_backup(self,record_id=None, **post):
		record_id = request.env['installation.solar.system'].sudo().search([('id','=',record_id)])
		if post.get('int_remove_existing') == 'yes' or post.get('batteryback_up') == 'yes':
			record_id.write({'new_pv_system_installation': post.get('pv_system_property') or record_id.new_pv_system_installation,
				'panels_need': post.get('pv_system_need') or record_id.panels_need,
				'size_of_solar_system': post.get('size_of_solar_system') or record_id.size_of_solar_system,
				'panels_power_class': post.get('panel_power_class') or record_id.panels_power_class,
				'inverter_size': post.get('inventer_pv_size') or record_id.inverter_size,
				'single_three_ph': post.get('single_ph_three') or record_id.single_three_ph,
				'export_device': post.get('export_device') or record_id.export_device,
				'panels_tilts': post.get('panels_tilts') or record_id.panels_tilts,
				'clip_locks': post.get('clip_locks') or record_id.clip_locks,
				'storey': post.get('single_storey') or record_id.storey,
				'battery_backup': post.get('batteryback_up') or record_id.battery_backup,
				'roof_type': post.get('roof') or record_id.roof_type,
				'panels_tile_need':post.get('panels_tile_need') or record_id.panels_tile_need,
				'clip_locks_need':post.get('clip_locks_need') or record_id.clip_locks_need,
				'hours_timer':post.get('hours_timer') or record_id.hours_timer,
				# 'house_pic':base64.encodestring(post.get('ins_house_attachment').read()) or record_id.house_pic,
				# 'roof_layout':base64.encodestring(post.get('ins_image_of_roof').read()) or record_id.roof_layout,
				# 'roof_tile_pic':base64.encodestring(post.get('ins_image_of_meter_box').read()) or record_id.roof_tile_pic,
				})
			if post.get('hours_timer'):
				record_id.write({
				'con_hour':int(post.get('hours_timer')) * 24,
			     })

			return request.render("airbid_master.my_solar_battery_backup",{'is_customer': True ,'record_id':record_id,'rec_id':record_id,})
		elif post.get('pv_system_property') == 'no':
			record_id.write({
				'hours_timer':post.get('hours_timer') or record_id.hours_timer,
				'new_pv_system_installation': post.get('pv_system_property') or record_id.new_pv_system_installation
			})
			if post.get('hours_timer'):
				record_id.write({
				'con_hour':int(post.get('hours_timer')) * 24,
			     })
			return request.render("airbid_master.my_solar_battery_backup",{'is_customer': True,'record_id':record_id,'rec_id':record_id,})
		elif post.get('int_remove_existing') == 'no':
			return request.render("airbid_master.my_solar_battery_backup",{'is_customer': True,'record_id':record_id,'rec_id':record_id,})
		elif post.get('batteryback_up') == 'no':
			record_id.write({
				'new_pv_system_installation': post.get('pv_system_property') or record_id.new_pv_system_installation,
				'size_of_solar_system': post.get('size_of_solar_system') or record_id.size_of_solar_system,
				'panels_need': post.get('pv_system_need') or record_id.panels_need,
				'panels_power_class': post.get('panel_power_class') or record_id.panels_power_class,
				'inverter_size': post.get('inventer_pv_size') or record_id.inverter_size,
				'single_three_ph': post.get('single_ph_three') or record_id.single_three_ph,
				'battery_backup': post.get('batteryback_up') or record_id.battery_backup,
				'export_device': post.get('export_device') or record_id.export_device,
				'panels_tilts': post.get('panels_tilts') or record_id.panels_tilts,
				'clip_locks': post.get('clip_locks') or record_id.clip_locks,
				'storey': post.get('single_storey') or record_id.storey,
				'battery_backup': post.get('batteryback_up') or record_id.battery_backup,
				'roof_type': post.get('roof') or record_id.roof_type,
				'panels_tile_need':post.get('panels_tile_need') or record_id.panels_tile_need,
				'clip_locks_need':post.get('clip_locks_need') or record_id.clip_locks_need,
				'house':base64.encodestring(post.get('house_attachment').read()) or record_id.house,
				'house_name_up':post.get('house_name') or record_id.house_name_up,
				'roof':base64.encodestring(post.get('image_of_meter_box').read()) or record_id.roof,
				'roof_nm':post.get('meter_name') or record_id.roof_nm,
				'roof_name_up':post.get('roof_name') or record_id.roof_name_up,
				'roof_tile_pic':base64.encodestring(post.get('image_of_roof').read()) or record_id.roof_tile_pic,
				'meter_box':base64.encodestring(post.get('meter_zoomin').read()) or record_id.meter_box,
				'meter_box_up':post.get('meter_zoomin_input') or record_id.meter_box_up,
				'meter_box_2':base64.encodestring(post.get('meter_zoomout').read()) or record_id.meter_box_2,
				'meter_box_2_name':post.get('meter_zoomout_input') or record_id.meter_box_2_name,
				#'battery_need_install':base64.encodestring(post.get('pic_battery_need').read()) or record_id.battery_need_install,
				'inverter_wall':base64.encodestring(post.get('meter_box_wall_pic').read()) or record_id.inverter_wall,
				'inverter_wall_name':post.get('meter_name_box_wall_pic') or record_id.inverter_wall_name,
				'is_complate':True,
				
				})
			
			return request.render("airbid_master.my_solar_information",{'is_edit': True,'record_id':record_id,'rec_id':record_id,})	

		# 	return request.render("airbid_master.my_solar_information",{'is_customer': True})
		# else:
		# 	return request.render("airbid_master.my_solar_battery_backup",{'is_customer': True})

	@http.route(['/information'], type='http', auth="public", website=True, sitemap=True,csrf=False)
	def my_solar_information(self,record_id=None, **post):
		record_id = request.env['installation.solar.system'].sudo().search([('id','=',record_id)])

		if post.get('record_id'):
			record_id =request.env['installation.solar.system'].sudo().search([('id','=',int(post.get('record_id')))])
			return request.render("airbid_master.my_solar_information",{'is_infopage':True,'is_customer': True,'record_id':record_id,'rec_id':record_id})

		record_id.write({
				'battery_backup_second': post.get('battery_sup_backup') or record_id.battery_backup_second,
				'battery_size': post.get('ins_battery_size') or record_id.battery_size,
				'battery_model_no': post.get('ins_battery_model_no') or record_id.battery_model_no,
				'battery_brand': post.get('ins_battery_brand') or record_id.battery_brand,
				'house':base64.encodestring(post.get('house_attachment').read()) or record_id.house,
				'roof':base64.encodestring(post.get('image_of_meter_box').read()) or record_id.roof,
				'roof_tile_pic':base64.encodestring(post.get('image_of_roof').read()) or record_id.roof_tile_pic,
				'meter_box':base64.encodestring(post.get('meter_zoomin').read()) or record_id.meter_box,
				'meter_box_2':base64.encodestring(post.get('meter_zoomout').read()) or record_id.meter_box_2,
				'battery_need_install':base64.encodestring(post.get('pic_battery_need').read()) or record_id.battery_need_install,
				'inverter_wall':base64.encodestring(post.get('meter_box_wall_pic').read()) or record_id.inverter_wall,
				'battery_need_install_name':post.get('pic_battery_need_input') or record_id.battery_need_install_name,
				'house_name_up':post.get('house_name') or record_id.house_name_up,
				'roof_nm':post.get('meter_name') or record_id.roof_nm,
				'roof_name_up':post.get('roof_name') or record_id.roof_name_up,
				'meter_box_up':post.get('meter_zoomin_input') or record_id.meter_box_up,
				'meter_box_2_name':post.get('meter_zoomout_input') or record_id.meter_box_2_name,
				'inverter_wall_name':post.get('meter_name_box_wall_pic') or record_id.inverter_wall_name,
				'is_complate':True,
			})
		return request.render("airbid_master.my_solar_information",{'is_infopage':True,'is_customer': True,'record_id':record_id,'rec_id':record_id})
		# return request.render("airbid_master.my_solar_information",{'is_customer': True})

	@http.route('/create/bid', auth='public', type='http',website=True,csrf=False)
	def create_website_bid(self,record_id=None,**post):
		if not record_id and post.get('record_id'):
			record_id=int(post.get('record_id'))
		record_id = request.env['installation.solar.system'].sudo().search([('id','=',record_id)])
		bid_id=False
		if post.get('is_alredy_bid'):
			bid_id=request.env['installer.bid'].sudo().browse(int(post.get('is_alredy_bid')))
		return request.render('airbid_master.cretae_bid',{'is_customer': True,'record_id':record_id.id,'rec_id':record_id,'bid_id':bid_id})

	@http.route('/create/bid/submit', auth='public', type='http',website=True,csrf=False)
	def create_submitwebsite_bid(self,record_id=None,**post):
		record_id = request.env['installation.solar.system'].sudo().search([('id','=',record_id)])
		if post.get('bid_id'):
			request.env['installer.bid'].sudo().search([('id','=',int(post.get('bid_id')))]).update({'bid_description':post.get('description'),'price':post.get('Price')})
			bid=request.env['installer.bid'].sudo().browse(int(post.get('bid_id')))
			emails_list=[]
			emails_list.append(request.env.ref('base.partner_admin').sudo().email)
			emails_list.append(request.env.user.email)

			mail_values = {
				'subject': 'BID Edited with Project( '+str(record_id.customer_project_name) +')' ,
				# 'partner_to' :  self.partner_id.name,
				'body_html': "BID description:= " + str(bid.bid_description) + " Price:= " + str(bid.price) + ".",
				#'record_name': record_id.customer_project_name,
				#'email_to':'ritisha.spellbound@gmail.com',
				'email_cc':", ".join(emails_list),
				'email_to':", ".join(emails_list),
				'email_from': request.env.user.email,
			}
			create_and_send_email = request.env['mail.mail'].sudo().create(mail_values)
			create_and_send_email.sudo().send()
			return request.render('airbid_master.submit_project_bid_form',{'is_customer': True,'record_id':record_id.id,'rec_id':record_id})
		else:
			# record_id = request.env['installation.solar.system'].sudo().search([('id','=',record_id)])
			bid_data={}
			bid_data['customer_id']=request.env.user.partner_id.id
			bid_data['project_id']=int(record_id)
			bid_data['bid_description']=post.get('description')
			bid_data['price']=post.get('Price')
			bid_data['project_state']='inprogress'
			
			is_product=request.env['product.template'].sudo().search([('installer_solar_id','=',record_id.id)])
			if not record_id.bid_paid_order_id:
				product_id=False
				if not is_product and record_id:
					product_data={}
					product_data['name']=record_id.customer_project_name
					product_data['standard_price']=10.0
					product_data['list_price']= 10.0
					product_data['uom_id']=request.env.ref('uom.product_uom_unit').id
					product_data['uom_po_id']=request.env.ref('uom.product_uom_unit').id
					product_data['sale_ok']=True
					product_data['installer_solar_id']=record_id.id
					product_data['bid_data']=str(bid_data)
					product_id=request.env['product.template'].sudo().create(product_data)
					record_id.project_state = "inprogress"
				else:
					is_product.bid_data=str(bid_data)
					is_product.standard_price=10.0
					is_product.list_price=10.0
					product_id=is_product
					record_id.project_state = "inprogress"

				order = request.website.sale_get_order(force_create=1)
				if order.state != 'draft':
					request.website.sale_reset()
					return {}

				order._cart_update(product_id=product_id.product_variant_ids[0].id, add_qty=1, set_qty=1)
			
				return request.redirect("/shop/cart")
			else:
				return request.render('airbid_master.submit_project_bid_form',{'is_customer': True,'record_id':record_id.id,'rec_id':record_id})

			# record_id.project_state = "inprogress"
			# record_id.installer_project_state = "inprogress"
		# 	bid=request.env['installer.bid'].sudo().create(bid_data)
		# 	emails_list=[]
		# 	emails_list.append(request.env.ref('base.partner_admin').sudo().email)
		# 	emails_list.append(request.env.user.email)

		# 	mail_values = {
		# 		'subject': 'BID Created with Project( '+str(record_id.customer_project_name) +')' ,
		# 		# 'partner_to' :  self.partner_id.name,
		# 		'body_html': "BID description:= " + str(bid.bid_description) + " Price:= " + str(bid.price) + ".",
		# 		#'record_name': record_id.customer_project_name,
		# 		#'email_to':'ritisha.spellbound@gmail.com',
		# 		'email_cc':", ".join(emails_list),
		# 		'email_to':", ".join(emails_list),
		# 		'email_from': request.env.user.email,
		# 	}
		# 	create_and_send_email = request.env['mail.mail'].sudo().create(mail_values)
		# 	create_and_send_email.sudo().send()

		# return request.render('airbid_master.submit_project_bid_form',{'is_customer': True,'record_id':record_id,'rec_id':record_id})

	@http.route('/submit/bid', auth='public', type='http',website=True,csrf=False)
	def submit_website_bid(self,record_id=None,**post):
		record_id = request.env['installation.solar.system'].sudo().search([('id','=',record_id)])
		is_product=request.env['product.template'].sudo().search([('installer_solar_id','=',record_id.id)])
		if not record_id.bid_paid_order_id:
			product_id=False
			if not is_product and record_id:
				product_data={}
				product_data['name']=record_id.customer_project_name
				product_data['standard_price'] = 15.0
				product_data['list_price'] = 15.0
				product_data['uom_id'] = request.env.ref('uom.product_uom_unit').id
				product_data['uom_po_id'] = request.env.ref('uom.product_uom_unit').id
				product_data['sale_ok'] = True
				product_data['installer_solar_id']=record_id.id
				product_id=request.env['product.template'].sudo().create(product_data)
			else:
				product_id=is_product

			order = request.website.sale_get_order(force_create=1)
			if order.state != 'draft':
				request.website.sale_reset()
				return {}

			order._cart_update(product_id=product_id.product_variant_ids[0].id, add_qty=1, set_qty=1)
		
			return request.redirect("/shop/cart?is_customer=True")
		else:
			return request.render('airbid_master.submit_project_bid_form',{'is_customer': True,'record_id':record_id.id,'rec_id':record_id})
