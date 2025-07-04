# -*- coding: utf-8 -*-

{
    "name": "Helpdesk Ticket Timesheet",
    "summary": "Add HR Timesheet to the tickets for Helpdesk Management.",
    "author": "Ionicx IT Solutions ",
    "website": "http://cognicx.com",
    "license": "AGPL-3",
    "category": "HRMS",
    "version": "16.0.1.0.0",
    "depends": [
        "helpdesk_mgmt_project",
        "hr_timesheet",
    ],
    "data": [
        "views/helpdesk_team_view.xml",
        "views/helpdesk_ticket_view.xml",
        "views/hr_timesheet_view.xml",
        # "report/report_timesheet_templates.xml",
    ],
    # "demo": ["demo/helpdesk_mgmt_timesheet_demo.xml"],
}