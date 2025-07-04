# -*- coding: utf-8 -*-
##############################################################################
#                                                                            #
# Part of WMSSOFT. (Website: www.wmssoft.com.au).                            #
# See LICENSE file for full copyright and licensing details.                 #
#                                                                            #
##############################################################################

from odoo import models


class OutstandingStatementWizard(models.TransientModel):
    """Outstanding Statement wizard."""

    _name = "outstanding.statement.wizard"
    _inherit = "statement.common.wizard"
    _description = "Outstanding Statement Wizard"

    def _export(self):
        """Export to PDF."""
        data = self._prepare_statement()
        return self.env.ref(
            "partner_statement.action_print_outstanding_statement"
        ).report_action(self.ids, data=data)
