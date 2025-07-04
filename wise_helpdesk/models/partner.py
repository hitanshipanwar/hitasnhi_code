from odoo import api, fields, models


class Partner(models.Model):
    _inherit = 'res.partner'

    old_id = fields.Char(string="Old ID")
    custom_create_uid = fields.Many2one('res.users', string='Data Created by', copy=True, store=True)
    custom_create_date = fields.Datetime(string='Data Created on', copy=True, store=True)

    insurance_company = fields.Char(string="Insurance Company")
    spmg_name = fields.Char(string="SPMG Name")
    spmg_npi = fields.Char(string="SPMG NPI")
    pmg_id = fields.Many2one(comodel_name='pmg', string="PMG ID")
    pmg_name = fields.Char(string="PMG Name")
    pmg_npi = fields.Char(string='PMG NPI')
    pcp_name = fields.Char(string="PCP Name")
    pcp_npi = fields.Char(string="PCP NPI")
    is_pcp = fields.Boolean(string="Is a PCP?")
    speciality_code = fields.Char(string='Speciality Code')
    speciality_description = fields.Char(string='Speciality Code Description')
    assigned_center = fields.Char(string="Assigned Center")

    member_id = fields.Char(string="Member ID")
    prev_member_id = fields.Char(string="Previous Member ID")
    membership_status = fields.Char(string="Membership Status")
    age = fields.Integer(string="Age")
    hchn = fields.Char(string="HCHN")
    sex = fields.Char(string="Sex")
    birth_date = fields.Date(string="Birth Date")
    phone_extension = fields.Char(string="Phone Ext.")

    alternate_phone = fields.Char(string="Phone Alternate")
    alternate_phone2 = fields.Char(string="Phone Alternate 2")

    region = fields.Char(string="Region")
    ases_prem = fields.Float(string="ASES Premium")
    paymonth = fields.Char(string="Paymonth")
    benefit_plan = fields.Char(string="Benefit Plan")
    benefit_plan_desc = fields.Char(string="Benefit Plan Description")
    tier = fields.Char(string="Tier")
    ratecell = fields.Char(string="Rate Cell")
    ratecell_description = fields.Char(string="Rate Cell Description")

    ipa_category = fields.Char(string="IPA Category")
    organization_id = fields.Char(string="Organization ID")
    organization = fields.Char(string="Organization")
    organization_npi = fields.Char(string="Organization NPI")
    billing_provider_name = fields.Char(string="Billing Provider Name")
    billing_provider_npi = fields.Char(string="Billing Provider NPI")
    membership_type = fields.Char(string="Membership Type")

    coverage = fields.Char(string="Coverage")
    raf = fields.Float(string="RAF")
    total_revenue = fields.Float(string="Total Revenue")
    cms_premium = fields.Float(string="CMS Premium")
    plantino_flag = fields.Char(string="Plantino Flag")
    hospice_flag = fields.Char(string="Hospice Flag")
    esrd_flag = fields.Char(string="ESRD Flag")
    cms_category = fields.Char(string="CMS Category")
    membership_key = fields.Char(string="Membership Key")
    helpdesk_team_member_id = fields.Many2one(comodel_name="helpdesk.team", string="Helpdesk Team Usuario")

    def write(self, vals):
        result = super(Partner, self).write(vals)
        if 'mobile' in vals:
            self.env['helpdesk.ticket'].update_mobile_numbers(self.id, vals['mobile'])
        return result