# Copyright 2016 Flavio Corpa <flavio.corpa@tecnativa.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
{
    "name": "Web Widget - Image Download",
    "summary": "Allows to download any image from its widget",
    "version": "14.0.1.0.0",
    "category": "web",
    'author': 'Spellbound Soft Solutions',
    'website': 'http://spellboundss.com/',
    'company': 'Spellbound Soft Solutions',
    "license": "LGPL-3",
    "application": False,
    "installable": True,
    "data": ["views/assets.xml"],
    "depends": ["web"],
    "qweb": ["static/src/xml/web_widget_image_download.xml"],
}
