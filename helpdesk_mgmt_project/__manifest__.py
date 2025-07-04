# -*- coding: utf-8 -*-

{
    "name": "Helpdesk Project",
    "summary": "Add the option to select project in the tickets.",
    "version": "16.0.1.0.1",
    "license": "AGPL-3",
    "category": "HRMS",
    "author": "Ionicx IT Solutions",
    "website": "http://cognicx.com",
    "depends": ["helpdesk_mgmt", "project"],
    "data": [
        "views/helpdesk_ticket_view.xml",
        "views/helpdesk_ticket_team_view.xml",
        "views/project_view.xml",
        "views/project_task_view.xml",
    ],
    "development_status": "Beta",
    "auto_install": True,
}
