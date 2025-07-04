# © 2004-2009 Tiny SPRL (<http://tiny.be>).
# © 2014-2017 Tecnativa - Pedro M. Baeza
# © 2016 ACSONE SA/NV (<http://acsone.eu>)
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
{
    "name": "Purchase order lines with discounts",
    "version": "16.0.1",
    'summary': 'Purchase order lines with discounts',
    'description': """
        Purchase Order
    """,
    "author": "Spellbound Soft Solutions ",
    "category": "Purchase Management",
    "website": "http://spellboundss.com/",
    'maintainer': 'Spellbound Soft Solutions',
    'company': 'Spellbound Soft Solutions',
    "depends": ["purchase_stock"],
    "data": [
        "views/purchase_discount_view.xml",
        "views/report_purchaseorder.xml",
        "views/product_supplierinfo_view.xml",
        "views/res_partner_view.xml",
        "views/account_move_line.xml",
    ],
    "license": "AGPL-3",
    "installable": True,
    'application': True,
    'auto_install': False,
    "images": ["images/purchase_discount.png"],
}
