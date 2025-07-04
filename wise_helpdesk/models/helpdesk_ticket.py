from odoo import api, fields, models


class HelpdeskTicket(models.Model):
    _inherit = 'helpdesk.ticket'

    custom_create_uid = fields.Many2one('res.users', string='Data Created by', copy=True, store=True)
    custom_create_date = fields.Datetime(string='Data Created on', copy=True, store=True)

    phone_number = fields.Char(string="Phone Number", related="partner_id.phone", store=True)
    mobile_number = fields.Char(string="Mobile Number", readonly=True)
    is_solved = fields.Boolean(string="Is Solved?", related="stage_id.is_solved")
    alternate_phone = fields.Char(string="Alternate Phone", related="partner_id.alternate_phone", store=True)
    alternate_phone2 = fields.Char(string="Alternate 2nd Phone")
    member_id = fields.Char(string="Member ID", related="partner_id.member_id", store=True)
    insurance_company = fields.Char(string="Insurance Company", related="partner_id.insurance_company", store=True)
    competition = fields.Char(string="Competition")
    coverage = fields.Char(string="Coverage")
    hchn = fields.Char(string="Chronic or HCHN")
    ratecell_description = fields.Char(string="Rate Cell Description")
    birth_date = fields.Date(string="Birthdate", related="partner_id.birth_date", store=True)
    age = fields.Integer(string="Age", related="partner_id.age", store=True)
    sex = fields.Char(string="Sex", related="partner_id.sex", store=True)
    city = fields.Char(string="City", related="partner_id.city", store=True)
    lost_call_phone = fields.Char(string="Lost Call Phone")
    visit_flag = fields.Char(string="Visit Flag")
    pmg_name = fields.Char(string="PMG Name", related="partner_id.pmg_name", store=True)
    pcp_name = fields.Char(string="PCP Name", related="partner_id.pcp_name", store=True)
    medicaid_expiration = fields.Date(string="Medicaid Expiration Date")
    category = fields.Many2one(comodel_name="helpdesk.category", string="Category")
    date_time_coordinated = fields.Datetime(string="Date and Time - Coordinated")
    aha_completed_id = fields.Many2one('aha.completed.type',string="AHA Completed")
    customer_satisfaction = fields.Selection([('No Disponible','No Disponible'),('Pobre','Pobre'),('Regular','Regular'),('Excelente','Excelente')],string="Customer Satisfaction Level")
    vaccination_status = fields.Selection([('N','N'),('Y','Y')],string="Vaccination Status")
    covid_19_vaccine = fields.Selection([('Pfizer','Pfizer'),('Moderna','Moderna'),('Johnson & Johnson','Johnson & Johnson')],string="COVID-19 vaccine")
    preferred_location = fields.Char(string="Preferred Location")
    old_id = fields.Char(string="Old ID")

# teleconsultas
    # paso1
    patient_phone = fields.Char(string="Teléfono Paciente")
    start_call_datetime = fields.Datetime(string="Día y Hora Inicio de la Llamada")
    reason = fields.Selection([
        ('Razon de la llamada','Consulta Médica.'),
        ('Consulta Médica-COVID-19','Consulta Médica-COVID-19'),
        ('Información sobre servicios.','Información sobre servicios.'),
        ('Orientación COVID-19.','Orientación COVID-19.'),
        ('Receta','Receta'),
        ('Otros','Otros')], string="Razon de la llamada")
    call_911 = fields.Selection([
        ('Yes','Yes'),
        ('No','No')], string="Se llamó al 911?")
    current_location = fields.Char(string="Dónde se encuentra usted ahora mismo?")
    accompanied = fields.Selection([
        ('Yes','Yes'),
        ('No','No')], string="Está usted acompañado?")
    companion_drivers = fields.Selection([
        ('Yes','Yes'),
        ('No','No')], string="Acompañante conduce y pudede llevarle a sala de emergancias")
    present_symptoms = fields.Char(string="Cuáles son los síntomas que presenta?")
    symptoms_since = fields.Char(string="Desde cuándo presenta los síntomas?")

    # paso2
    previous_condition1 = fields.Selection([
        ('Anemia','Anemia'),
        ('Artritis','Artritis'),
        ('Asma','Asma'),
        ('Ataques de pánico','Ataques de pánico'),
        ('Ataques de ansiedad','Ataques de ansiedad'),
        ('Colesterol','Colesterol'),
        ('Colitis','Colitis'),
        ('Diabetes','Diabetes'),
        ('Fibromialgía','Fibromialgía'),
        ('Gastritis','Gastritis'),
        ('Hipertensión','Hipertensión'),
        ('Hipoglucemia','Hipoglucemia'),
        ('Migraña','Migraña'),
        ('Neuropatía','Neuropatía'),
        ('Obesidad mórbida','Obesidad mórbida'),
        ('Sinusitis','Sinusitis'),
        ('Tiroides','Tiroides')], string="Condicion Previa 1")
    previous_condition2 = fields.Selection([
        ('Anemia','Anemia'),
        ('Artritis','Artritis'),
        ('Asma','Asma'),
        ('Ataques de pánico','Ataques de pánico'),
        ('Ataques de ansiedad','Ataques de ansiedad'),
        ('Colesterol','Colesterol'),
        ('Colitis','Colitis'),
        ('Diabetes','Diabetes'),
        ('Fibromialgía','Fibromialgía'),
        ('Gastritis','Gastritis'),
        ('Hipertensión','Hipertensión'),
        ('Hipoglucemia','Hipoglucemia'),
        ('Migraña','Migraña'),
        ('Neuropatía','Neuropatía'),
        ('Obesidad mórbida','Obesidad mórbida'),
        ('Sinusitis','Sinusitis'),
        ('Tiroides','Tiroides')], string="Condicion Previa 2")
    previous_condition3 = fields.Char(string="Condicion Previa 3")
    last_3_hours_medication = fields.Selection([
        ('Yes','Yes'),
        ('No','No')], string="Ha tomado algún medicamento en las últimas tres (3) horas?")
    medication_name = fields.Char(string="Nombre de los medicamentos indicados")

    # paso3
    feel_pain = fields.Selection([
        ('Yes','Yes'),
        ('No','No')], string="¿Siente usted dolor?")
    pain_level = fields.Selection([
        ('Severo','Severo'),
        ('Moderado','Moderado'),
        ('Leve','Leve')], string="Pain Level")
    pcp_last_visit = fields.Date(string="PCP Last Visit")
    child_vaccination = fields.Selection([
        ('Yes','Yes'),
        ('No','No')], string="Si es paciente pedriático: ¿Se encuentran al día las vacunas del niño?")

    # paso4
    beneficiary_recommendation = fields.Selection([
        ('Orientación sobre servicios de PMG','Orientación sobre servicios de PMG'),
        ('Orientación COVID-19','Orientación COVID-19'),
        ('Referido a Médico Primario','Referido a Médico Primario'),
        ('Referido a Sala de Emergencias','Referido a Sala de Emergencias'),
        ('Se brindó información','Se brindó información')], string="Recomendación para el beneficiario")
    nutritionist = fields.Selection([
        ('Yes','Yes'),
        ('No','No')], string="Referido a Nutricionista")
    emergency_room = fields.Selection([
        ('Lista','Lista')], string="Sala de Emergencia a la que se refirio")
    municipal_emergency_room = fields.Many2one("emergency.room", string="Municipio de la sala de emergencia")
    nurse_id = fields.Many2one(comodel_name="res.users", string="Nombre de la enfermera que atendió el caso")
    triage_info = fields.Text(string="Triage Information")
    call_ended = fields.Datetime(string="Día y Hora Finalizada la Llamada")


# insalud Censo
    beneficiary_name = fields.Char(string="Beneficiary Name", related="partner_id.name", store=True)
    facility = fields.Char(string="Facility")
    hospital_npi = fields.Char(string="Hospital NPI")
    place_service = fields.Char(string="Place of Services")
    ipa_group = fields.Char(string="IPA Group")
    census_type = fields.Char(string="Census Type")
    admission_date = fields.Date(string="Admission Date")
    discharge_date = fields.Date(string="Discharge Date")
    census_type2 = fields.Char(string="Census Type 2")
    los = fields.Integer(string="LoS")
    admitting_physician = fields.Char(string="Admitting Physician")
    admitting_physician_npi = fields.Char(string="Admitting Physician NPI")
    admitting_phone = fields.Char(string="Admitting Phone")
    admission_diagnosis = fields.Char(string="Admission Diagnosis")
    admission_diagnosis_description = fields.Char(string="Admission Diagnosis Description")
    discharge_diagnosis = fields.Char(string="Discharge Diagnosis")
    discharge_diagnosis_description = fields.Char(string="Discharge Diagnosis Description")

    download_date = fields.Date(string="Download Date")
    production_date = fields.Date(string="Production Date")
    ipa_category = fields.Char(string="ipa_category")
    pcp_npi = fields.Char(string="PCP NPI")
    new_admission_flag = fields.Char(string="New Admission Flag")
    new_discharge_flag = fields.Char(string="New Discharge Flag")
    new_hospital_visit_flag = fields.Char(string="New Hospital Visits Flag")
    new_readmission_flag = fields.Char(string="New Readmission Flag")
    readmission_flag = fields.Char(string="Readmission Flag")
    pcp_abreviation = fields.Char(string="PCP Name Abreviation")
    lace_score = fields.Integer(string="LACE Score")

    # desafilicion
    razon_desafiliacion = fields.Selection([
        ('Vital - No aplica','Vital - No aplica'),
        ('Vital - PMG de Preferencia','Vital - PMG de Preferencia'),
        ('Vital - PMG Alianza','Vital - PMG Alianza'),
        ('Vital - PMG Anterior','Vital - PMG Anterior'),
        ('Vital - Insatisfacción de servicios','Vital - Insatisfacción de servicios'),
        ('Vital - Accesibilidad','Vital - Accesibilidad'),
        ('Vital - Especialistas','Vital - Especialistas'),
        ('Vital - Se rehúsa a ofrecer razones de cambio','Vital - Se rehúsa a ofrecer razones de cambio'),
        ('Vital - Disponibilidad de Citas','Vital - Disponibilidad de Citas'),
        ('Vital - Horarios del centro','Vital - Horarios del centro'),
        ('Vital - Referidos','Vital - Referidos'),
        ('Vital - No recibió servicios por PMG','Vital - No recibió servicios por PMG'),
        ('Buydown','Buydown'),
        ('Beneficios', 'Beneficios'),
        ('Cambio involuntario','Cambio involuntario'),
        ('Especialistas','Especialistas'),
        ('Máximo de Cubierta','Máximo de Cubierta'),
        ('Medicamentos / OTC','Medicamentos / OTC'),
        ('Quiere conocer servicios de SSS','Quiere conocer servicios de SSS'),
        ('Quiere conocer servicios de MCS','Quiere conocer servicios de MCS'),
        ('Quiere conocer servicios de Humana','Quiere conocer servicios de Humana'),
        ('Se desplaza a EU','Se desplaza a EU'),
        ('Se rehusó a ofrecer razones','Se rehusó a ofrecer razones'),
        ('Servicio','Servicio'),
        ('Transportación','Transportación')], string="Razón Desafiliación")
    estatus_boleta = fields.Selection([
        ('Pending','Pending'),
        ('Done','Done'),
        ('Cancelled','Cancelled')], string="Estatus Boleta")
    pcp_desafiliacion = fields.Char(string="PCP Desafiliacion")
    especialidad_desafiliacion = fields.Char(string="Especialidad Desafiliacion")


# Telemedicina
    use_phone_or_pc = fields.Selection([
        ('Si','Si'),
        ('No','No'),
        ('Desconocido','Desconocido'),
        ('No aplica','No aplica')], string="Tiene y sabe usar celular, tableta o PC inteligente")

    has_email = fields.Selection([
        ('Si','Si'),
        ('No','No'),
        ('Desconocido','Desconocido'),
        ('No aplica','No aplica')], string="Paciente tiene correo electronico")

    has_signal = fields.Selection([
        ('Si','Si'),
        ('No','No'),
        ('Desconocido','Desconocido'),
        ('No aplica','No aplica')], string="Paciente tiene buena senal de celular en su hogar")

    has_internet = fields.Selection([
        ('Si','Si'),
        ('No','No'),
        ('Desconocido','Desconocido'),
        ('No aplica','No aplica')], string="Paciente tiene internet en su hogar")

    has_high_speed_internet = fields.Selection([
        ('Si','Si'),
        ('No','No'),
        ('Desconocido','Desconocido'),
        ('No aplica','No aplica')], string="Paciente tiene Internet de alta calidad?")

    receive_services = fields.Selection([
        ('Si','Si'),
        ('No','No'),
        ('Desconocido','Desconocido'),
        ('No aplica','No aplica')], string="Paciente interesa recibir servicios de telemedicina")

    inform_patient_portal = fields.Selection([
        ('Si','Si'),
        ('No','No'),
        ('Desconocido','Desconocido'),
        ('No aplica','No aplica')], string="Paciente informado sobre portal del paciente del centro")

    used_patient_portal = fields.Selection([
        ('Si','Si'),
        ('No','No'),
        ('Desconocido','Desconocido'),
        ('No aplica','No aplica')], string="Paciente ha usado el portal de pacientes")

#Encuestas

    encuesta = fields.Selection([
        ('MMM Encuesta How Are You Call','MMM Encuesta How Are You Call')], string="Encuesta")


    encuesta_question1 = fields.Selection([
        ('Buena','Buena'),
        ('Excelente','Excelente'),
        ('Regular','Regular')], string="Cómo se siente con el servicio que le hemos brindado?")
    encuesta_question2 = fields.Selection([
        ('Si','Si'),
        ('No','No')], string="Ha recibido los servicios que ha necesitado de parte de MMM hasta este momento?")
    encuesta_question3 = fields.Selection([
        ('Si','Si'),
        ('No','No')], string="Tiene alguna duda sobre algún proceso o beneficio de su cubierta?")
    encuesta_question4 = fields.Selection([
        ('Si','Si'),
        ('No','No')], string="Hay algo adicional en lo que pueda servirle en esta llamada?")

    @api.model
    def create(self, vals):
        if vals.get('partner_id'):
            partner = self.env['res.partner'].browse(vals['partner_id'])
            vals['mobile_number'] = partner.mobile
        return super(HelpdeskTicket, self).create(vals)

    @api.onchange('partner_id')
    def onchange_set_phone_number(self):
        for rec in self:
            if rec.partner_id:
                rec.write({'mobile_number': rec.partner_id.mobile})

    @api.model
    def update_mobile_numbers(self, partner_id, new_mobile):
        tickets = self.search([
            ('partner_id', '=', partner_id)
        ])
        for ticket in tickets:
            if not ticket.is_solved:
                ticket.write({'mobile_number': new_mobile})

class AhaCompletedType(models.Model):
    _name = 'aha.completed.type'

    name = fields.Char(string='Name')