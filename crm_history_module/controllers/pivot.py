# -*- coding: utf-8 -*-
from collections import deque
import io
import json
from odoo import http, _
from odoo.http import content_disposition, request
from odoo.tools import ustr, osutil, pycompat
import csv

class CsvTableExporter(http.Controller):

    @http.route('/web/pivot/export_csv', type='http', auth="user")
    def export_csv(self, data, **kw):
        jdata = json.loads(data)
        output = io.BytesIO()
        csv_writer = pycompat.csv_writer(output, quoting=1)
        writer = {}
        measure_count = jdata['measure_count']
        origin_count = jdata['origin_count']
        measure_headers = jdata['measure_headers']
        col_group_headers = jdata['col_group_headers']
        x, y, carry = 1, 0, deque()
        for i, header_row in enumerate(col_group_headers):
            if i > len(writer)-1:
                for k in range(i+1):
                    try:
                        if writer[k]:
                            pass
                    except Exception:
                        writer[k] = [[] for i in range(len(measure_headers)+1)]
            writer[i][0] = ''
            for header in header_row:
                while (carry and carry[0]['x'] == x):
                    cell = carry.popleft()
                    for j in range(measure_count * (2 * origin_count - 1)):
                        if y > len(writer)-1:
                            for k in range(y+1):
                                try:
                                    if writer[k]:
                                        pass
                                except Exception:
                                    writer[k] = [[]
                                                 for i in range(len(measure_headers)+1)]
                        writer[y][x+j] = ''
                    if cell['height'] > 1:
                        carry.append({'x': x, 'height': cell['height'] - 1})
                    x = x + measure_count * (2 * origin_count - 1)
                for j in range(header['width']):
                    if y > len(writer)-1:
                        for k in range(y+1):
                            try:
                                if writer[k]:
                                    pass
                            except Exception:
                                writer[k] = [[]
                                             for i in range(len(measure_headers)+1)]
                    writer[y][x + j] = header['title'] if j == 0 else ''
                if header['height'] > 1:
                    carry.append({'x': x, 'height': header['height'] - 1})
                x = x + header['width']
            while (carry and carry[0]['x'] == x):
                cell = carry.popleft()
                for j in range(measure_count * (2 * origin_count - 1)):
                    if y > len(writer)-1:
                        for k in range(y+1):
                            try:
                                if writer[k]:
                                    pass
                            except Exception:
                                writer[k] = [[]
                                             for i in range(len(measure_headers)+1)]
                    writer[y][x+j] = ''
                if cell['height'] > 1:
                    carry.append({'x': x, 'height': cell['height'] - 1})
                x = x + measure_count * (2 * origin_count - 1)
            x, y = 1, y + 1

        measure_headers = jdata['measure_headers']
        if measure_headers:
            if y > len(writer)-1:
                for k in range(y+1):
                    try:
                        if writer[k]:
                            pass
                    except Exception:
                        writer[k] = [[] for i in range(len(measure_headers)+1)]
            writer[y][0] = ''
            for measure in measure_headers:
                if y > len(writer)-1:
                    for k in range(y+1):
                        try:
                            if writer[k]:
                                pass
                        except Exception:
                            writer[k] = [[] for i in range(len(measure_headers)+1)]
                writer[y][x] = measure['title']
                for i in range(1, 2 * origin_count - 1):
                    if y > len(writer)-1:
                        for k in range(y+1):
                            try:
                                if writer[k]:
                                    pass
                            except Exception:
                                writer[k] = [[]
                                             for i in range(len(measure_headers)+1)]
                    writer[y][x+i] = ''
                x = x + (2 * origin_count - 1)
            x, y = 1, y + 1

        origin_headers = jdata['origin_headers']

        if origin_headers:
            if y > len(writer)-1:
                for k in range(y+1):
                    try:
                        if writer[k]:
                            pass
                    except Exception:
                        writer[k] = [[] for i in range(len(measure_headers)+1)]
            writer[y][0] = ''
            for origin in origin_headers:
                style = header_bold if origin['is_bold'] else header_plain
                if y > len(writer)-1:
                    for k in range(y+1):
                        try:
                            if writer[k]:
                                pass
                        except Exception:
                            writer[k] = [[] for i in range(len(measure_headers)+1)]
                writer[y][x] = origin['title']
                x = x + 1
            y = y + 1

        x = 0
        for row in jdata['rows']:
            if y > len(writer)-1:
                for k in range(y+1):
                    try:
                        if writer[k]:
                            pass
                    except Exception:
                        writer[k] = [[] for i in range(len(measure_headers)+1)]
            writer[y][x] = row['indent'] * '     ' + ustr(row['title'])
            for cell in row['values']:
                x = x + 1
                if cell.get('is_bold', False):
                    if y > len(writer)-1:
                        for k in range(y+1):
                            try:
                                if writer[k]:
                                    pass
                            except Exception:
                                writer[k] = [[]
                                             for i in range(len(measure_headers)+1)]
                    writer[y][x] = cell['value']
                else:
                    if y > len(writer)-1:
                        for k in range(y+1):
                            try:
                                if writer[k]:
                                    pass
                            except Exception:
                                writer[k] = [[]
                                             for i in range(len(measure_headers)+1)]
                    writer[y][x] = cell['value']
            x, y = 0, y + 1

        for i in writer.keys():
            csv_writer.writerow(writer[i])

        data = output.getvalue()
        filename = osutil.clean_filename(
            _("Pivot %(title)s (%(model_name)s)", title=jdata['title'], model_name=jdata['model']))
        response = request.make_response(data,
                                         headers=[('Content-Type', 'text/csv'),
                                                  ('Content-Disposition', content_disposition(filename + '.csv'))],
                                         )

        return response
