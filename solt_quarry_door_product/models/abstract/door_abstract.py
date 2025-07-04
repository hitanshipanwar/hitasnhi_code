# -*- coding: utf-8 -*-

from odoo import fields, models


class DoorAbstract(models.AbstractModel):
    _name = 'door.abstract'
    _description = 'Door abstract'

    name = fields.Char('Name', required=True)
    price = fields.Float('Price', digits='Product Unit of Measure')
