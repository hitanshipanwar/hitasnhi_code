from datetime import datetime, time
from pytz import timezone
from odoo import models, fields, api


class HrTimesheetReminder(models.Model):
    _inherit = 'account.analytic.line'

    @api.model
    def send_timesheets(self):
        employees_without_update = self.env['account.analytic.line'].search([('date', '=', fields.Date.today())])
        print('33333333333333', employees_without_update)
        employee_ids = employees_without_update.mapped('employee_id.id')
        print('111111111111111', employee_ids)
        employees = self.env['res.partner'].sudo().browse(employee_ids)
        print('222222222222', employees)
        employee_names = employees.mapped('name')
        employee_emails = employees.mapped('email')
        for name, email in zip(employee_names, employee_emails):
            print('Employee:', name)
            print('Email:', email)
            template = self.env.ref('ld_employee_timesheet_remainder.update_email_template')
            template.send_mail(self.id, force_send=True)
            print('ssssssssssssssennnnnnnnnnnndddddddddd', employee_emails)


from odoo import models, fields, api
from datetime import datetime, date,timedelta


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    send_timesheet_date = fields.Date(string="Send Timesheet Date")

    # CRON FUNCTION THAT CHECK EMAPLOYEES TIMESHEET
    @api.model
    def check_employee_timesheet(self):
        # print('>>>>>>>>>>>>>>>>>>>>>>>>>>')
        # Check Weekend (MONDAY=0, SATUDAY=5, SUNDAY=6)
        day_no = datetime.today().weekday()
        # print(">>>>>>>>>>>>>>day_no>>>>>>/>>>>>>>>>>>>>>>", day_no)
        current_date = datetime.now().date()
        # print('================current_date==================', current_date)
        start_date = datetime(current_date.year, current_date.month, 1).date()
        # print('=============start_date=======================', start_date)
        day_count = (current_date - start_date).days + 1
        # print('================day_count==================', day_count)
        if day_no < 5 or True:
            employees = self.search([])
            # print("========================employees==", employees)
            for employee in employees:
                # print("-------------------employee-------------", employee)
                total_effort = 0
                check_timesheet = True
                # if employee.send_timesheet_date and employee.send_timesheet_date == date.today():
                #     check_timesheet = False
                # if employee.user_id and employee.work_email and check_timesheet:
                if employee.user_id and employee.work_email:
                    # Check Employee Timesheet
                    emp_timesheet = self.env['account.analytic.line'].sudo().search([('employee_id','=',employee.id),('date','=',date.today())])
                    print(">>>>>>>>>>>>>>>>>>>>>>>>>>>", emp_timesheet)
                    if emp_timesheet:
                        total_effort = sum(emp_timesheet.mapped('unit_amount'))
                    if total_effort < 8:
                        print("=========================", employee.id)
                        ctx = {}
                        db = self.env.cr.dbname
                        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
                        action_id = self.env.ref('hr_timesheet.act_hr_timesheet_line').id
                        menu_id = self.env.ref('hr_timesheet.timesheet_menu_root').id
                        ctx['action_url'] = "{}/web?db={}#action={}&model=account.analytic.line&view_type=list&menu_id={}".format(
                            base_url, db, action_id, menu_id)
                        ctx['total_effort'] = total_effort
                        ctx['missing_effort'] = 8 - total_effort

                        # Data Preparation
                        missing_datas = []
                        for single_date in [d for d in (start_date + timedelta(n) for n in range(day_count)) if
                                            d <= current_date]:
                            print("========================", employee)
                            print("===========single_date============", single_date)
                            if single_date.weekday() < 5:
                                # lv_record = []
                                # emp_leave = self.env['hr.leave'].sudo().search([('employee_id', '=', employee.id)])
                                # print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>0", emp_leave)
                                # if emp_leave:
                                #   lv_start_date = emp_leave.request_date_from
                                #   lv_end_date = emp_leave.request_date_to
                                #   day_counts = (lv_end_date - lv_start_date).days + 1
                                #   for i in range(day_counts):
                                #       lv_record.append(lv_start_date + timedelta(i))
                                #   print(">>>>>>>>>>>>>>>>>>>>>>>lv_record.>>>>>>>>>>>>>>>>>>", lv_record)
                                # if not single_date in lv_record:
                                missing_total_effort = 0
                                missing_emp_timesheet = self.env['account.analytic.line'].sudo().search(
                                    [('employee_id', '=', employee.id), ('date', '=', single_date)])
                                if missing_emp_timesheet:
                                    missing_total_effort = sum(missing_emp_timesheet.mapped('unit_amount'))
                                if missing_total_effort < 8:
                                    missing_dic = {
                                        'date' : str(single_date) + ' / ' + str(single_date.strftime("%A")),
                                        'total_effort' : missing_total_effort,
                                        'missing_effort' : 8 - missing_total_effort,
                                    }
                                    missing_datas.append(missing_dic)
                        ctx['missing_datas'] = missing_datas
                        # Send Email Alert
                        mail_template = self.env.ref('ionicx_hrms_customization.update_email_template')
                        mail_template.with_context(ctx).sudo().send_mail(employee.id, force_send=True, email_values={
                            'email_to': employee.work_email})
                        employee.sudo().write({
                            'send_timesheet_date': date.today()
                            })

    # # CRON FUNCTION THAT CHECK EMAPLOYEES TIMESHEET
    # @api.model
    # def check_employee_leave(self):
    #   current_date = datetime.now().date()
    #   start_date = datetime(current_date.year, current_date.month, 1).date()
    #   # date_end = datetime(current_date.year, current_date.month, ).date
    #   end_date = datetime(current_date.year, current_date.month + 1, 1) + timedelta(days=-1)

    #   print("==================================", start_date)
    #   print("==================================", end_date)


# class HrEmployee(models.Model):
#   _inherit = 'hr.leave'

#   # CRON FUNCTION THAT CHECK EMAPLOYEES LEAVE RECORD
#   @api.model
#   def check_employee_leave(self):
#       print('>>>>>>>>>>>>>>>>>>>>>>>>>>')
#       # pass()






# Hitanshi's

from odoo import models, fields, api
from datetime import datetime, date


# class HrEmployee(models.Model):
#     _inherit = 'hr.employee'

#     send_timesheet_date = fields.Date(string="Send Timesheet Date")
#     work_hrs = fields.Float(string="Work Hours")

#     # CRON FUNCTION THAT CHECK EMAPLOYEES TIMESHEET
#     @api.model
#     def check_employee_timesheet(self):
#         print("===============================")
#         # Check Weekend (MONDAY=0, SATUDAY=5, SUNDAY=6)
#         day_no = datetime.today().weekday()
#         if day_no < 5:
#             employees = self.search([])
#             for employee in employees:
#                 check_timesheet = True
#                 if employee.send_timesheet_date and employee.send_timesheet_date == date.today():
#                     check_timesheet = False
#                 if employee.user_id and employee.work_email and check_timesheet:
#                     # Check Employee Timesheet
#                     emp_timesheet = self.env['account.analytic.line'].sudo().search([('employee_id','=',employee.id),('date','=',date.today())])
#                     total_hrs = 0.00
#                     if emp_timesheet:
#                         for timesheet_hrs_count in emp_timesheet:
#                             total_hrs += timesheet_hrs_count.unit_amount
#                     print("emp_timesheet========================", total_hrs)
#                     employee.sudo().write({
#                         'send_timesheet_date': date.today()
#                         })
#                     # if not emp_timesheet:
#                     if total_hrs < 8:
#                         if emp_timesheet:
#                             ctx = {}
#                             db = self.env.cr.dbname
#                             base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
#                             action_id = self.env.ref('hr_timesheet.act_hr_timesheet_line').id
#                             menu_id = self.env.ref('hr_timesheet.timesheet_menu_root').id
#                             ctx['action_url'] = "{}/web?db={}#action={}&model=account.analytic.line&view_type=list&menu_id={}".format(
#                                 base_url, db, action_id, menu_id)
#                             # Send Email Alert
#                             mail_template = self.env.ref('ionicx_hrms_customization.update_email_template')
#                             ss
#                             mail_template.with_context(ctx).sudo().send_mail(employee.id, force_send=True, email_values={
#                                 'email_to': employee.work_email})
#                             employee.sudo().write({
#                                 'send_timesheet_date': date.today()
#                                 })

