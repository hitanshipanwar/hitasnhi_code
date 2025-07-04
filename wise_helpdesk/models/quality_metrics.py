from odoo import api, fields, models
from datetime import datetime


class QualityMetrics(models.Model):
    _name = 'quality.metrics'
    _description = 'Quality Metrics'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin', 'utm.mixin']

    quality_type = fields.Selection([('alianza','alianza'),('rse','rse'),('insalud','insalud')],string='Type')
    custom_create_uid = fields.Many2one('res.users', string='Data Created by', copy=True, store=True)
    custom_create_date = fields.Datetime(string='Data Created on', copy=True, store=True)

    name = fields.Char(string="Name")
    partner_id = fields.Many2one(comodel_name='res.partner', string='Contact')
    pcp_name = fields.Char(string='PCP Name', related='partner_id.pcp_name', store=True)
    pcp_npi = fields.Char(string='PCP NPI', related='partner_id.pcp_npi', store=True)
    pmg_name = fields.Char(string='PMG Name', related='partner_id.pmg_name', store=True)
    pmg_npi = fields.Char(string='PMG NPI', related='partner_id.pmg_npi', store=True)
    member_id = fields.Char(string="Member ID", related='partner_id.member_id', store=True)
    member_name = fields.Char(string='Member Name', related='partner_id.name', store=True)
    sex = fields.Char(string='Sex', related='partner_id.sex', store=True)
    birth_date = fields.Date(string='Birth Date', related='partner_id.birth_date', store=True)
    phone = fields.Char(string='phone', related='partner_id.phone', store=True)
    membership_status = fields.Char(string='Membership Status', related='partner_id.membership_status', store=True)
    paymonth = fields.Char(string='Paymonth', related='partner_id.paymonth', store=True)
    city = fields.Char(string="City", related='partner_id.city', store=True)

    old_id = fields.Char(string='Old ID')
    insurance_company = fields.Char(string="Insurance Company", related='partner_id.insurance_company', store=True)
    organization = fields.Char(string='Organization', related='partner_id.organization')

    measure_category = fields.Char(string='Measure Category')
    quality_measure = fields.Char(string='Quality Measure')
    measure_description = fields.Char(string='Measure Description')
    measure_key = fields.Char(string='Measure Key')
    current_rate_cell = fields.Char(string='Current Rate Cell')
    current_rate_cell_desc = fields.Char(string='Current Rate Cell Description')
    raf_score = fields.Char(string='RAF Score')
    measure_status = fields.Char(string='Measure Status')
    diagnosis_code = fields.Char(string='Diagnosis Code')
    diagnosis_description = fields.Char(string='Diagnosis Description')
    drug_name = fields.Char(string='Drug Name')
    estimated_expiration_date = fields.Char(string='Estimated Expiration Date')
    last_service_code = fields.Char(string='Last Service Code')
    last_service_date = fields.Char(string='Last Service Date')

    render_provider = fields.Char(string='Render Provider')
    render_provider_npi = fields.Char(string='Render Provider NPI')
    app_date = fields.Char(string='Appointment Date')
    current_service_code = fields.Char(string='Current Service Code')
    current_service_date = fields.Char(string='Current Service Date')
    current_diagnosis_code = fields.Char(string='Current Diagnosis Code')
    transmission_date = fields.Char(string='Transmission Date')

    #has to be selection field
    internal_compliance_status = fields.Selection([('Awaiting Billing Transmission','Awaiting Billing Transmission'),
                                                   ('Certification Completed - Need Appointment','Certification Completed - Need Appointment'),
                                                   ('Compliant','Compliant'),
                                                   ('Need Appointment','Need Appointment'),
                                                   ('Non-Compliant','Non-Compliant'),
                                                   ('Not Applicable','Not Applicable'),
                                                   ('Schedule Appointment','Schedule Appointment')],string='Internal Compliance Status')

    insalud_internal_compliance_status = fields.Selection([('Compliant','Compliant'),
                                                            ('Non-Compliant','Non-Compliant'),
                                                            ('Not Applicable','Not Applicable'),
                                                            ('Pending','Pending')],string='Internal Compliance Status')

    notes = fields.Text(string='Notes')
    rescued_flag = fields.Char(string='Rescued Flag')
    official_compliance_status = fields.Char(string='Official Compliance Status')
    official_compliance_date = fields.Date(string='Official Compliance Date')
    official_expiration_date = fields.Date(string='Official Expiration Date')

    #insalud
    estimated_month_closure = fields.Date(string='Estimated Month Closure')
    hedis_value_set = fields.Char(string='HEDIS Value Set')
    status = fields.Selection([('Cambiar Dosis','Cambiar Dosis'),
                               ('Cambio de IPA','Cambio de IPA'),
                               ('Completado','Completado'),
                               ('Contraindicado','Contraindicado'),
                               ('En Proceso','En Proceso'),
                               ('Evidencia obtenida InnovaMD','Evidencia obtenida InnovaMD'),
                               ('Investigacion MMM','Investigacion MMM'),
                               ('No evidencia de Despacho','No evidencia de Despacho'),
                               ('Repetir','Repetir'),
                               ('Upload-Innova Gap Closure','Upload-Innova Gap Closure'),
                               ('N/A','N/A')], string="Status")
    #rse
    current_hchn_classification = fields.Char(string='Current HCHN Clarification')
    auditor_last_update_by = fields.Many2one('res.users', string="Auditor Last Update By")
    auditor_update_date = fields.Datetime(string="Auditor Last Update Date")


    @api.model
    def create(self, vals):
        if self.env.user.has_group('wise_helpdesk.group_auditors_access'):
            vals['auditor_last_update_by'] = self.env.user.id
            vals['auditor_update_date'] = datetime.now()
        return super(QualityMetrics, self).create(vals)

    def write(self, vals):
        if self.env.user.has_group('wise_helpdesk.group_auditors_access'):
            vals['auditor_last_update_by'] = self.env.user.id
            vals['auditor_update_date'] = datetime.now()
        return super(QualityMetrics, self).write(vals)