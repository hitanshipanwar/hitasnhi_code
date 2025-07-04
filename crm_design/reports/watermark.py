from base64 import b64decode
from io import BytesIO
from logging import getLogger
from odoo import api, models

logger = getLogger(__name__)

try:
    from PyPDF2 import PdfFileReader, PdfFileWriter 
except ImportError:
    logger.debug("Can not import PyPDF2")

from odoo.modules.module import get_resource_path
from odoo import models





class Report(models.Model):
    _inherit = "ir.actions.report"

    @api.model
    def _run_wkhtmltopdf(
        self,
        bodies,
        report_ref=False,
        header=None,
        footer=None,
        landscape=False,
        specific_paperformat_args=None,
        set_viewport_size=False,
    ):
        result = super(Report, self)._run_wkhtmltopdf(
            bodies,
            report_ref=report_ref,
            header=header,
            footer=footer,
            landscape=landscape,
            specific_paperformat_args=specific_paperformat_args,
            set_viewport_size=set_viewport_size,
        )
        pdf = PdfFileWriter()
        pdf_watermark = PdfFileReader(open(get_resource_path('crm_design','static','watermark.pdf'), 'rb'))
        for page in PdfFileReader(BytesIO(result)).pages:
            watermark_page = pdf.addBlankPage(
                page.mediaBox.getWidth(), page.mediaBox.getHeight()
            )
            watermark_page.mergePage(pdf_watermark.getPage(0))
            watermark_page.mergePage(page)

        pdf_content = BytesIO()
        pdf.write(pdf_content)
        return pdf_content.getvalue()
