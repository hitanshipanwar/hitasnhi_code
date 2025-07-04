# -*- coding: utf-8 -*-
{
    'name': "Documents - Spec",
    'summary': "Project from documents",
    'author': "Soltein SA de CV",
    'website': "https://www.soltein.mx",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',
    'depends': ['solt_quarry_door_sale', 'documents', 'documents_sign'],

    # always loaded
    'data': [
        'data/documents_folder_data.xml',
        'data/documents_facet_data.xml',
        'data/documents_workflow_rule_data.xml',
        'views/documents_folder_views.xml',
        'views/documents_facet_views.xml',
        'views/documents_tag_views.xml',
        'views/documents_document_views.xml',
        'views/specs_views.xml'
    ],
    'license': 'OEEL-1',
    'post_init_hook': '_documents_specs_post_init',
}

