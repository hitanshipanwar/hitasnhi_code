from odoo import fields,api,models,_

class ProductBid(models.Model):
	_inherit ='product.template'

	# if this true then  only Bid product visible in mambership menu.........
	bid_product = fields.Boolean(string="Bid Product")
	installer_solar_id=fields.Many2one('installation.solar.system')
	bid_data=fields.Char()
	
class ImageSelection(models.Model):
	_name="image.selection"
	_description="Image Selection"

	ques_id = fields.Selection([('five','5'),('six','6'),('seven','7'),('eight','8'),('nine','9')],string="Question Number")
	choose_img_id = fields.Many2many('ir.attachment',string="Choose Image")
	solar_type = fields.Selection([('top','Top Quality (Most expensive)'),('standard','Standard quality at good price')])
	inverter_type = fields.Selection([('top','Top Quality (Most expensive)'),('std','Standard quality at good price'),('micro','Micro Inverters')])
	property_type = fields.Selection([('stand','Stand-alone home'),('town','Townhouse'),('villa','Villa'),('apart','Apartment'),('commer','Commercial / Business site')])
	story_no = fields.Selection([('singal','Single story'),('double','Double story'),('trippel','Triple  story'),('other','Other')])
	roof_type = fields.Selection([('tin','Tin / Coulourbond'),('terr','Terracotta'),('tile','Tile'),('slate','Slate'),('asbestos','Asbestos'),('flat','Flat'),('other','Other')])
