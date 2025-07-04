# -*- coding: utf-8 -*-

from odoo import models, fields, api


class StockPicking(models.Model):
	_inherit = 'stock.picking'

	def _send_confirmation_email(self):
		if not self.env.context.get('to_not_send_mail'):
			for stock_pick in self.filtered(lambda p: p.company_id.stock_move_email_validation and p.picking_type_id.code == 'outgoing'):
				delivery_template_id=self.env.ref('sss_picking_validate.mail_template_data_delivery_confirmation_sss_piking_order').id
				stock_pick.with_context(force_send=True).message_post_with_template(delivery_template_id, email_layout_xmlid='mail.mail_notification_light')