# # -*- coding: utf-8 -*-

from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError, ValidationError
import base64
import io
import re
import fitz  # PyMuPDF for PDF processing
from PIL import Image
import logging

_logger = logging.getLogger(__name__)


class ResUeser(models.Model):
    _inherit = 'sale.order'

# task HSO-1812 starts
    # def get_pdf_attachment_links_from_note(self):
    #     self.ensure_one()

    #     # 1. Extract all attachment IDs from the Terms & Conditions HTML field
    #     tc_attachment_ids = []
    #     if self.note:
    #         tc_attachment_ids = self._extract_attachment_ids(self.note)  # Extract referenced attachment IDs

    #     # 2. Get all attachments linked to this sale order
    #     all_attachments = self.env['ir.attachment'].search([
    #         ('res_model', '=', 'sale.order'),
    #         ('res_id', '=', self.id)
    #     ])

    #     # 3. Get attachments that are **both referenced in T&C and still linked**
    #     linked_tc_attachments = all_attachments.filtered(lambda att: att.id in tc_attachment_ids)
    #     links = []
    #     for attachment in linked_tc_attachments:
    #         url = '/web/content/{}/{}?download=true'.format(attachment.id, attachment.name)
    #         links.append('<a href="{}" target="_blank">{}</a>'.format(url, attachment.name))
    #     return '<br>'.join(links)

    # def _extract_attachment_ids(self, html_content):
    #     """Extract attachment IDs from the Terms and Conditions HTML field."""
    #     attachment_ids = []
    #     matches = re.findall(r'/web/content/(\d+)', html_content)
    #     if matches:
    #         attachment_ids = list(map(int, matches))
    #     return attachment_ids

# task HSO-1812 ends


 # task HSO-1847 starts
    def get_pdf_images_from_note(self):
        self.ensure_one()

        pdf_images = []
        if self.note:
            attachment_ids = self._extract_attachment_ids(self.note)

            attachments = self.env['ir.attachment'].browse(attachment_ids)
            for attachment in attachments:
                if attachment.mimetype == 'application/pdf':  # Ensure it's a PDF
                    pdf_images.extend(self._convert_pdf_to_images(attachment))
        # print("pdf_images ========== ",pdf_images)
        # okok
        return pdf_images  # List of Base64-encoded images

    def _extract_attachment_ids(self, html_content):
        matches = re.findall(r'/web/content/(\d+)', html_content)
        return list(map(int, matches)) if matches else []

    def _convert_pdf_to_images(self, attachment):
        """Convert a PDF attachment to a list of images (Base64-encoded)."""
        images = []
        pdf_content = io.BytesIO(base64.b64decode(attachment.datas))

        try:
            pdf_doc = fitz.open(stream=pdf_content, filetype="pdf")
            for page in pdf_doc:
                pix = page.get_pixmap()
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                
                img_byte_arr = io.BytesIO()
                img.save(img_byte_arr, format="PNG")
                img_base64 = base64.b64encode(img_byte_arr.getvalue()).decode("utf-8")

                images.append(img_base64)
        except Exception as e:
            return []

        return images

    def get_first_pdf_attachment_id(self):
        """Returns the first PDF attachment linked to the sale order"""
        self.ensure_one()
        attachment = self.env['ir.attachment'].search([
            ('res_model', '=', 'sale.order'),
            ('res_id', '=', self.id),
            ('mimetype', '=', 'application/pdf')
        ], limit=1)
        return attachment.id if attachment else False
 # task HSO-1847 ends


# task HSO-1739 
class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'


    # def get_pdf_attachment_links_from_note(self):
    #     self.ensure_one()

    #     # 1. Extract all attachment IDs from the Terms & Conditions HTML field
    #     tc_attachment_ids = []
    #     if self.notes:
    #         tc_attachment_ids = self._extract_attachment_ids(self.notes)  # Extract referenced attachment IDs

    #     # 2. Get all attachments linked to this sale order
    #     all_attachments = self.env['ir.attachment'].search([
    #         ('res_model', '=', 'purchase.order'),
    #         ('res_id', '=', self.id)
    #     ])

    #     # 3. Get attachments that are **both referenced in T&C and still linked**
    #     linked_tc_attachments = all_attachments.filtered(lambda att: att.id in tc_attachment_ids)
    #     links = []
    #     for attachment in linked_tc_attachments:
    #         url = '/web/content/{}/{}?download=true'.format(attachment.id, attachment.name)
    #         links.append('<a href="{}" target="_blank">{}</a>'.format(url, attachment.name))
    #     return '<br>'.join(links)

    # def _extract_attachment_ids(self, html_content):
    #     """Extract attachment IDs from the Terms and Conditions HTML field."""
    #     attachment_ids = []
    #     matches = re.findall(r'/web/content/(\d+)', html_content)
    #     if matches:
    #         attachment_ids = list(map(int, matches))
    #     return attachment_ids

    def get_pdf_images_from_note(self):
        self.ensure_one()

        pdf_images = []
        if self.notes:
            attachment_ids = self._extract_attachment_ids(self.notes)
            _logger.info('attachment_ids: %s', attachment_ids)
            
            attachments = self.env['ir.attachment'].browse(attachment_ids).exists()
            _logger.info('attachments: %s', attachments)
            for attachment in attachments:
                if attachment.mimetype == 'application/pdf':  # Ensure it's a PDF
                    pdf_images.extend(self._convert_pdf_to_images(attachment))
        # print("pdf_images ========== ",pdf_images)
        # okok
        return pdf_images  # List of Base64-encoded images

    def _extract_attachment_ids(self, html_content):
        matches = re.findall(r'/web/content/(\d+)', html_content)
        return list(map(int, matches)) if matches else []

    def _convert_pdf_to_images(self, attachment):
        """Convert a PDF attachment to a list of images (Base64-encoded)."""
        images = []
        pdf_content = io.BytesIO(base64.b64decode(attachment.datas))

        try:
            pdf_doc = fitz.open(stream=pdf_content, filetype="pdf")
            for page in pdf_doc:
                pix = page.get_pixmap()
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                
                img_byte_arr = io.BytesIO()
                img.save(img_byte_arr, format="PNG")
                img_base64 = base64.b64encode(img_byte_arr.getvalue()).decode("utf-8")

                images.append(img_base64)
        except Exception as e:
            return []

        return images

    def get_first_pdf_attachment_id(self):
        """Returns the first PDF attachment linked to the sale order"""
        self.ensure_one()
        attachment = self.env['ir.attachment'].search([
            ('res_model', '=', 'purchase.order'),
            ('res_id', '=', self.id),
            ('mimetype', '=', 'application/pdf')
        ], limit=1)
        return attachment.id if attachment else False

# task HSO-1739