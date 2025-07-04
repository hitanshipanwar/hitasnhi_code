# -*- coding: utf-8 -*-
##############################################################################
#                                                                            #
# Part of WMSSOFT. (Website: www.wmssoft.com.au).                            #
# See LICENSE file for full copyright and licensing details.                 #
#                                                                            #
##############################################################################

import base64
import csv
import io
from odoo.addons.crm.report.crm_activity_report import ActivityReport
from odoo import models, fields, tools

class OutboundWizard(models.TransientModel):
    """Activity Statement wizard."""

    _name = "out.bound.wizard"
    _description = "Out Bound Wizard"

    date_start = fields.Date(string='Start Date')
    date_end = fields.Date(string='End Date')
    customer_id = fields.Many2many('res.partner', string='Customer')
    activity_type = fields.Many2many(
        'mail.activity.type', string='Activity Type')
    generated_csv_file = fields.Binary(
        "Generated file",
        help="Technical field used to temporarily hold the generated CSV file before it's downloaded."
    )

    def button_export_pdf(self):
        self.ensure_one()
        customer = self.customer_id.mapped('id')
        lables = self.activity_type.mapped('name')
        lables.append("Total")
        lables.insert(0, "User")
        activity_type = self.activity_type.mapped('id')
        
        domain=[]
        if self.date_start:
            domain.append(('date', '>=', self.date_start))

        if self.date_end:
            domain.append(('date', '<=', self.date_end))
            
        if customer:
            domain.append(('author_id', 'in', customer))
        
        if activity_type:
            domain.append(('mail_activity_type_id', 'in', activity_type))
        else:
            activity_type = self.env['mail.activity.type'].search([])
            lables = ["User"]+activity_type.mapped('name')+["Total"]
            activity_type = activity_type.ids
            domain.append(('mail_activity_type_id', 'in', activity_type))
        
        activity = self.env['mail.message'].search(domain)
        all_lst = []
        if activity:
            customers = {}
            total_row = ["Total"]
            for active in activity:
                column = 0
                if customers.get(active.author_id.id):
                    data = customers.get(active.author_id.id)
                    for ac in activity_type:
                        if ac == active.mail_activity_type_id.id:
                            data[ac] = data[ac] + 1
                            column += data[ac]
                        else:
                            column += data[ac]
                else:
                    customers[active.author_id.id] = {}
                    customers[active.author_id.id]['user'] = active.author_id.name
                    for ac in activity_type:
                        if ac == active.mail_activity_type_id.id:
                            customers[active.author_id.id][ac] = 1
                            column += customers[active.author_id.id][ac]
                        else:
                            customers[active.author_id.id][ac] = 0
                customers[active.author_id.id]['col'] = column

            for cm in customers:
                all_lst.append(list(customers[cm].values()))

            def get_sum(arr, indx, ax=0):
                if ax == 0:
                    return sum(arr[indx])
                return sum(a[indx] for a in arr)
            if all_lst:
                index = 0
                for total in all_lst[0]:
                    if index != 0:
                        total_row.append(get_sum(all_lst, index, 1))
                    index += 1
                all_lst.append(total_row)
                all_lst.insert(0, lables)
        data_print = {}
        data_print['data'] = all_lst
        data_print['start'] = self.date_start
        data_print['end'] = self.date_end
        return self.env.ref('crm_history_module.crm_activity_details_report').report_action([], data=data_print)

    def button_export_csv(self):
        self.ensure_one()
        header = [
            "",
            "Filter:",
            self.date_start or 'All', self.date_end or 'All'
        ]

        customer = self.customer_id.mapped('id')
        lables = self.activity_type.mapped('name')
        lables.append("Total")
        lables.insert(0, "User")
        empty_row = list(map(lambda x: "", lables))
        activity_type = self.activity_type.mapped('id')
        
        domain=[]
        if self.date_start:
            domain.append(('date', '>=', self.date_start))

        if self.date_end:
            domain.append(('date', '<=', self.date_end))
            
        if customer:
            domain.append(('author_id.id', 'in', customer))
        
        if activity_type:
            domain.append(('mail_activity_type_id.id', 'in', activity_type))
        else:
            activity_type = self.env['mail.activity.type'].search([])
            lables = ["User"]+activity_type.mapped('name')+["Total"]
            activity_type = activity_type.ids
            domain.append(('mail_activity_type_id', 'in', activity_type))
        
        activity = self.env['mail.message'].search(domain)

        all_lst = []
        if activity:
            customers = {}
            total_row = ["Total"]
            for active in activity:
                column = 0
                if customers.get(active.author_id.id):
                    data = customers.get(active.author_id.id)
                    for ac in activity_type:
                        if ac == active.mail_activity_type_id.id:
                            data[ac] = data[ac] + 1
                            column += data[ac]
                        else:
                            column += data[ac]
                else:
                    customers[active.author_id.id] = {}
                    customers[active.author_id.id]['user'] = active.author_id.name
                    for ac in activity_type:
                        if ac == active.mail_activity_type_id.id:
                            customers[active.author_id.id][ac] = 1
                            column += customers[active.author_id.id][ac]
                        else:
                            customers[active.author_id.id][ac] = 0
                customers[active.author_id.id]['col'] = column
            for cm in customers:
                all_lst.append(list(customers[cm].values()))

            def get_sum(arr, indx, ax=0):
                if ax == 0:
                    return sum(arr[indx])
                return sum(a[indx] for a in arr)
            if all_lst:
                index = 0
                for total in all_lst[0]:
                    if index != 0:
                        total_row.append(get_sum(all_lst, index, 1))
                    index += 1
                all_lst.append(total_row)
        output = io.StringIO()
        writer = csv.writer(output)
        if len(all_lst):
            writer.writerow(header)
            writer.writerow(empty_row)
            writer.writerow(lables)
            for wr in all_lst:
                writer.writerow(wr)
        else:
            writer.writerow(["Data not found."])
        self.generated_csv_file = base64.b64encode(output.getvalue().encode())
        us_format = "%m_%d_%Y"
        return {
            "type": "ir.actions.act_url",
            "target": "self",
            "url": "/web/content?model=out.bound.wizard&download=true&field=generated_csv_file&filename=1099 report {} - {}.csv&id={}".format(
                (self.date_start.strftime(
                    us_format) if self.date_start else ''), (self.date_end.strftime(us_format) if self.date_end else ''), self.id
            ),
        }