##############################################################################
#
# Bista Solutions Pvt. Ltd
# Copyright (C) 2020 (https://www.bistasolutions.com)
#
##############################################################################

{
    'name': "Client Bista ODOO-Bill.com Connector",
    'version': '1.0',
    'author': 'Bista Solutions Pvt. Ltd.',
    'website': "https://www.bistasolutions.com",
    'license': 'OPL-1',
    'category': 'Accounting',
    'depends': ['base','account', 'l10n_us', 'contacts', 'payment', 'purchase', 'web', 'mail'],
    'description': """Connector of ODOO and Bill.com""",
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        'data/cron.xml',
        'views/res_config_setting_view.xml',
        'views/res_partner.xml',
        'views/res_partner_bank.xml',
        'views/account_move.xml',
        'views/account_payment_view.xml',
        'views/config_view.xml',
        'wizard/bulk_send_bill_com.xml',
        'wizard/bulk_send_vendor_bill_com.xml',
        'wizard/update_company_data_wizard_view.xml',
        'views/scheduler.xml',
        'views/journal.xml',
        'views/error_logs.xml',
        'views/account_account.xml',
        'views/payment_methods.xml',
        'views/ir_attachment_view.xml',
        'views/account_payment_term_view.xml',
        'views/res_users.xml'
    ],
    # 'assets': {
    #     'web.assets_backend': [
    #         'client_bista_odoo_bill_com_connector/static/src/components/attachment_card/attachment_card.xml',
    #         'client_bista_odoo_bill_com_connector/static/src/components/attachment_image/attachment_image.xml',
    #         'client_bista_odoo_bill_com_connector/static/src/components/attachment_image/attachment_image.scss',

    #         'client_bista_odoo_bill_com_connector/static/src/models/attachment/attachment.js',
    #     ],

    # },
    'installable': True,
    'auto_install': False,
}
