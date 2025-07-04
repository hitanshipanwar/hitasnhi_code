import logging
from odoo import api, SUPERUSER_ID

_logger = logging.Logger(__name__)


def migrate(cr, version):
    if not version:
        return
    cr.execute("""
                UPDATE specs_type s
                   SET sequence = 3, name='Spec Ready', description='This stage will indicate when the spec has been captured and the design along with the order are awaiting the client signature.'
                 WHERE s.code = 'price'
                """)
    cr.execute("""
                    UPDATE specs_type s
                       SET sequence = 6
                     WHERE s.code = 'cancel'
                    """)