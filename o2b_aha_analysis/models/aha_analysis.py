from odoo import models, fields, api, _, tools
import logging

_logger = logging.getLogger(__name__)

class AHAAnalysis(models.Model):
	_name = "aha.analysis"
	_description = "AHA Analysis"
	_auto = False
	_rec_name = "pcp_name"

	pcp_name = fields.Char(string="PCP Name", readonly=True)
	aha_completed_id = fields.Many2one('aha.completed.type', string="AHA Completed", readonly=True)
	ticket_count = fields.Integer(string="Ticket Count", readonly=True)
	ticket_id = fields.Many2one('helpdesk.ticket', string="Tickets", readonly=True)
	company_id = fields.Many2one('res.company', string="Company", readonly=True)
	date_from = fields.Date(string="Date From", readonly=True)
	date_to = fields.Date(string="Date To", readonly=True)

	def init(self):
		_logger.info("******** Initializing AHA Analysis View ********")
		tools.drop_view_if_exists(self.env.cr, self._table)
		query = """
			CREATE OR REPLACE VIEW %s AS (
				SELECT
					MIN(t.id) as id,
					t.pcp_name,
					t.aha_completed_id,
					t.company_id,
					MIN(t.id) as ticket_id,
					MIN(t.create_date) as date_from,
					MAX(t.create_date) as date_to,
					COUNT(*) as ticket_count
				FROM helpdesk_ticket t
				GROUP BY t.pcp_name, t.aha_completed_id, t.company_id
			)
		""" % (self._table)
		_logger.info("Creating view with query: %s", query)
		self.env.cr.execute(query)