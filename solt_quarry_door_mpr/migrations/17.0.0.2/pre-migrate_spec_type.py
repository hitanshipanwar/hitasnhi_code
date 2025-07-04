import logging

_logger = logging.Logger(__name__)


def migrate(cr, version):
    if not version:
        return
    cr.execute("""
            UPDATE specs_type s
               SET sequence=5
             WHERE s.code = 'bom'
            """)