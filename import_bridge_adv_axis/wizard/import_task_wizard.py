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


class ImportProjectTask(models.TransientModel):
    _name = "import.project.task"
    _description = 'import project task'

    import_file = fields.Binary(string="Add File")
    file_option = fields.Selection([('csv', 'CSV File'), ('xls', 'XLS File')], string='Select File', default='csv')

    def import_project_task(self):       

        if self.file_option == 'csv':
            
            csv_data = base64.b64decode(self.import_file)
            data_file = io.StringIO(csv_data.decode("utf-8"))
            data_file.seek(0)
            csv_reader = csv.DictReader(data_file, delimiter=',')

            for line in csv_reader:
                if line.get('Project Id'):
                    project_id = self.env['project.project'].search([('name', '=', line.get('Project Id'))])
                    if not project_id:
                        project_id = project_id.create({
                            'name': line.get('Project Id'),
                        })

                if line.get('User'):
                    user_id = self.env['res.users'].search([('name', '=', line.get('User'))])

                if line.get('Deadline Date'):
                    deadline_date = datetime.datetime.strptime(line['Deadline Date'], '%d/%m/%Y')
                else:
                    deadline_date = datetime.datetime.now()

                if line.get('Tag'):
                    tag_ids = self.env['project.tags'].search([('name', '=', line.get('Tag'))])

                if int(line.get('Bool')) == 1:
                    bool_field = 1
                else:
                    bool_field = 0

                project_task = self.env['project.task'].create({
                    'name': line.get('Task Name'),
                    'project_id': project_id.id,
                    'user_ids': [(6,0,[user_id.id])],
                    'date_deadline': deadline_date,
                    'tag_ids': tag_ids.ids,
                    'description': line.get('Description'),
                    'partner_name': line.get('Partner Name'),
                    'extra_color': line.get('Color'),
                    'extra_bool': bool_field,
                    'extra_amount': line.get('Amount'),
                    'extra_notes': line.get('Notes'),
                })

                print("project_task::::::::::::::::::",project_task)
                

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
                
                if line.get('Project Id'):
                    project_id = self.env['project.project'].search([('name', '=', line.get('Project Id'))])
                    if not project_id:
                        project_id = project_id.create({
                            'name': line.get('Project Id'),
                        })

                if line.get('User'):
                    user_id = self.env['res.users'].search([('name', '=', line.get('User'))])

                if line.get('Deadline Date'):
                    deadline_date = datetime.datetime.strptime(line['Deadline Date'], '%d/%m/%Y')
                else:
                    deadline_date = datetime.datetime.now()

                if line.get('Tag'):
                    tag_ids = self.env['project.tags'].search([('name', '=', line.get('Tag'))])

                if int(line.get('Bool')) == 1:
                    bool_field = 1
                else:
                    bool_field = 0

                project_task = self.env['project.task'].create({
                    'name': line.get('Task Name'),
                    'project_id': project_id.id,
                    'user_ids': [(6,0,[user_id.id])],
                    'date_deadline': deadline_date,
                    'tag_ids': tag_ids.ids,
                    'description': line.get('Description'),
                    'partner_name': line.get('Partner Name'),
                    'extra_color': line.get('Color'),
                    'extra_bool': bool_field,
                    'extra_amount': line.get('Amount'),
                    'extra_notes': line.get('Notes'),
                })

                print("project_task::::::::::::::::::",project_task)

        else:
            raise Warning(_("Invalid file!"))


     