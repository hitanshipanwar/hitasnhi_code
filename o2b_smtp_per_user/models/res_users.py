# -*- coding: utf-8 -*-
##########################################################################
# Author      : O2b Technologies Pvt. Ltd.(<www.o2btechnologies.com>)
# Copyright(c): 2016-Present O2b Technologies Pvt. Ltd.
# All Rights Reserved.
#
# This program is copyright property of the author mentioned above.
# You can`t redistribute it and/or modify it.
#
##########################################################################

from odoo import api, fields, models, _

class IrMailSserver(models.Model):
    _name = 'ir.mail_server'
    _inherit = ['ir.mail_server', 'google.gmail.mixin', 'microsoft.outlook.mixin']


    default = fields.Boolean(string="Default Server")
    smtp_user = fields.Char(string='Username', help="Optional username for SMTP authentication", groups=False)
    smtp_pass = fields.Char(string='Password', help="Optional password for SMTP authentication", groups=False)

    @api.onchange("default")
    def onchange_default(self):
        if self.default:
            search_mail_server = self.env['ir.mail_server'].search([('default','=',True)])
            # print("search_mail_server === ",search_mail_server)
            if search_mail_server:
                search_mail_server.default = False

    def action_check_settings_access(self):
        if not self.env.user.has_group('base.group_system'):
            return {
                'type': 'ir.actions.act_url',
                'url': '/web',
                'target': 'self',
            }
        else:
            return self.env.ref('base.res_config_setting_act_window').read()[0]


class Users(models.Model):
    _inherit = "res.users"

    mail_server_id = fields.Many2one('ir.mail_server', string='Outgoing Mail Server')

    # @api.multi
    def action_create_add(self):
        # opens server wizard
        search_mail_server = self.env['ir.mail_server'].sudo().search([('smtp_user', '=', self.login)], limit=1)
        view_id = self.env.ref('o2b_smtp_per_user.ir_mail_server_add_form').id
        if search_mail_server:
            vals = {
                'mail_server_id': search_mail_server.id,
                'smtp_user': search_mail_server.smtp_user,
                'smtp_pass': search_mail_server.smtp_pass,
                'name': search_mail_server.name,
                'smtp_host': search_mail_server.smtp_host,
                'smtp_port': search_mail_server.smtp_port,
                'smtp_encryption': search_mail_server.smtp_encryption

            }
            ctx = { 'set_connection': True, 'user_id': self.id}
            search_mail_server_obj = self.env['new.mail_server.model'].create(vals)
            return {
                'type': 'ir.actions.act_window',
                'name': 'Outgoing Mail Servers',
                'view_type': 'form',
                'view_mode': 'form',
                'views': [(view_id, 'form')],
                'res_id': search_mail_server_obj.id,
                'res_model': 'new.mail_server.model',
                'target': 'new',
                'context':ctx,
            }
        vals = {
            'name': self.name + ' ' + 'Outgoing Mail Server',
            'smtp_host': 'smtp.office365.com',
            'smtp_port': '25',
            'smtp_encryption': 'starttls',
            'smtp_user': self.login,
        }
        ctx = {
            'set_connection': True,
            'user_id': self.id
        }
        search_mail_server_obj = self.env['new.mail_server.model'].create(vals)
        return {
            'type': 'ir.actions.act_window',
            'name': 'Outgoing Mail Servers',
            'view_type': 'form',
            'view_mode': 'form',
            'views': [(view_id, 'form')],
            'res_id': search_mail_server_obj.id,
            'res_model': 'new.mail_server.model',
            'target': 'new',
            'context': ctx,
        }

    def action_remove(self):
        self.sudo().mail_server_id = False

class NewIrMailServer(models.TransientModel):
    
    _name = "new.mail_server.model"
    _description = "New Mail Server Model"


    mail_server_id = fields.Many2one('ir.mail_server', string='Outgoing Mail Server')
    name = fields.Char(string='Description', required=True, index=True, readonly=False, store=True)
    smtp_host = fields.Char(string='SMTP Server', required=True, help="Hostname or IP of SMTP server", readonly=False, store=True)
    smtp_port = fields.Integer(string='SMTP Port', required=True, default=25, help="SMTP Port. Usually 465 for SSL, and 25 or 587 for other cases.", readonly=False, store=True)
    smtp_user = fields.Char(string='Username', help="Optional username for SMTP authentication", readonly=False, store=True)
    smtp_pass = fields.Char(string='Password', help="Optional password for SMTP authentication", readonly=False, store=True)
    smtp_encryption = fields.Selection([('none', 'None'),
                                        ('starttls', 'TLS (STARTTLS)'),
                                        ('ssl', 'SSL/TLS')],
                                       string='Connection Security', required=True, default='none', readonly=False, store=True,
                                       help="Choose the connection encryption scheme:\n"
                                            "- None: SMTP sessions are done in cleartext.\n"
                                            "- TLS (STARTTLS): TLS encryption is requested at start of SMTP session (Recommended)\n"
                                            "- SSL/TLS: SMTP sessions are encrypted with SSL/TLS through a dedicated port (default: 465)")
    smtp_debug = fields.Boolean(string='Debugging', readonly=False, store=True, help="If enabled, the full output of SMTP sessions will "
                                                         "be written to the server log at DEBUG level "
                                                         "(this is very verbose and may include confidential info!)")
    sequence = fields.Integer(string='Priority', readonly=False, store=True, default=10, help="When no specific mail server is requested for a mail, the highest priority one "
                                                                  "is used. Default priority is 10 (smaller number = higher priority)")

    def action_add_records(self):
        if not self.mail_server_id:
            vals = {
                'name': self.name,
                'smtp_host': self.smtp_host,
                'smtp_port': self.smtp_port,
                'smtp_encryption': self.smtp_encryption,
                'smtp_user': self.smtp_user,
                'smtp_pass': self.smtp_pass,
                'smtp_debug': self.smtp_debug,
                'sequence': self.sequence
            }
            self.mail_server_id = self.env['ir.mail_server'].sudo().create(vals).id
        if self.mail_server_id and 'set_connection' in self._context and self._context.get('set_connection'):
            val = self.mail_server_id.sudo().test_smtp_connection()
        if self.mail_server_id and self._context and 'user_id' in self._context:
            user_id = self._context.get('user_id')
            user_id = self.env['res.users'].sudo().browse(int(user_id))
            if user_id:
                user_id.mail_server_id = self.mail_server_id.id
        vals = {
            'name': self.name,
            'smtp_host': self.smtp_host,
            'smtp_port': self.smtp_port,
            'smtp_encryption': self.smtp_encryption,
            'smtp_user': self.smtp_user,
            'smtp_pass': self.smtp_pass,
            'smtp_debug': self.smtp_debug,
            'sequence': self.sequence
        }
        self.mail_server_id.sudo().write(vals)



class Mail(models.Model):
    _inherit = "mail.mail"

    # @api.model
    # def create(self, vals):
    #     rec = super(Mail, self).create(vals)
    #     context = self._context
    #     current_uid = context.get('uid')
    #     user = self.env['res.users'].browse(current_uid)
    #     search_mail_server = self.env['ir.mail_server'].search([('default','=',True)])
    #     if not user:
    #         user = self.env.user
    #     if not rec.mail_server_id and user and user.mail_server_id:
    #         rec.mail_server_id = user.mail_server_id.id
    #     elif not rec.mail_server_id and user and not user.mail_server_id and search_mail_server:
    #         rec.mail_server_id = search_mail_server.id
    #     author_id = rec.author_id

    #     # print("search_mail_server === ",search_mail_server)
    #     # print("author_id === ",author_id)
    #     # print("len(author_id.user_ids) === ",len(author_id.user_ids))
    #     # print("rec.mail_message_id === ",rec.mail_message_id)
    #     # print("rec.mail_server_id.smtp_user === ",rec.mail_server_id.smtp_user)


    #     if author_id and not len(author_id.user_ids) and rec.mail_message_id and rec.mail_server_id.smtp_user:
            
    #         email_from_new = '"' + str(rec.author_id.name) + '" <' + rec.mail_server_id.smtp_user + '>'
    #         rec.email_from = email_from_new
    #         mail_message_id = rec.mail_message_id
    #         mail_message_id.email_from = email_from_new
    #     return rec


    @api.model_create_multi
    def create(self, vals):
        # Call the super create method to handle record creation
        recs = super(Mail, self).create(vals)
        context = self._context
        current_uid = context.get('uid', self.env.uid)
        user = self.env['res.users'].browse(current_uid)
        search_mail_server = self.env['ir.mail_server'].search([('default', '=', True)], limit=1)
        
        for rec in recs:
            # Use the current user as a fallback if not explicitly provided
            if not user:
                user = self.env.user

            # Assign the mail server based on user or default settings
            if not rec.mail_server_id:
                if user.mail_server_id:
                    rec.mail_server_id = user.mail_server_id.id
                elif search_mail_server:
                    rec.mail_server_id = search_mail_server.id

            # Update email_from if required
            if (
                rec.author_id and
                not rec.author_id.user_ids and
                rec.mail_message_id and
                rec.mail_server_id.smtp_user
            ):
                email_from_new = f'"{rec.author_id.name}" <{rec.mail_server_id.smtp_user}>'
                rec.email_from = email_from_new
                rec.mail_message_id.email_from = email_from_new

        return recs

class GoogleGmailMixin(models.AbstractModel):

    _inherit = 'google.gmail.mixin'
    
    google_gmail_refresh_token = fields.Char(string='Refresh Token', groups=False, copy=False)
    google_gmail_uri = fields.Char(compute='_compute_gmail_uri', string='URI', help='The URL to generate the authorization code from Google', groups=False)


class MicrosoftOutlookMixin(models.AbstractModel):

    _inherit = 'microsoft.outlook.mixin'

    microsoft_outlook_refresh_token = fields.Char(string='Outlook Refresh Token',
        groups=False, copy=False)


    def open_microsoft_outlook_uri(self):
        """Open the URL to accept the Outlook permission.

        This is done with an action, so we can force the user the save the form.
        We need him to save the form so the current mail server record exist in DB and
        we can include the record ID in the URL.
        """
        self.ensure_one()

        # if not self.env.user.has_group('base.group_system'):
        #     raise AccessError(_('Only the administrator can link an Outlook mail server.'))

        if not self.is_microsoft_outlook_configured:
            raise UserError(_('Please configure your Outlook credentials.'))

        return {
            'type': 'ir.actions.act_url',
            'url': self.microsoft_outlook_uri,
        }
        

class HrEmployeePublic(models.Model):
    _inherit = 'hr.employee'

    @api.model
    def _lang_get(self):
        return self.env['res.lang'].get_installed()
   
    # private info
    private_street = fields.Char(string="Private Street", groups=False)
    private_street2 = fields.Char(string="Private Street2", groups=False)
    private_city = fields.Char(string="Private City", groups=False)
    private_state_id = fields.Many2one(
        "res.country.state", string="Private State",
        domain="[('country_id', '=?', private_country_id)]",
        groups=False)
    private_zip = fields.Char(string="Private Zip", groups=False)
    private_country_id = fields.Many2one("res.country", string="Private Country", groups=False)
    private_phone = fields.Char(string="Private Phone", groups=False)
    private_email = fields.Char(string="Private Email", groups=False)
    lang = fields.Selection(selection=_lang_get, string="Lang", groups=False)
    country_id = fields.Many2one(
        'res.country', 'Nationality (Country)', groups=False, tracking=True)
    gender = fields.Selection([
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other')
    ], groups=False, tracking=True)
    marital = fields.Selection([
        ('single', 'Single'),
        ('married', 'Married'),
        ('cohabitant', 'Legal Cohabitant'),
        ('widower', 'Widower'),
        ('divorced', 'Divorced')
    ], string='Marital Status', groups=False, default='single', tracking=True)
    spouse_complete_name = fields.Char(string="Spouse Complete Name", groups=False, tracking=True)
    spouse_birthdate = fields.Date(string="Spouse Birthdate", groups=False, tracking=True)
    children = fields.Integer(string='Number of Dependent Children', groups=False, tracking=True)
    place_of_birth = fields.Char('Place of Birth', groups=False, tracking=True)
    country_of_birth = fields.Many2one('res.country', string="Country of Birth", groups=False, tracking=True)
    birthday = fields.Date('Date of Birth', groups=False, tracking=True)
    ssnid = fields.Char('SSN No', help='Social Security Number', groups=False, tracking=True)
    sinid = fields.Char('SIN No', help='Social Insurance Number', groups=False, tracking=True)
    identification_id = fields.Char(string='Identification No', groups=False, tracking=True)
    passport_id = fields.Char('Passport No', groups=False, tracking=True)
    bank_account_id = fields.Many2one(
        'res.partner.bank', 'Bank Account Number',
        domain="[('partner_id', '=', work_contact_id), '|', ('company_id', '=', False), ('company_id', '=', company_id)]",
        groups=False,
        tracking=True,
        help='Employee bank account to pay salaries')
    permit_no = fields.Char('Work Permit No', groups=False, tracking=True)
    visa_no = fields.Char('Visa No', groups=False, tracking=True)
    visa_expire = fields.Date('Visa Expiration Date', groups=False, tracking=True)
    work_permit_expiration_date = fields.Date('Work Permit Expiration Date', groups=False, tracking=True)
    has_work_permit = fields.Binary(string="Work Permit", groups=False)
    work_permit_scheduled_activity = fields.Boolean(default=False, groups=False)
    additional_note = fields.Text(string='Additional Note', groups=False, tracking=True)
    certificate = fields.Selection([
        ('graduate', 'Graduate'),
        ('bachelor', 'Bachelor'),
        ('master', 'Master'),
        ('doctor', 'Doctor'),
        ('other', 'Other'),
    ], 'Certificate Level', default='other', groups=False, tracking=True)
    study_field = fields.Char("Field of Study", groups=False, tracking=True)
    study_school = fields.Char("School", groups=False, tracking=True)
    emergency_contact = fields.Char("Contact Name", groups=False, tracking=True)
    emergency_phone = fields.Char("Contact Phone", groups=False, tracking=True)
    km_home_work = fields.Integer(string="Home-Work Distance", groups=False, tracking=True)
    employee_type = fields.Selection([
            ('employee', 'Employee'),
            ('student', 'Student'),
            ('trainee', 'Trainee'),
            ('contractor', 'Contractor'),
            ('freelance', 'Freelancer'),
        ], string='Employee Type', default='employee', required=True, groups=False,
        help="The employee type. Although the primary purpose may seem to categorize employees, this field has also an impact in the Contract History. Only Employee type is supposed to be under contract and will have a Contract History.")

    # employee in company
    category_ids = fields.Many2many(
        'hr.employee.category', 'employee_category_rel',
        'emp_id', 'category_id', groups=False,
        string='Tags')
    # misc
    notes = fields.Text('Notes', groups=False)
    barcode = fields.Char(string="Badge ID", help="ID used for employee identification.", groups=False, copy=False)
    pin = fields.Char(string="PIN", groups=False, copy=False,
        help="PIN used to Check In/Out in the Kiosk Mode of the Attendance application (if enabled in Configuration) and to change the cashier in the Point of Sale application.")
    departure_reason_id = fields.Many2one("hr.departure.reason", string="Departure Reason", groups=False,
                                          copy=False, tracking=True, ondelete='restrict')
    departure_description = fields.Html(string="Additional Information", groups=False, copy=False)
    departure_date = fields.Date(string="Departure Date", groups=False, copy=False, tracking=True)
    message_main_attachment_id = fields.Many2one(groups=False)
    id_card = fields.Binary(string="ID Card Copy", groups=False)
    driving_license = fields.Binary(string="Driving License", groups=False)
    private_car_plate = fields.Char(groups=False, help="If you have more than one car, just separate the plates by a space.")
    # properties
    attendance_manager_id = fields.Many2one(
        'res.users', store=True, readonly=False,
        domain="[('share', '=', False), ('company_ids', 'in', company_id)]",
        groups=False,
        help="The user set in Attendance will access the attendance of the employee through the dedicated app and will be able to edit them.")


class HrEmployeePublic(models.Model):
    _inherit = 'hr.employee.public'

    attendance_manager_id = fields.Many2one(related='employee_id.attendance_manager_id', groups=False)