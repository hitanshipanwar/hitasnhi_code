from odoo import fields, models, api, _
from html import escape
from odoo.exceptions import AccessError, UserError, ValidationError


class StockPicking(models.Model):
	_inherit = 'stock.picking'

	purolator_shipment_pin = fields.Char(string="Purolator Shipment PIN",copy=False)