import logging
from odoo import api, SUPERUSER_ID

_logger = logging.Logger(__name__)


def migrate(cr, version):
    if not version:
        return
    cr.execute("ALTER TABLE door_family_field_line ADD sequence integer ;")
    cr.execute("ALTER TABLE door_family_field_line ADD display_type character varying ;")
    cr.execute("ALTER TABLE door_family_field_line ADD name character varying ;")