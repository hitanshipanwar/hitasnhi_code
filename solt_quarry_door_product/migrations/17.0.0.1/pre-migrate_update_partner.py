import logging
from odoo import api, SUPERUSER_ID

_logger = logging.Logger(__name__)


def migrate(cr, version):
    if not version:
        return
    cr.execute("ALTER TABLE door_hardware_list DROP COLUMN pricelist_id;")