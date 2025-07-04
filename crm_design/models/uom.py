# -*- coding: utf-8 -*-

from odoo import models,fields


class UoM(models.Model):
    _inherit = 'uom.uom'

    thai_uom_name = fields.Char(string="Thai Name")

    def name_get(self):
        res = super().name_get()

        record = False
        if self._context.get('params'):
            model = self._context.get('params').get('model')
            id = self._context.get('params').get('id')
            record = self.env[model].browse(id)

        uom_list = []
        for uom in self:
            name = ''
            # if record and record.is_thai or self._context.get('is_thai'):
            if self._context.get('is_thai'):
                if uom.thai_uom_name:
                    name += uom.thai_uom_name
                else:
                    name += uom.name
            else:
                name += uom.name
            uom_list.append((uom.id,name or ''))

        return uom_list
