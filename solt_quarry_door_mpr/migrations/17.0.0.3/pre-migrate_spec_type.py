import logging

_logger = logging.Logger(__name__)


def migrate(cr, version):
    if not version:
        return
    cr.execute("""
            UPDATE specs_type s
               SET name='In Production'
             WHERE s.code = 'bom'
            """)