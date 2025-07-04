# -*- encoding: utf-8 -*-
#                                                                            #
#   OpenERP Module                                                           #
#   Copyright (C) 2013 Author <email@email.fr>                               #
#                                                                            #
#   This program is free software: you can redistribute it and/or modify     #
#   it under the terms of the GNU Affero General Public License as           #
#   published by the Free Software Foundation, either version 3 of the       #
#   License, or (at your option) any later version.                          #
#                                                                            #
#   This program is distributed in the hope that it will be useful,          #
#   but WITHOUT ANY WARRANTY; without even the implied warranty of           #
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the            #
#   GNU Affero General Public License for more details.                      #
#                                                                            #
#   You should have received a copy of the GNU Affero General Public License #
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.    #
#                                                                            #

{
    "name": "Report Pdf Preview",
    "version": "2.0",
    "depends": ["web"],
    'author': 'Spellbound Soft Solutions ',
    'website': 'http://www.spellboundss.com',
    "category": "web",
    "description": """
    """,
    "license": "AGPL-3",
    "data": [
        # 'views/assets.xml',
    ],
    'depends' : ['base'],
    "init_xml": [],
    'update_xml': [],
    'demo_xml': [],
     'assets': {
        'web.assets_backend': [
            'report_pdf_preview/static/src/scss/preview_dialog.scss',
            'report_pdf_preview/static/src/js/web_pdf_preview.js',
            "report_pdf_preview/static/src/xml/report_viewer.xml",
        ],
        # 'web.assets_qweb': [
        # ]
    },
    # "qweb": [
    #     "report_pdf_preview/static/src/xml/report_viewer.xml",
    # ],
    'images': ['static/description/icon.jpg','static/description/main_screenshot.png'],
    'installable': True,
    'active': False,
    #    'certificate': '',
}
