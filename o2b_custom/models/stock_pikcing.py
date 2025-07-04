# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools, _
import base64
from odoo.exceptions import UserError, ValidationError

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def action_print_packing_slip_o2b(self):
        self.ensure_one()
        report_action = self.env.ref('o2b_custom.action_report_packing_slip_o2b')
        pdf, _ = report_action._render_qweb_pdf(self.ids)
        # Continue processing (e.g., attaching the PDF and posting to chatter)
        attachment = self.env['ir.attachment'].create({
            'name': 'Packing Slip - %s.pdf' % self.name,
            'type': 'binary',
            'datas': base64.b64encode(pdf),
            'res_model': self._name,
            'res_id': self.id,
        })
        self.message_post(
            body="Packing Slip printed.",
            attachment_ids=[attachment.id],
            subtype_id=self.env.ref('mail.mt_note').id,
        )
        return True

