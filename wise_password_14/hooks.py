from odoo import api, SUPERUSER_ID
from datetime import datetime


def post_init_hook(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    for rec in env['res.users'].search([]):
        rec.date_password_changed = datetime.now()