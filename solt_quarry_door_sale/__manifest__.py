# -*- coding: utf-8 -*-
{
    'name': "Specs - Sales",

    'summary': "Adds the Specs functionalities",
    'author': "Soltein SA de CV",
    'website': "https://www.soltein.mx",
    'contributors': ['Yosbanis Vicente<90yobi90@gmail.com>'],
    'category': 'Uncategorized',
    'version': '17.0.0.4',
    'license': 'LGPL-3',
    'depends': ['base',
                'sale_management',
                'sale_crm',
                'mail',
                'solt_quarry_door_product',
                'sale_purchase'
            ],
    'data': [
        'security/ir_module_category.xml',
        'security/res_groups.xml',
        'security/ir_rules.xml',
        'security/ir.model.access.csv',
        'data/stage_cantera_type_data.xml',
        'views/specs_sale.xml',
        'views/door_glass_specs_views.xml',
        'views/sale_order_views.xml',
        'views/door_accessories_views.xml',
        'views/res_config_settings_views.xml',
        'views/door_special_preparations_views.xml',
        'views/door_family_views.xml',
        'views/product_template_views.xml',
        'views/door_hardware_views.xml',
        'views/crm_team_views.xml',
        'views/sale_portal_templates_views.xml',
        'views/res_partner_views.xml',

        'report/ir_actions_report_templates.xml',
        'report/ir_actions_report.xml',

        'views/menus.xml',
    ],
}

