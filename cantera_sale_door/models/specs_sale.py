# -*- coding: utf-8 -*-

from odoo import _, api, fields, models

import logging

_logger =logging.getLogger(__name__)

class SpecsSale(models.Model):
	_name = 'specs.sale'
	_inherit = ['mail.thread', 'mail.activity.mixin']
	_rec_name = 'name_specs'


	stage_id = fields.Many2one(
        'specs.type',
        string='Etapa',
        group_expand='_read_group_stage_ids',
        default=lambda self: self._select_state()
    )
	state = fields.Selection(
		selection=[
            ('errase', 'Borrador'),
            ('price', 'Precio Actualizado'),
            ('bom', 'Bom Creado'),
            ('cancel', 'Cancelado')
        ],
        string="Estado", readonly=True,
        compute='_change_state'
	)
	specs_type = fields.Selection(
		[('door', 'Puerta'),
		('windows', 'Ventana'),
		('railing', 'Barandal')],
		string='Tipo de Producto',
	)
	specs_sale_id = fields.Many2one(
		'sale.order',
		string='Cotización'
	)
	specs_amount_total = fields.Float(
    	string='Precio Total',
    )
	specs_leads_id = fields.Many2one(
		'crm.lead',
		string='guia'
	)
	specs_product_id = fields.Many2one(
		'door.family',
		string='Familia de producto'
	)
	specs_dc_id = fields.Many2one(
		'door.configuration',
		string='Configuración de Producto'
	)
	specs_design_id = fields.Many2one(
		'door.design',
		string='Diseño'
	)
	specs_level_id = fields.Many2one(
		'door.level',
		string='Nivel de Complejidad'
	)
	specs_mtrs = fields.Float(
    	string='Metros Cuadrados',
     	digits=(12, 4)
    )
	specs_suffix_id = fields.Many2one(
		'door.suffix',
		string='Sufijo'
	)
	specs_ant = fields.Float(
    	string='Ancho Total',
     	digits=(12, 4)
    )
	specs_alt = fields.Float(
    	string='Altura Total',
     	digits=(12, 4)
    )
	specs_antmarc = fields.Float(
    	string='Ancho con Marco',
     	digits=(12, 4)
    )
	specs_altmarc = fields.Float(
    	string='Altura con Marco',
     	digits=(12, 4)
    )
	specs_bast = fields.Float(
    	string='Ancho de Bastidor',
     	digits=(12, 4)
    )
	specs_porfbast = fields.Float(
    	string='Profundidad de Bastidor',
     	digits=(12, 4)
    )
	specs_antleaft = fields.Float(
    	string='Ancho de la Hoja',
     	digits=(12, 4)
    )
	specs_altleaft = fields.Float(
    	string='Altura de la Hoja',
     	digits=(12, 4)
    )
	specs_altboard = fields.Float(
    	string='Altura de Tablero',
     	digits=(12, 4)
    )
	specs_huacal = fields.Selection(
		[('yes', 'Yes'),
		('No', 'No')],
		string='Huacal',
	)
	specs_handing_id = fields.Many2one(
		'door.handing',
		string='Handing'
	)
	specs_operable = fields.Selection(
		[('yes', 'Yes'),
		('No', 'No')],
		string='Operable',
	)
	specs_type_arc_id = fields.Many2one(
		'door.type.arc',
		string='Tipo de Arco'
	)
	specs_altarc = fields.Float(
    	string='Altura de Arco',
     	digits=(12, 4)
    )
	specs_tolsup = fields.Float(
    	string='Tolerancia Superior (hoja y marco sup)',
     	digits=(12, 4) 
    )
	specs_tolcen = fields.Float(
    	string='Tolerancia Central (entre hoja y hoja)',
     	digits=(12, 4)
    )
	specs_tollat = fields.Float(
    	string='Tolerancia de los Lados (entre hoja y marco izq y der)',
     	digits=(12, 4)
    )
	specs_glass = fields.Selection(
		[('yes', 'Yes'),
		('No', 'No')],
		string='Vidrio Fijo',
	)
	specs_type_glass_id = fields.Many2one(
		'door.type.glass',
		string='Tipo de Vidrio'
	)
	specs_glassf = fields.Selection(
		[('yes', 'Yes'),
		('No', 'No')],
		string='Vidrio Fijo en Fijos',
	)
	specs_typef_glass_id = fields.Many2one(
		'door.type.glass',
		string='Tipo de Vidrio en Fijos'
	)
	specs_typet_glass_id = fields.Many2one(
		'door.type.glass',
		string='Tipo de Vidrio'
	)
	specs_ancmarc = fields.Float(
    	string='Ancho de Marco',
     	digits=(12, 4)
    )
	specs_profmarc = fields.Float(
    	string='Profundidad de Marco',
     	digits=(12, 4)
    )
	specs_amount_hinges = fields.Integer(
    	string='Cantidad de Bisagras'
    )
	specs_traslape_int_id = fields.Many2one(
		'door.traslape',
		string='Traslape Interna'
	)
	specs_traslape_ext_id = fields.Many2one(
		'door.traslape',
		string='Traslape Externa'
	)
	specs_pch_id = fields.Many2one(
		'door.metal',
		string='Preparación de Chapa'
	)
	specs_altce = fields.Float(
    	string='Altura de Cerradura',
     	digits=(12, 4)
    )
	specs_mbas = fields.Float(
    	string='Medidas Bastidor Superior',
     	digits=(12, 4)
    )
	specs_mbai = fields.Float(
    	string='Medidas Bastidor Interior',
     	digits=(12, 4)
    )
	specs_rlat = fields.Integer(
    	string='Roller Latches'
    )
	specs_bac = fields.Integer(
    	string='Ball Catch'
    )
	specs_tyarct_id = fields.Many2one(
		'door.type.arc',
		string='Tipo de Arco en Transom'
	)
	specs_altarct = fields.Float(
    	string='Altura del Arco de Transom',
     	digits=(12, 4)
    )
	specs_antra = fields.Float(
    	string='Ancho de Transom',
     	digits=(12, 4)
    )
	specs_altra = fields.Float(
    	string='Altura de Transom',
     	digits=(12, 4)
    )
	specs_ddm = fields.Selection(
		[('yes', 'Yes'),
		('no', 'No')],
		string='Doble Marco',
	)
	specs_ddmf = fields.Selection(
		[('yes', 'Yes'),
		('no', 'No')],
		string='Doble Marco de Fijos',
	)
	specs_altpc = fields.Float(
    	string='Altura Panel Central',
     	digits=(12, 4)
    )
	specs_anpc = fields.Float(
    	string='Ancho Panel Central',
     	digits=(12, 4)
    )
	specs_anfi = fields.Float(
    	string='Ancho de Fijos',
     	digits=(12, 4)
    )
	specs_alfi = fields.Float(
    	string='Altura de Fijos',
     	digits=(12, 4)
    )
	specs_board_type_id = fields.Many2one(
		'door.board.type',
		string='Tipo de Tablero de Fijos'
	)
	specs_altboard_type = fields.Float(
    	string='Altura de Tablero de Fijos',
     	digits=(12, 4)
    )
	specs_posfi_id = fields.Many2one(
		'door.position',
		string='Posición del Fijo'
	)
	specs_line_ids = fields.One2many(
		'door.accessories',
		'acc_id'
	)
	specs_tolerance = fields.Float(
    	string='Tolerancia Guardapolvo',
     	digits=(12, 4)
    )
	specs_assembly_id = fields.Many2one(
		'door.assembly',
		string='Preparación de Ensamble'
	)
	description = fields.Text(
		string='Comentarios'
	)
	specs_glass_line_ids = fields.One2many(
		'door.glass.specs',
		'glass_id'
	)
	specs_tramrec = fields.Float(
    	string='Tramo Recto (pulg lineales)',
     	digits=(12, 4)
    )
	specs_traminc = fields.Float(
    	string='Tramo Inclinado (pulg lineales)',
     	digits=(12, 4)
    )
	specs_tramcurniv = fields.Float(
    	string='Tramo Curvo a nivel (pulg lineales)',
     	digits=(12, 4)
    )
	specs_tramcurin = fields.Float(
    	string='Tramo Curvo inclinado (pulg lineales)',
     	digits=(12, 4)
    )
	specs_pasrec = fields.Float(
    	string='Pasamanos recto o inclinado (pulg lineales)',
     	digits=(12, 4)
    )
	specs_newdec = fields.Float(
    	string='Pasamanos curvos a nivel o curvo inclinado (pulg lineales)',
     	digits=(12, 4)
    )
	specs_cls = fields.Integer(
    	string='Cantidad Picaporte Superior'
    )
	specs_cli = fields.Integer(
    	string='Cantidad Picaporte Inferior'
    )
	name_specs = fields.Char(
		compute='name_create'
	)
	railing_id = fields.Many2one(
		'railing',
		string='Railing'
	)
	opportunity_specs = fields.Many2one(
		string='Lead/Oportunidad',
		related='specs_sale_id.opportunity_id'
	)
	
	campo_o2m_ids = fields.One2many(
        'mrp.bom',
        'specs_id', 
        string='specs'
    )
	mrp_count = fields.Integer(
		string='Total mrp',
		compute='_count_mrp'	
	)
 #####################################################
	specs_board_id = fields.Many2one(
		'product.attribute.value',
		string='Tablero'
	)
	specs_forging_id = fields.Many2one(
		'product.attribute.value',
		string='Forja',
	)
	specs_anchor_id = fields.Many2one(
		'product.attribute.value',
		string='Anclas',
	)
	specs_hinges_id = fields.Many2one(
		'product.attribute.value',
		string='Bisagras',
	)
	specs_jac_id = fields.Many2one(
		'product.attribute.value',
		string='Jaladera Activa Exterior',
	)
	specs_jacin_id = fields.Many2one(
		'product.attribute.value',
		string='Jaladera Activa Interior',
	)
	specs_jin_id = fields.Many2one(
		'product.attribute.value',
		string='Jaladera Inactiva Exterior',
	)
  
	specs_jinin_id = fields.Many2one(
		'product.attribute.value',
		string='Jaladera Inactiva Interior',
	)
	specs_moce_id = fields.Many2one(
		'product.attribute.value',
		string='Modelo de Cerradura',
	)
	specs_typeguar_id = fields.Many2one(
		'product.attribute.value',
		string='Tipo de Guardapolvo',
	)
 #####################################################
	specs_flashing_id = fields.Many2one(
		'product.attribute.value',
		string='Tipo de Flashing',
	)
	specs_latchsup_id = fields.Many2one(
		'product.attribute.value',
		string='Picaporte Superior',
	)
	specs_latchin_id = fields.Many2one(
		'product.attribute.value',
		string='Picaporte Inferior',
	)
	product_id = fields.Many2one(
		'product.product',
		string='producto'
	)
	specs_molding_int_id = fields.Many2one(
		'product.attribute.value',
		string='Moldura Interna'
	)
	specs_molding_ext_id = fields.Many2one(
		'product.attribute.value',
		string='Moldura Externa'
	)
	block_changes = fields.Boolean(
        string='Registro Bloqueado',    
    )
	specs_color_id = fields.Many2one(
		'product.attribute.value',
		string='Color'
	)
	specs_sp_line_ids = fields.One2many(
		'door.special.preparations',
		'prep_id'
	)
	specs_preparations_ids = fields.Many2many(
		comodel_name ='product.attribute.value',
		relation ='product_attribute_value1_rel',
        string='Preparaciones Especiales',
        column1 = 'id1',
        column2 = 'id2'
    )
	specs_glass_type_id = fields.Many2many(
		comodel_name ='product.attribute.value',
		relation = 'product_attribute_value2_rel',
        string='Tipo de Vidrio',
        column1 = 'id3',
        column2 = 'id4'
    )
 
	@api.onchange('specs_type')
	def _domain_specs_glass_ids(self):
		for rec in self:
			if rec.specs_type:
				door_obj =self.env['product.template'].search([('name','=','Vidrios')])
				ids_list = []
				for w in door_obj:
					ids_list.extend(w.attribute_line_ids.value_ids.ids)
				rec.specs_glass_type_id = [(6,0,ids_list)]
	
	@api.onchange('specs_type')
	def _domain_specs_preparation_ids(self):
		for rec in self:
			if rec.specs_type:
				door_obj =self.env['product.template'].search([('name','=','Preparaciones Especiales')])
				ids_list = []
				for w in door_obj:
					ids_list.extend(w.attribute_line_ids.value_ids.ids)
				rec.specs_preparations_ids = [(6,0,ids_list)]
	
	@api.onchange('specs_type')
	def _domain_specs_color_id(self):
		for rec in self:
			if rec.specs_type:
				door_obj =self.env['product.template'].search([('name','=','Pintura')])
				ids_list = []
				for w in door_obj:
					ids_list.extend(w.attribute_line_ids.value_ids.ids)
				res = {}
				res['domain'] = {'specs_color_id': [('id', 'in', ids_list)]}
				return res
			else:
				res = {}
				res['domain'] = {'specs_color_id': []}
 
	@api.onchange('specs_type')
	def _domain_product_id(self):
		for rec in self:
			if rec.specs_type:
				door_obj =self.env['product.product'].search([])
				ids_list = []
				for w in door_obj:
					if w.sale_ok == True:
						ids_list.append(w.id)
				res = {}
				res['domain'] = {'product_id': [('id', 'in', ids_list)]}
				return res
			else:
				res = {}
				res['domain'] = {'product_id': []}
    
    
	@api.onchange('specs_type')
	def _domain_specs_dc_id(self):
		for rec in self:
			if rec.specs_type:
				door_obj =self.env['door.configuration'].search([])
				ids_list = []
				for w in door_obj:
					if rec.specs_type == 'windows':
						if w.name == 'Fixed' or w.name == 'Casement' or w.name == 'Awning':
							ids_list.append(w.id)
					else:
						if w.name != 'Fixed' and w.name != 'Casement' and w.name != 'Awning':
							ids_list.append(w.id)
				res = {}
				res['domain'] = {'specs_dc_id': [('id', 'in', ids_list)]}
				return res
			else:
				res = {}
				res['domain'] = {'specs_dc_id': []}
 
	@api.onchange('specs_type')
	def _domain_specs_molding_ext_id(self):
		for rec in self:
			if rec.specs_type:
				door_obj =self.env['product.template'].search([('name','=','Molduras')])
				ids_list = []
				for w in door_obj:
					ids_list.extend(w.attribute_line_ids.value_ids.ids)
				res = {}
				res['domain'] = {'specs_molding_ext_id': [('id', 'in', ids_list)]}
				return res
			else:
				res = {}
				res['domain'] = {'specs_molding_ext_id': []}
	
	@api.onchange('specs_type')
	def _domain_specs_molding_int_id(self):
		for rec in self:
			if rec.specs_type:
				door_obj =self.env['product.template'].search([('name','=','Molduras')])
				ids_list = []
				for w in door_obj:
					ids_list.extend(w.attribute_line_ids.value_ids.ids)
				res = {}
				res['domain'] = {'specs_molding_int_id': [('id', 'in', ids_list)]}
				return res
			else:
				res = {}
				res['domain'] = {'specs_molding_int_id': []}
 
	
	def _change_state(self):
		for rec in self:
			if rec.stage_id == self.env.ref("cantera_sale_door.stage_in_progress"):
				rec.state = 'errase'
			if rec.stage_id == self.env.ref("cantera_sale_door.stage_planned"):
				rec.state = 'price'
			if rec.stage_id == self.env.ref("cantera_sale_door.stage_finish"):
				rec.state = 'bom'
			if rec.stage_id == self.env.ref("cantera_sale_door.stage_cancel"):
				rec.state = 'cancel'
			
 
	@api.onchange('specs_type')
	def _domain_specs_latchin_id(self):
		for rec in self:
			if rec.specs_type:
				door_obj =self.env['product.template'].search([('name','=','Picaporte')])
				ids_list = []
				for w in door_obj:
					ids_list.extend(w.attribute_line_ids.value_ids.ids)
				res = {}
				res['domain'] = {'specs_latchin_id': [('id', 'in', ids_list)]}
				return res
			else:
				res = {}
				res['domain'] = {'specs_latchin_id': []}
 
	@api.onchange('specs_type')
	def _domain_specs_latchsup_id(self):
		for rec in self:
			if rec.specs_type:
				door_obj =self.env['product.template'].search([('name','=','Picaporte')])
				ids_list = []
				for w in door_obj:
					ids_list.extend(w.attribute_line_ids.value_ids.ids)
				res = {}
				res['domain'] = {'specs_latchsup_id': [('id', 'in', ids_list)]}
				return res
			else:
				res = {}
				res['domain'] = {'specs_latchsup_id': []}
 
	@api.onchange('specs_type')
	def _domain_specs_flashing_id(self):
		for rec in self:
			if rec.specs_type:
				door_obj =self.env['product.template'].search([('name','=','Flashing')])
				ids_list = []
				for w in door_obj:
					ids_list.extend(w.attribute_line_ids.value_ids.ids)
				res = {}
				res['domain'] = {'specs_flashing_id': [('id', 'in', ids_list)]}
				return res
			else:
				res = {}
				res['domain'] = {'specs_flashing_id': []}
 
	@api.onchange('specs_type')
	def _domain_specs_typeguar_id(self):
		for rec in self:
			if rec.specs_type:
				door_obj =self.env['product.template'].search([('name','=','Guardapolvos')])
				ids_list = []
				for w in door_obj:
					ids_list.extend(w.attribute_line_ids.value_ids.ids)
				res = {}
				res['domain'] = {'specs_typeguar_id': [('id', 'in', ids_list)]}
				return res
			else:
				res = {}
				res['domain'] = {'specs_typeguar_id': []}
 
	@api.onchange('specs_type')
	def _domain_specs_moce_id(self):
		for rec in self:
			if rec.specs_type:
				door_obj =self.env['product.template'].search([('name','=','Cerradura')])
				ids_list = []
				for w in door_obj:
					ids_list.extend(w.attribute_line_ids.value_ids.ids)
				res = {}
				res['domain'] = {'specs_moce_id': [('id', 'in', ids_list)]}
				return res
			else:
				res = {}
				res['domain'] = {'specs_moce_id': []}
 
	@api.onchange('specs_type')
	def _domain_specs_jinin_id(self):
		for rec in self:
			if rec.specs_type:
				door_obj =self.env['product.template'].search([('name','=','Jaladeras')])
				ids_list = []
				for w in door_obj:
					ids_list.extend(w.attribute_line_ids.value_ids.ids)
				res = {}
				res['domain'] = {'specs_jinin_id': [('id', 'in', ids_list)]}
				return res
			else:
				res = {}
				res['domain'] = {'specs_jinin_id': []}
 
	@api.onchange('specs_type')
	def _domain_specs_jin_id(self):
		for rec in self:
			if rec.specs_type:
				door_obj =self.env['product.template'].search([('name','=','Jaladeras')])
				ids_list = []
				for w in door_obj:
					ids_list.extend(w.attribute_line_ids.value_ids.ids)
				res = {}
				res['domain'] = {'specs_jin_id': [('id', 'in', ids_list)]}
				return res
			else:
				res = {}
				res['domain'] = {'specs_jin_id': []}
 
	@api.onchange('specs_type')
	def _domain_specs_jacin_id(self):
		for rec in self:
			if rec.specs_type:
				door_obj =self.env['product.template'].search([('name','=','Jaladeras')])
				ids_list = []
				for w in door_obj:
					ids_list.extend(w.attribute_line_ids.value_ids.ids)
				res = {}
				res['domain'] = {'specs_jacin_id': [('id', 'in', ids_list)]}
				return res
			else:
				res = {}
				res['domain'] = {'specs_jacin_id': []}
    
	@api.onchange('specs_type')
	def _domain_specs_board_id(self):
		for rec in self:
			if rec.specs_type:
				door_obj =self.env['product.template'].search([('name','=','Tablero')])
				ids_list = []
				for w in door_obj:
					ids_list.extend(w.attribute_line_ids.value_ids.ids)
				res = {}
				res['domain'] = {'specs_board_id': [('id', 'in', ids_list)]}
				return res
			else:
				res = {}
				res['domain'] = {'specs_board_id': []}
	
	@api.onchange('specs_type')
	def _domain_specs_forgin_id(self):
		for rec in self:
			if rec.specs_type:
				door_obj =self.env['product.template'].search([('name','=','Forja')])
				ids_list = []
				for w in door_obj:
					ids_list.extend(w.attribute_line_ids.value_ids.ids)
				res = {}
				res['domain'] = {'specs_forging_id': [('id', 'in', ids_list)]}
				return res
			else:
				res = {}
				res['domain'] = {'specs_forging_id': []}
 
	@api.onchange('specs_type')
	def _domain_specs_anchor_id(self):
		for rec in self:
			if rec.specs_type:
				door_obj =self.env['product.template'].search([('name','=','Anclas')])
				ids_list = []
				for w in door_obj:
					ids_list.extend(w.attribute_line_ids.value_ids.ids)
				res = {}
				res['domain'] = {'specs_anchor_id': [('id', 'in', ids_list)]}
				return res
			else:
				res = {}
				res['domain'] = {'specs_anchor_id': []}
    
	@api.onchange('specs_type')
	def _domain_specs_hinges_id(self):
		for rec in self:
			if rec.specs_type:
				door_obj =self.env['product.template'].search([('name','=','Bisagra')])
				ids_list = []
				for w in door_obj:
					ids_list.extend(w.attribute_line_ids.value_ids.ids)
				res = {}
				res['domain'] = {'specs_hinges_id': [('id', 'in', ids_list)]}
				return res
			else:
				res = {}
				res['domain'] = {'specs_hinges_id': []}
 
	@api.onchange('specs_type')
	def _domain_specs_jac_id(self):
		for rec in self:
			if rec.specs_type:
				door_obj =self.env['product.template'].search([('name','=','Jaladeras')])
				ids_list = []
				for w in door_obj:
					ids_list.extend(w.attribute_line_ids.value_ids.ids)
				res = {}
				res['domain'] = {'specs_jac_id': [('id', 'in', ids_list)]}
				return res
			else:
				res = {}
				res['domain'] = {'specs_jac_id': []}

	@api.depends('campo_o2m_ids.specs_id')
	def _count_mrp(self):
		for record in self:
			score = self.env['mrp.bom'].search([
				('specs_id', '=', record.id)
			])
			record.mrp_count = len(score)

	def mrp_call_view(self):
		return {
			"name": 'Lista de Materiales',
			"view_mode": 'tree,form',
			"res_model": 'mrp.bom',
			"type": 'ir.actions.act_window',
			"target": 'current',
			"domain": [
				('specs_id', '=', self.id)
			],
			"context": {'default_specs_id': self.id}
		}
	
	@api.constrains(
		'specs_ant', 'specs_alt','specs_product_id','specs_dc_id','specs_molding_ext_id',
		'specs_molding_int_id','specs_flashing_id','specs_typeguar_id','specs_latchsup_id',
		'specs_latchin_id','specs_jac_id','specs_jacin_id','specs_jin_id','specs_jinin_id',
		'specs_cls','specs_cli','specs_tramrec','specs_traminc','specs_tramcurniv',
  		'specs_tramcurin','specs_pasrec','specs_newdec','specs_type_arc_id','specs_tyarct_id'

	)
	def square_feet(self):
		for rec in self:
			ant = rec.specs_ant * 0.0254
			alt = rec.specs_alt * 0.0254
			total = ant * alt
			configuration = 0.00
			flashing = 0.00
			smock = 0.00
			latch = 0.00
			handled = 0.00
			tramo_recto = 0.00
			tramo_inclinado = 0.00
			curvo_nivel = 0.00
			curvo_inclin = 0.00
			pass_rec_inc = 0.00
			pass_cur = 0.00
			price_family = 0.00
			# mol_in = 0.00
			# mol_ex = 0.00
			if rec.specs_type == 'door' or rec.specs_type == 'windows':
				rec.specs_mtrs = total
				price_family = rec.specs_product_id.price * total
				for flash in rec.specs_flashing_id.pav_attribute_line_ids.product_template_value_ids:
					if rec.specs_flashing_id.name == flash.name:
						if str(rec.specs_dc_id.name) == 'SD' or str(rec.specs_dc_id.name) == 'SDSL' or str(rec.specs_dc_id.name) == 'SDFS' or str(rec.specs_dc_id.name) == 'SDT' or str(rec.specs_dc_id.name) == 'SDTCP' or str(rec.specs_dc_id.name) == 'SDTCPSL' or str(rec.specs_dc_id.name) == 'SDTSL':
							flashing = flash.price_sd
						if str(rec.specs_dc_id.name) == 'DD' or str(rec.specs_dc_id.name) == 'DDSL' or str(rec.specs_dc_id.name) == 'DDFS' or str(rec.specs_dc_id.name) == 'DDT' or str(rec.specs_dc_id.name) == 'DDTCP' or str(rec.specs_dc_id.name) == 'DDTCPSL' or str(rec.specs_dc_id.name) == 'DDTSL':
							flashing = flash.price_dd
						if str(rec.specs_dc_id.name) == "Fixed" or str(rec.specs_dc_id.name) == "Casement" or str(rec.specs_dc_id.name) == "Awning":
							flashing = flash.price_unique
				for sm in rec.specs_typeguar_id.pav_attribute_line_ids.product_template_value_ids:
					if rec.specs_typeguar_id.name == sm.name:
						if str(rec.specs_dc_id.name) == 'SD' or str(rec.specs_dc_id.name) == 'SDSL' or str(rec.specs_dc_id.name) == 'SDFS' or str(rec.specs_dc_id.name) == 'SDT' or str(rec.specs_dc_id.name) == 'SDTCP' or str(rec.specs_dc_id.name) == 'SDTCPSL' or str(rec.specs_dc_id.name) == 'SDTSL':
							smock = sm.price_sd
						if str(rec.specs_dc_id.name) == 'DD' or str(rec.specs_dc_id.name) == 'DDSL' or str(rec.specs_dc_id.name) == 'DDFS' or str(rec.specs_dc_id.name) == 'DDT' or str(rec.specs_dc_id.name) == 'DDTCP' or str(rec.specs_dc_id.name) == 'DDTCPSL' or str(rec.specs_dc_id.name) == 'DDTSL':
							smock = sm.price_dd
						if str(rec.specs_dc_id.name) == "2R" or str(rec.specs_dc_id.name) == "2L" or str(rec.specs_dc_id.name) == "1L2R" or str(rec.specs_dc_id.name) == "1R2L" or str(rec.specs_dc_id.name) == "3R" or str(rec.specs_dc_id.name) == "3L" or str(rec.specs_dc_id.name) == "1L3R" or str(rec.specs_dc_id.name) == "1R3L" or str(rec.specs_dc_id.name) == "2R2L" or str(rec.specs_dc_id.name) == "1L4R" or str(rec.specs_dc_id.name) == "1R4L" or str(rec.specs_dc_id.name) == "4R" or str(rec.specs_dc_id.name) == "4L" or str(rec.specs_dc_id.name) == "2R3L" or str(rec.specs_dc_id.name) == "2L3R":
							smock = sm.price_bifolds
				var_in = []
				var_ex = []
				for mol_in in rec.specs_molding_int_id.pav_attribute_line_ids.product_template_value_ids:
					if rec.specs_molding_int_id.name == mol_in.name:
						var_in = mol_in
				for mol_ex in rec.specs_molding_ext_id.pav_attribute_line_ids.product_template_value_ids:
					if rec.specs_molding_ext_id.name == mol_ex.name:
						var_ex = mol_ex
				if str(rec.specs_dc_id.name) == 'SD' or str(rec.specs_dc_id.name) == 'SDSL' or str(rec.specs_dc_id.name) == 'DD' or str(rec.specs_dc_id.name) == 'DDSL':
					if str(rec.specs_type_arc_id.name)=='None' or str(rec.specs_type_arc_id.name)=='Simulated Eyebrow arch':
						if var_ex:
							configuration = var_ex.price_mol_cua
						if var_in:
							configuration = var_in.price_mol_cua
						if var_ex and var_in:
							configuration = var_in.price_mol_cua + var_ex.price_mol_cua
					if str(rec.specs_type_arc_id.name)=='Custom' or str(rec.specs_type_arc_id.name)=='Darla' or str(rec.specs_type_arc_id.name)=='Eliptical' or str(rec.specs_type_arc_id.name)=='Eyebrow' or str(rec.specs_type_arc_id.name)=='Full' or str(rec.specs_type_arc_id.name)=='Gothic' or str(rec.specs_type_arc_id.name)=='Provenzal':
						if var_ex:
							configuration = var_ex.price_mol_arq
						if var_in:
							configuration = var_in.price_mol_arq
						if var_ex and var_in:
							configuration = var_in.price_mol_arq + var_ex.price_mol_arq
				if str(rec.specs_dc_id.name) == 'SDFS' or str(rec.specs_dc_id.name) == 'SDT' or str(rec.specs_dc_id.name) == 'SDTCP' or str(rec.specs_dc_id.name) == 'SDTCPSL' or str(rec.specs_dc_id.name) == 'SDTSL' or str(rec.specs_dc_id.name) == 'DDFS' or str(rec.specs_dc_id.name) == 'DDT' or str(rec.specs_dc_id.name) == 'DDTCP' or str(rec.specs_dc_id.name) == 'DDTCPSL' or str(rec.specs_dc_id.name) == 'DDTSL' and rec.specs_molding_int_id or rec.specs_molding_ext_id:
					if str(rec.specs_tyarct_id.name)=='Custom' or str(rec.specs_tyarct_id.name)=='Darla' or str(rec.specs_tyarct_id.name)=='Eliptical' or str(rec.specs_tyarct_id.name)=='Eyebrow' or str(rec.specs_tyarct_id.name)=='Full' or str(rec.specs_tyarct_id.name)=='Gothic' or str(rec.specs_tyarct_id.name)=='Provenzal':
						if var_ex:
							configuration = var_ex.price_mol_arq
						if var_in:
							configuration = var_in.price_mol_arq
						if var_ex and var_in:
							configuration = var_in.price_mol_arq + var_ex.price_mol_arq
					if str(rec.specs_tyarct_id.name)=='None' or str(rec.specs_tyarct_id.name)=='Simulated Eyebrow arch':
						if var_ex:
							configuration = var_ex.price_mol_cua
						if var_in:
							configuration = var_in.price_mol_cua
						if var_ex and var_in:
							configuration = var_in.price_mol_cua + var_ex.price_mol_cua
				if str(rec.specs_dc_id.name) == 'Fixed' or str(rec.specs_dc_id.name) == 'Awning' or str(rec.specs_dc_id.name) == 'Casement':
					if str(rec.specs_type_arc_id.name)=='None' or str(rec.specs_type_arc_id.name)=='Simulated Eyebrow arch':
						if var_ex:
							configuration = var_ex.price_mol_cua
						if var_in:
							configuration = var_in.price_mol_cua
						if var_ex and var_in:
							configuration = var_in.price_mol_cua + var_ex.price_mol_cua
					if str(rec.specs_type_arc_id.name)=='Custom' or str(rec.specs_type_arc_id.name)=='Darla' or str(rec.specs_type_arc_id.name)=='Eliptical' or str(rec.specs_type_arc_id.name)=='Eyebrow' or str(rec.specs_type_arc_id.name)=='Full' or str(rec.specs_type_arc_id.name)=='Gothic' or str(rec.specs_type_arc_id.name)=='Provenzal':
						if var_ex:
							configuration = var_ex.price_mol_arq
						if var_in:
							configuration = var_in.price_mol_arq
						if var_ex and var_in:
							configuration = var_in.price_mol_arq + var_ex.price_mol_arq
			if rec.specs_type == 'railing':
				rec.specs_mtrs = total
				if rec.specs_tramrec:
					linea = self.env['railing'].search([('name', '=', 'Straight')])
					tramo_recto = rec.specs_tramrec * linea.price 
				if rec.specs_traminc:
					inclinado = self.env['railing'].search([('name', '=', 'Raked')])
					tramo_inclinado = rec.specs_traminc * inclinado.price 
				if rec.specs_tramcurniv:
					curv_niv = self.env['railing'].search([('name', '=', 'Curved')])
					curvo_nivel = rec.specs_tramcurniv * curv_niv.price 
				if rec.specs_tramcurin:
					curv_inc = self.env['railing'].search([('name', '=', 'Curved Raked')])
					curvo_inclin = rec.specs_tramcurin * curv_inc.price 
				if rec.specs_pasrec:
					pas_rec_inc = self.env['railing'].search([('name', '=', 'Handrail S o R')])
					pass_rec_inc = rec.specs_pasrec * pas_rec_inc.price
				if rec.specs_newdec:
					pas_cur = self.env['railing'].search([('name', '=', 'Handrail C o CR')])
					pass_cur = rec.specs_newdec * pas_cur.price 
			total_railing = tramo_recto + tramo_inclinado + curvo_nivel + curvo_inclin + pass_rec_inc + pass_cur
			latch_sup = 0.00
			for lt in rec.specs_latchsup_id.pav_attribute_line_ids.product_template_value_ids:
					if rec.specs_latchsup_id.name == lt.name:
						latch_sup = lt.price_unique
			latch_in = 0.00
			for lti in rec.specs_latchin_id.pav_attribute_line_ids.product_template_value_ids:
					if rec.specs_latchin_id.name == lti.name:
						latch_in = lti.price_unique
			latch = (latch_sup * rec.specs_cls) + (latch_in * rec.specs_cli)
   
			jac_ex = 0.00
			for jac in rec.specs_jac_id.pav_attribute_line_ids.product_template_value_ids:
					if rec.specs_jac_id.name == jac.name:
						if rec.specs_jac_id:
							jac_ex = jac.price_unique
						else:
							jac_ex = 0.00
			jac_in = 0.00
			for jacin in rec.specs_jacin_id.pav_attribute_line_ids.product_template_value_ids:
					if rec.specs_jacin_id.name == jacin.name:
						if rec.specs_jacin_id:
							jac_in = jacin.price_unique
						else:
							jac_in = 0.00
			jin_ex = 0.00
			for jin in rec.specs_jin_id.pav_attribute_line_ids.product_template_value_ids:
					if rec.specs_jin_id.name == jin.name:
						if rec.specs_jin_id:
							jin_ex = jin.price_unique
						else:
							jin_ex = 0.00
			jin_in = 0.00
			for jinin in rec.specs_jinin_id.pav_attribute_line_ids.product_template_value_ids:
					if rec.specs_jinin_id.name == jinin.name:
						if rec.specs_jinin_id:
							jin_in = jinin.price_unique
						else:
							jin_in = 0.00
			handled = jac_ex + jac_in + jin_ex + jin_in
   
			family_conf = price_family + configuration + flashing + smock + latch + handled + total_railing
			rec.specs_amount_total = family_conf
      
	def name_create(self):
		for rec in self:
			rec.name_specs=''
			if rec.specs_type == 'door':
				value = 'Puerta'
			if rec.specs_type == 'windows':
				value = 'Ventana'
			if rec.specs_type == 'railing':
				value = 'Barandal'
			nombre =value+' '+str(rec.specs_dc_id.name)+' '+str(rec.specs_product_id.name)
			if rec.specs_type:
				rec.name_specs=nombre
    
	def save_total_specs(self):
		self.ensure_one()
		for rec in self:
			unit = self.env['uom.uom'].search([('name', '=', 'Unidades')])
			_logger.info(unit,'################################################################################333')
			template = self.env['product.template'].search([('name', '=', rec.product_id.name)])
			for t in template:
				product_template = t.id
			caso = {
					'order_id': rec.specs_sale_id.id,
					'product_id': rec.product_id.id,
					'product_template_id': product_template,
					'price_unit': rec.specs_amount_total,
					'name': rec.name_specs,
					'product_uom': unit.id,
					'customer_lead': 1.00,
					'product_uom_qty': 1.00,
				}
			self.env['sale.order.line'].create(caso)
			rec.stage_id = self.env.ref("cantera_sale_door.stage_planned", raise_if_not_found=False)
   
   
	def materials_bills_create(self, campo):
		for product in campo.pav_attribute_line_ids.product_template_value_ids.ptav_product_variant_ids.product_template_variant_value_ids:
			if campo.name == product.name:
				for prod_bo in self.env['product.product'].search([]):
					if product.name == prod_bo.product_template_variant_value_ids.ptav_product_variant_ids.product_template_variant_value_ids.name:
						return prod_bo.id
			
           
	def create_materials_bills(self):
		materials = []
		for rec in self:
			unit = self.env['uom.uom'].search([('name', '=', 'Unidades')])
			lista = [
				rec.specs_color_id,
				rec.specs_board_id,
				rec.specs_forging_id,
				rec.specs_anchor_id,
				rec.specs_hinges_id,
				rec.specs_jac_id,
				rec.specs_jacin_id,
				rec.specs_jin_id,
				rec.specs_jinin_id,
				rec.specs_moce_id,
				rec.specs_typeguar_id,
				rec.specs_flashing_id,
				rec.specs_latchsup_id,
				rec.specs_latchin_id,
				rec.specs_molding_int_id,
				rec.specs_molding_ext_id,
				rec.specs_sp_line_ids.preparations_ids,
				rec.specs_glass_line_ids.glass_type_id,
			]
			for product in lista:
				if product:
					materials.append(rec.materials_bills_create(product))
			for l in self.env['sale.order.line'].search([('order_id', '=', rec.specs_sale_id.id)]):
				_logger.info(l.name,'################################################################################333')
				bills = self.env['mrp.bom'].create(
					{
					'product_tmpl_id': l.product_template_id.id,
					'product_id': l.product_id.id,
					'product_uom_id': unit.id,
					'product_qty': 1.00,
					'specs_id':rec.id
					}
				)
				for m in materials:
					self.env['mrp.bom.line'].create(
						{
							'bom_id': bills.id,
							'product_id': m,
							'product_uom_id': unit.id,
							'product_qty': 1.00,
						}
					)
			rec.stage_id = self.env.ref("cantera_sale_door.stage_finish", raise_if_not_found=False)
    
	@api.model
	def _read_group_stage_ids(self, stages, domain, order):
		return self.env['specs.type'].search([])

	def _select_state(self):
		state = self.env.ref("cantera_sale_door.stage_in_progress", raise_if_not_found=False)
		return state if state and state.id else False     


	def state_cancel(self):
		for rec in self:
			# for x in rec.specs_sale_id.order_line:
			# 	x.unlink()
			# for l in self.env['mrp.bom'].search([('specs_id','=', rec.id)]):
			# 	l.unlink()
			rec.stage_id = self.env.ref("cantera_sale_door.stage_cancel", raise_if_not_found=False)
			rec.block_changes = True
			
   
	def state_return(self):
		for rec in self:
			rec.stage_id = self.env.ref("cantera_sale_door.stage_in_progress", raise_if_not_found=False)
			rec.block_changes = False