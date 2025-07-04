from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    ncs_username = fields.Char("NCS Username", copy=False, help="UserName provided by canada post.")
    ncs_password = fields.Char("NCS Password", copy=False, help="Password provided by canada post.")
    ncs_customer_number = fields.Char("Customer Number", copy=False,
                                      help="The mailed by customer, Customer number provided by canada post.")
    use_canada_post_shipping_provider = fields.Boolean(copy=False, string="Are You Using Canada Shipping Provider?",
                                                           help="If use Canada shipping Integration than value set "
                                                                "TRUE.",
                                                           default=False)
    ncs_contract_id = fields.Char("NCS Contract-Id")