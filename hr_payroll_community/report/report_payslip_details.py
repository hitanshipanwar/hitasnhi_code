#-*- coding:utf-8 -*-

from odoo import api, models
from datetime import timedelta

class PayslipDetailsReport(models.AbstractModel):
    _name = 'report.hr_payroll_community.report_payslipdetails'
    _description = 'Payslip Details Report'

    def get_details_by_rule_category(self, payslip_lines):
        PayslipLine = self.env['hr.payslip.line']
        RuleCateg = self.env['hr.salary.rule.category']

        def get_recursive_parent(current_rule_category, rule_categories=None):
            if rule_categories:
                rule_categories = current_rule_category | rule_categories
            else:
                rule_categories = current_rule_category

            if current_rule_category.parent_id:
                return get_recursive_parent(current_rule_category.parent_id, rule_categories)
            else:
                return rule_categories

        res = {}
        result = {}

        if payslip_lines:
            self.env.cr.execute("""
                SELECT pl.id, pl.category_id, pl.slip_id FROM hr_payslip_line as pl
                LEFT JOIN hr_salary_rule_category AS rc on (pl.category_id = rc.id)
                WHERE pl.id in %s
                GROUP BY rc.parent_id, pl.sequence, pl.id, pl.category_id
                ORDER BY pl.sequence, rc.parent_id""",
                (tuple(payslip_lines.ids),))
            for x in self.env.cr.fetchall():
                result.setdefault(x[2], {})
                result[x[2]].setdefault(x[1], [])
                result[x[2]][x[1]].append(x[0])
            for payslip_id, lines_dict in result.items():
                res.setdefault(payslip_id, [])
                for rule_categ_id, line_ids in lines_dict.items():
                    rule_categories = RuleCateg.browse(rule_categ_id)
                    lines = PayslipLine.browse(line_ids)
                    level = 0
                    for parent in get_recursive_parent(rule_categories):
                        res[payslip_id].append({
                            'rule_category': parent.name,
                            'name': parent.name,
                            'code': parent.code,
                            'level': level,
                            'total': sum(lines.mapped('total')),
                        })
                        level += 1
                    for line in lines:
                        res[payslip_id].append({
                            'rule_category': line.name,
                            'name': line.name,
                            'code': line.code,
                            'total': line.total,
                            'level': level
                        })
        return res

    def get_lines_by_contribution_register(self, payslip_lines):
        result = {}
        res = {}
        for line in payslip_lines.filtered('register_id'):
            result.setdefault(line.slip_id.id, {})
            result[line.slip_id.id].setdefault(line.register_id, line)
            result[line.slip_id.id][line.register_id] |= line
        for payslip_id, lines_dict in result.items():
            res.setdefault(payslip_id, [])
            for register, lines in lines_dict.items():
                res[payslip_id].append({
                    'register_name': register.name,
                    'total': sum(lines.mapped('total')),
                })
                for line in lines:
                    res[payslip_id].append({
                        'name': line.name,
                        'code': line.code,
                        'quantity': line.quantity,
                        'amount': line.amount,
                        'total': line.total,
                    })
        return res

    @api.model
    def _get_report_values(self, docids, data=None):
        payslips = self.env['hr.payslip'].browse(docids)
        return {
            'doc_ids': docids,
            'doc_model': 'hr.payslip',
            'docs': payslips,
            'data': data,
            'get_details_by_rule_category': self.get_details_by_rule_category(payslips.mapped('details_by_salary_rule_category').filtered(lambda r: r.appears_on_payslip)),
            'get_lines_by_contribution_register': self.get_lines_by_contribution_register(payslips.mapped('line_ids').filtered(lambda r: r.appears_on_payslip)),
        }

class EmployeePayslipDetailsReport(models.AbstractModel):
    _name = 'report.hr_payroll_community.employee_report_payslipdetails'
    _description = 'Employee Payslip Details Report'
    

    @api.model
    def _get_report_values(self, docids, data=None):
        payslips = self.env['hr.payslip'].browse(docids)
        def get_amount_percentage_base(payslip,type):
            rule_id = self.env['hr.salary.rule'].search([('code','=',type),('from_date','<=',payslip.date_from),('end_date','>=',payslips.date_to)],limit=1)
            if payslip and rule_id:
                if rule_id.amount_type == 'percentage':
                    return payslip.contract_id.wage * rule_id.amount_percentage_payslip / 100
                else:
                    return rule_id.amount_fix_payslip
            else:
                return 0.0

        def get_leaves_deduct_amt(payslip):
            if payslip:
                work_day_count = 0 
                day_count = (payslip.date_to - payslip.date_from).days + 1
                for single_date in [d for d in (payslip.date_from + timedelta(n) for n in range(day_count)) if
                                                d <= payslip.date_to]:
                    if single_date.weekday() < 5:
                        work_day_count += 1
                
                first_contract_date = payslip.employee_id.first_contract_date
                if first_contract_date:
                    emp_timeoff = self.env['hr.leave'].search([('employee_id', '=', payslip.employee_id.id),('request_date_from','>=',first_contract_date),('request_date_to','<=',payslip.date_from),('is_payable','!=',True),('state', '=', 'validate')])
                    months = (payslip.date_to.year - first_contract_date.year) * 12 + payslip.date_to.month - first_contract_date.month
                    
                    monthly_leave = int(self.env['ir.config_parameter'].sudo().get_param('hr_payroll_community.monthly_leave')) or 0
                    total_leave = months*monthly_leave
                    due_previous_leave = total_leave - len(emp_timeoff)
                    current_leave = monthly_leave
                    current_leave_ids = self.env['hr.leave'].search([('employee_id', '=', payslip.employee_id.id),('request_date_from','>=',payslip.date_from),('request_date_to','<=',payslip.date_to),('is_payable','!=',True),('state', '=', 'validate')])
                    current_leave_ids = int(sum(current_leave_ids.mapped('number_of_days_display'))) or 0
                    
                    deductions_leave = 0
                    if due_previous_leave > 0:
                        current_leave+=due_previous_leave

                    if current_leave_ids > current_leave:
                        deductions_leave = current_leave_ids - current_leave
                    total_work_days = work_day_count
                    one_day_salary = payslip.contract_id.wage / work_day_count
                    leaves_deduct_amt = one_day_salary * deductions_leave
                    work_day_count = work_day_count - deductions_leave
                    return leaves_deduct_amt,work_day_count,total_work_days
                else:
                    return 0.0
        return {
            'doc_ids': docids,
            'doc_model': 'hr.payslip',
            'docs': payslips,
            'data': data,
            'get_amount_percentage_base':get_amount_percentage_base,
            'get_leaves_deduct_amt':get_leaves_deduct_amt,
        }