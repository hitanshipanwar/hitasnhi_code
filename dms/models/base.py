# -*- coding: utf-8 -*-

from odoo import models


class Base(models.AbstractModel):
    _inherit = "base"

    def unlink(self):
        """Cascade DMS related resources removal."""
        result = super().unlink()
        self.env["dms.file"].sudo().search(
            [("res_model", "=", self._name), ("res_id", "in", self.ids)]
        ).unlink()
        self.env["dms.directory"].sudo().search(
            [("res_model", "=", self._name), ("res_id", "in", self.ids)]
        ).unlink()
        return result
