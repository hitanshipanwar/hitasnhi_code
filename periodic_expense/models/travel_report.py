from odoo import models, fields, api
from odoo.exceptions import ValidationError

class TravelReport(models.Model):
    _name = 'periodic.travel.report'
    _description = 'Travel Report'
    # _rec_name = 'employee_id'

    @api.model
    def _get_employee_id(self):
        employee = self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)
        return employee.id if employee else False

    employee_id = fields.Many2one('hr.employee', string='Employee', required=True, readonly=True, default=lambda self: self._get_employee_id())
    start_date = fields.Date(string='Start Date', required=True)
    end_date = fields.Date(string='End Date', required=True)
    project = fields.Many2one('project.project', string='Project')
    location = fields.Char(string='Location')
    trip_purpose = fields.Char(string='Trip Purpose')
    activity_detail = fields.Char(string='Activity Detail')
    expense_line_ids = fields.One2many('periodic.expense.line', 'report_id', string='Expense Lines')


    def name_get(self):
        result = []
        for record in self:
            name = f"Travel Report of {record.employee_id.name}"
            result.append((record.id, name))
        return result



class ExpenseLine(models.Model):
    _name = 'periodic.expense.line'
    _description = 'Travel Expense Line'

    report_id = fields.Many2one('periodic.travel.report', string='Travel Report', required=True, ondelete='cascade')
    date = fields.Datetime(string='Expense Date & Time', required=True)
    description = fields.Char(string='Description', required=True)
    expense_type_id = fields.Many2one('periodic.travel.expense.type', string="Expense Type")
    attachment = fields.Binary(string='Attachment')
    attachment_filename = fields.Char(string='Filename')
    expense_amount = fields.Float(string='Expense Amount', required=True)
    expense_id = fields.Many2one('hr.expense', string='Linked Expense', readonly=True)


    @api.constrains('expense_amount')
    def _check_amount_positive(self):
        for record in self:
            if record.expense_amount <= 0:
                raise ValidationError("Expense Amount is mandatory.")


    @api.model
    def create(self, vals):
        record = super().create(vals)
        
        expense = self.env['hr.expense'].sudo().create({
            'name': vals.get('description'),
            'employee_id': record.report_id.employee_id.id,
            'date': vals.get('date'),
            'unit_amount': vals.get('expense_amount'),
        })

        if vals.get('attachment'):
            self.env['ir.attachment'].create({
                'name': vals.get('attachment_filename') or 'Expense Attachment',
                'type': 'binary',
                'datas': vals.get('attachment'),
                'res_model': 'hr.expense',
                'res_id': expense.id,
            })

        record.expense_id = expense.id
        return record


    @api.model
    def write(self, vals):
        record = super().write(vals)
        for line in self:
            update_vals = {}
            if 'description' in vals:
                update_vals['name'] = vals['description']

            if 'date' in vals:
                update_vals['date'] = vals['date']

            if 'expense_amount' in vals:
                update_vals['unit_amount'] = vals['expense_amount']

            if update_vals:
                line.expense_id.sudo().write(update_vals)

            if 'attachment' in vals:
                old_attachments = self.env['ir.attachment'].search([
                    ('res_model', '=', 'hr.expense'),
                    ('res_id', '=', line.expense_id.id)
                ])
                old_attachments.unlink()

                self.env['ir.attachment'].create({
                    'name': vals.get('attachment_filename') or 'Expense Attachment',
                    'type': 'binary',
                    'datas': vals.get('attachment'),
                    'res_model': 'hr.expense',
                    'res_id': line.expense_id.id,
                })

        return record



class TravelExpenseType(models.Model):
    _name = 'periodic.travel.expense.type'
    _description = 'Travel Expense Type'

    name = fields.Char(string="Expense Type", required=True)