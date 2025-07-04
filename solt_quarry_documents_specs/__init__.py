# -*- coding: utf-8 -*-

from . import controllers
from . import models


def _documents_specs_post_init(env):
    env['specs.sale'].search([('use_documents', '=', True)])._create_missing_folders()
