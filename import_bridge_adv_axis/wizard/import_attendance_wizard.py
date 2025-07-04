# -*- coding: utf-8 -*-
#################################################################################
# Author      : AxisTechnolabs.com
# Copyright(c): 2011-Axistechnolabs.com.
# All Rights Reserved.
#
# This program is copyright property of the author mentioned above.
# You can`t redistribute it and/or modify it.
#
#################################################################################
from odoo import models, fields, _
from odoo.exceptions import Warning
import logging
import tempfile
import binascii
import datetime

_logger = logging.getLogger(__name__)
import io
import re

try:
    import csv
except ImportError:
    _logger.debug('Cannot `import csv`.')
try:
    import xlrd
except ImportError:
    _logger.debug('Cannot `import xlrd`.')
try:
    import base64
except ImportError:
    _logger.debug('Cannot `import base64`.')


class ImportHrAttendance(models.TransientModel):
    _name = "import.hr.attendance"
    _description = 'import hr attendance'

    import_file = fields.Binary(string="Add File")
    file_option = fields.Selection([('csv', 'CSV File'), ('xls', 'XLS File')], string='Select File', default='csv')

    def import_hr_attendance(self):       

        if self.file_option == 'csv':
            
            csv_data = base64.b64decode(self.import_file)
            data_file = io.StringIO(csv_data.decode("utf-8"))
            data_file.seek(0)
            csv_reader = csv.DictReader(data_file, delimiter=',')

            for line in csv_reader:

                if line.get('Employee Name'):
                    hr_employee = self.env['hr.employee'].search([('name', '=', line.get('Employee Name'))])
                    if not hr_employee:
                        hr_employee = hr_employee.create({
                            'name': line.get('Partner'),
                        })

                hour_diff = "05:30:00"
                hour_diff = datetime.datetime.strptime(hour_diff, "%H:%M:%S")
            
                if line.get('Sign In'):
                    split_in = str(line['Sign In']).split()
                    split_in2 = datetime.datetime.strptime(split_in[1], "%H:%M:%S")
                    split_in3 = split_in2 - hour_diff
                    split_in4 = split_in[0] + " " + str(split_in3)
                    sign_in = datetime.datetime.strptime(split_in4, "%d/%m/%Y %H:%M:%S")
                else:
                    sign_in = ""

                if line.get('Sign Out'):
                    split_in = str(line['Sign Out']).split()
                    split_in2 = datetime.datetime.strptime(split_in[1], "%H:%M:%S")
                    split_in3 = split_in2 - hour_diff
                    split_in4 = split_in[0] + " " + str(split_in3)
                    sign_out = datetime.datetime.strptime(split_in4, "%d/%m/%Y %H:%M:%S")
                else:
                    sign_out = ""                

                hr_attendance = self.env['hr.attendance'].create({
                    'employee_id': hr_employee.id,
                    'check_in': sign_in,
                    'check_out': sign_out,
                    'partner_name': line.get('Partner Name'),
                    'extra_color': line.get('Extra Color'),
                })

                print("hr_attendance::::::::::::::::::",hr_attendance)
                

        elif self.file_option == 'xls':
            fp = tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx")
            fp.write(binascii.a2b_base64(self.import_file))
            fp.seek(0)
            workbook = xlrd.open_workbook(fp.name)
            sheet = workbook.sheet_by_index(0)
            keys = sheet.row_values(0)
            xls_reader = [sheet.row_values(i) for i in range(1, sheet.nrows)]

            for row in xls_reader:
                line = dict(zip(keys, row))
                
                if line.get('Employee Name'):
                    hr_employee = self.env['hr.employee'].search([('name', '=', line.get('Employee Name'))])
                    if not hr_employee:
                        hr_employee = hr_employee.create({
                            'name': line.get('Partner'),
                        })

                hour_diff = "05:30:00"
                hour_diff = datetime.datetime.strptime(hour_diff, "%H:%M:%S")
            
                if line.get('Sign In'):
                    split_in = str(line['Sign In']).split()
                    split_in2 = datetime.datetime.strptime(split_in[1], "%H:%M:%S")
                    split_in3 = split_in2 - hour_diff
                    split_in4 = split_in[0] + " " + str(split_in3)
                    sign_in = datetime.datetime.strptime(split_in4, "%d/%m/%Y %H:%M:%S")
                else:
                    sign_in = ""

                if line.get('Sign Out'):
                    split_in = str(line['Sign Out']).split()
                    split_in2 = datetime.datetime.strptime(split_in[1], "%H:%M:%S")
                    split_in3 = split_in2 - hour_diff
                    split_in4 = split_in[0] + " " + str(split_in3)
                    sign_out = datetime.datetime.strptime(split_in4, "%d/%m/%Y %H:%M:%S")
                else:
                    sign_out = ""

                hr_attendance = self.env['hr.attendance'].create({
                    'employee_id': hr_employee.id,
                    'check_in': sign_in,
                    'check_out': sign_out,
                    'partner_name': line.get('Partner Name'),
                    'extra_color': line.get('Extra Color'),
                })

                print("hr_attendance::::::::::::::::::",hr_attendance)

        else:
            raise Warning(_("Invalid file!"))


     