import logging
from odoo import api, SUPERUSER_ID

_logger = logging.Logger(__name__)


def migrate(cr, version):
    if not version:
        return
    cr.execute("ALTER TABLE res_company ADD specs_deadbolt_categ_id integer ;")
    cr.execute("UPDATE specs_sale SET specs_moce_id=NULL;")