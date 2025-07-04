# -*- coding: utf-8 -*-
##############################################################################
#                                                                            #
# Part of WMSSOFT. (Website: www.wmssoft.com.au).                            #
# See LICENSE file for full copyright and licensing details.                 #
#                                                                            #
##############################################################################

from odoo import fields, models, api


class AccountkMove(models.Model):
    _inherit = 'account.move'

    def make_post_to_draft_entries(self):
        for rec in self:
            print("rec---------------------------------",rec)
            rec.button_draft()
