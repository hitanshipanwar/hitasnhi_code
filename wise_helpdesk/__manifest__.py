{
    "name": "Wise Solution - CRA base fields",
    "summary": "Wise Solution - CRA base fields",
    "description": """
Task Id: 3169573, 3185116
Wise Solutions is a help desk provider with Databases with more than 200.000 contacts and many users
creating helpdesk tickets in Odoo. They track how many tickets were created and updated for every user
per day, week, month in the helpdesk app.

Throughout their different projects, they have created several Studio fields in the res.partner model
and helpdesk.ticket model.

For the CRA project, the partner needs the creation of the following fields as BASE fields since the
start of the project. Partner is upgrading this project from zero (no Odoo upgrade script will be used),
he also needs three studio modules to be upgraded and installed in their new Odoo 16 database (including
ALL the information in them)
""",
    "author": "Odoo, Inc",
    "website": "http://www.odoo.com",
    "category": "Custom Developments",
    "version": "0.2",
    "license": "OPL-1",
    "depends": [
        "helpdesk",
        "contacts"
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/quality_measure_views.xml",
        "views/rse_quality_views.xml",
        "views/insalud_quality_views.xml",
        "views/pmg_views.xml",
        "views/pcp_views.xml",
        "views/res_partner_form_view.xml",
        "views/helpdesk_ticket_form.xml",
        "views/emergency_room_inherit.xml",
        "views/helpdesk_category_view.xml",
        "views/res_users_form.xml",
        "views/helpdesk_stage.xml",
        "views/auditor.xml"

    ],
}
