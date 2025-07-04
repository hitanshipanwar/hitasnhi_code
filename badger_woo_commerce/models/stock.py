# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, _, api


class StockMove(models.Model):
    _inherit = 'stock.move'
    
    employee_name = fields.Char('Employee Name')
    
    def _prepare_procurement_values(self):
        result = super(StockMove, self)._prepare_procurement_values()
        result.update({'employee_name': self.employee_name})
        return result


class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    employee_name = fields.Char('Employee Name', related='move_id.employee_name')


class StockRule(models.Model):
    _inherit = 'stock.rule'

    def _get_custom_move_fields(self):
        fields = super(StockRule, self)._get_custom_move_fields()
        fields += ['employee_name']
        return fields
    
    def _push_prepare_move_copy_values(self, move_to_copy, new_date):
        res = super(StockRule, self)._push_prepare_move_copy_values(move_to_copy, new_date)
        res['employee_name'] = move_to_copy.employee_name
        return res