import json

from odoo.http import content_disposition, request, route
import werkzeug
from odoo.addons.web.controllers.report import ReportController
from odoo.tools.misc import xlsxwriter
from odoo.addons.web.controllers.pivot import TableExporter



class ReportController(ReportController):
    @route([
        '/report/<converter>/<reportname>',
        '/report/<converter>/<reportname>/<docids>',
    ], type='http', auth='user', website=True)
    def report_routes(self, reportname, docids=None, converter=None, **data):
        request.env.context.get('allowed_company_ids', [2])
        # report = request.env['ir.actions.report']._get_report_from_name(reportname)
        report = request.env['ir.actions.report']
        context = dict(request.env.context)
        d = json.dumps(data)
        if docids:
            docids = [int(i) for i in docids.split(',')]
        if data.get('options'):
            data.update(json.loads(data.pop('options')))
        if data.get('context'):
            data['context'] = json.loads(data['context'])
            context.update(data['context'])
        if converter == 'html':
            html = report.with_context(context)._render_qweb_html(docids, data=data)[0]
            return request.make_response(html)
        elif converter == 'pdf':
            context['allowed_company_ids']=request.env.user.company_ids.mapped('id')
            pdf = report.with_context(context)._render_qweb_pdf(reportname,docids, data=data)[0]
            pdfhttpheaders = [('Content-Type', 'application/pdf'), ('Content-Length', len(pdf))]
            return request.make_response(pdf, headers=pdfhttpheaders)
        elif converter == 'text':
            text = report.with_context(context)._render_qweb_text(docids, data=data)[0]
            texthttpheaders = [('Content-Type', 'text/plain'), ('Content-Length', len(text))]
            return request.make_response(text, headers=texthttpheaders)

        elif converter == "xlsx":
            xlsx = report.with_context(**context)._render_xlsx(
                reportname, docids, data=data
            )[0]
            xlsxhttpheaders = [
                (
                    "Content-Type",
                    "application/vnd.openxmlformats-"
                    "officedocument.spreadsheetml.sheet",
                ),
                ("Content-Length", len(xlsx)),
            ]
            return request.make_response(xlsx, headers=xlsxhttpheaders)

        else:
            raise werkzeug.exceptions.HTTPException(description='Converter %s not implemented.' % converter)
