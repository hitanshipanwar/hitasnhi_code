# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name' : 'CRM Design',
    'version' : '0.27',
    'summary': 'CRM Design',
    'description': """
        CRM Design
    """,
    'author': "Spellbound Soft Solutions",
    'website': "http://spellboundss.com/",
    'maintainer': 'Spellbound Soft Solutions',
    'company': 'Spellbound Soft Solutions',
    'depends' : ['base','base_setup','crm','crm_iap_mine','sale','sale_crm','product','account','mail','account_payment','web','calendar','hr','purchase_stock','purchase','stock','sale_crm'],
    'data': [
        'data/design_product_data.xml',
        'data/fully_invoiced_crm_stage.xml',
        'security/ir.model.access.csv',
        'security/security.xml',
        'security/personal_lead.xml',
        'wizard/visit_appointment_view.xml',
        'wizard/account_payment_register_view_inherit.xml',
        'views/crm_views_inherited.xml',
        'wizard/reject_quotation_view.xml',
        'wizard/approve_quotation_view.xml',
        'wizard/stock_backorder_confirmation_view.xml',
        'views/picking_views.xml',
        'views/sale_order_views_inherited.xml',
        'views/account_move_inherit.xml',
        'views/hr_department_views_inherited.xml',
        'views/hr_employee_view.xml',
        'views/design_product_view.xml',
        'data/platform_crm_data.xml',
        'data/mail_compose_message_data.xml',
        'data/mail_compose_invoice_template.xml',
        'data/payment_term.xml',
        'data/ir_config_parameter_data.xml',
        'reports/mail_template_kitchen_design_data.xml',
        'reports/sale_order_portal_view_inherited.xml',
        'reports/account_move_portal_template_inherited.xml',
        'reports/product_requirment_sale_order_template.xml',
        'reports/report_header_template.xml',
        'reports/product_product_label.xml',
        'reports/shelf_talker_reports.xml',
        'reports/journa_items_report.xml',
        'reports/layouts.xml',
        'reports/payment_receipt_report.xml',
        'reports/invoice_pdf_report.xml',
        'views/res_partner_inherited.xml',
        'views/approval_request_views.xml',
        'views/crm_lead_views.xml',
        'views/account_payment_inherit.xml',
        'views/res_users_view_inherit.xml',
        'views/res_company.xml',
        'views/purchase_order_view.xml',
        'views/res_config_settings_view.xml',
        'views/uom_category_view.xml',
        'views/account_account_views.xml',
        'views/purchase_order_portal_template.xml',
        'views/platform.xml'
    ],

    'assets': {
        'web.assets_backend': [
            'crm_design/static/src/js/digital_sign.js',
            'crm_design/static/src/css/product_header.css',
            'crm_design/static/src/css/backend_signature_style.css',
            'crm_design/static/src/legacy/js/views/kanban/kanban_controller_inherit.js',
            'crm_design/static/src/legacy/xml/base.xml',
            # 'crm_design/static/src/js/settimeout.js',  
        ],
        'web.report_assets_common': [
           'crm_design/static/src/css/report_header.css',
        ],
        'web.assets_frontend': [
            'crm_design/static/src/css/style.css',
            'crm_design/static/src/js/approve_design.js',
            'crm_design/static/src/js/portal_signature.js',
            'crm_design/static/src/js/name_signature_extend.js',
        ],
        'web.assets_tests': [
          
        ],
        'web.qunit_suite_tests': [

        ],
        'web.assets_qweb': [
            'crm_design/static/src/xml/digital_sign.xml',
        ],
    },
    
    'license': 'LGPL-3',
}
