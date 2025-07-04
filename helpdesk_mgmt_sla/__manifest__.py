# -*- coding: utf-8 -*-

{
    "name": "Helpdesk Ticket SLA",
    "summary": "Add SLA to the tickets for Helpdesk Management.",
    "author": "Ionicx IT Solutions",
    "website": "http://cognicx.com",
    "license": "AGPL-3",
    "category": "HRMS",
    "version": "14.0.2.0.0",
    "depends": ["base", "helpdesk_mgmt", "resource"],
    "data": [
        "data/helpdesk_sla_cron.xml",
        "data/deadline_reminder_action_data.xml",
        "security/ir.model.access.csv",
        "views/helpdesk_sla_views.xml",
        "views/helpdesk_ticket_views.xml",
        "views/helpdesk_ticket_team_views.xml",
    ],
    # "demo": ["demo/helpdesk_mgmt_sla_demo.xml"],
}
