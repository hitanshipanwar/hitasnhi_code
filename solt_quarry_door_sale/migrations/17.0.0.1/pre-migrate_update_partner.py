import logging
from odoo import api, SUPERUSER_ID

_logger = logging.Logger(__name__)


def migrate(cr, version):
    if not version:
        return
    cr.execute("ALTER TABLE res_company ADD specs_sale_company_id integer ;")
    cr.execute("ALTER TABLE res_company ADD specs_cost_company_id integer ;")