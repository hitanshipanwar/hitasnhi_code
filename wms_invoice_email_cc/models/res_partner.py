# -*- coding: utf-8 -*-
##############################################################################
#                                                                            #
# Part of WMSSOFT. (Website: www.wmssoft.com.au).                            #
# See LICENSE file for full copyright and licensing details.                 #
#                                                                            #
##############################################################################

from odoo import fields, models, api


class ResPartner(models.Model):
    _inherit = "res.partner"

    mail_cc_invoice = fields.Char(string="CC Invoice Email")

    @api.model
    def create(self, vals):
        result = super(ResPartner, self).create(vals)
        if result.parent_id and not result.parent_id.parent_id:
            result.mail_cc_invoice = result.parent_id.email
        else:
            result.mail_cc_invoice = result.parent_id.mail_cc_invoice
        return result
