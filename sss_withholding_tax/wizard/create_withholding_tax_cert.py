# Copyright 2019 Ecosoft Co., Ltd (https://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError

from ..models.withholding_tax_cert import INCOME_TAX_FORM, WHT_CERT_INCOME_TYPE


class CreateWithholdingTaxCert(models.TransientModel):
    _name = "create.withholding.tax.cert"
    _description = "Create Withholding Tax Cert Wizard"

    # wt_certificate_ids = fields.One2many(
    #     comodel_name='withholding.tax.certificate',
    #     inverse_name='wt_line_id',
    #     string="WT Certificates",)

    wt_line_id = fields.Many2one('withholding.tax.certificate')
    wt_account_ids = fields.Many2many(
        comodel_name="account.account",
        string="Withholing Tax Accounts",
        required=True,
        help="If accounts are specified, system will auto fill tax amount",
        default=lambda self: self.env["account.account"].search(
            [("wt_account", "=", True)]
        ),
    )
    substitute = fields.Boolean(string="Substitute")
    wt_cert_id = fields.Many2one(
        comodel_name="withholding.tax.cert",
        domain=[("state", "=", "done")],
        help="Withholding Tax is state 'done' only",
    )
    # Used for create multi certs
    income_tax_form = fields.Selection(
        selection=INCOME_TAX_FORM, string="Income Tax Form"
    )
    wt_cert_income_type = fields.Selection(
        selection=WHT_CERT_INCOME_TYPE, string="Type of Income"
    )
    other_income_desc = fields.Char('Other Description')

    @api.model
    def default_get(self, fields):
        res = super().default_get(fields)
        model = self._context.get("active_model", False)
        for active_id in self._context.get("active_ids", []):
            if model == "account.move":
                move = self.env[model].browse(active_id)
                if move.move_type != "entry":
                    raise UserError(
                        _(
                            "You can create withholding tax from "
                            "Payment or Journal Entry only."
                        )
                    )
                if move.state != "posted":
                    raise UserError(
                        _(
                            "You can create withholding tax from "
                            "Journal Entry state 'Paid' only."
                        )
                    )
        return res

    def create_wt_cert(self):
        self.ensure_one()
        ctx = self._context.copy()
        # model = ctx.get("active_model", False)
        # active_id = ctx.get("active_id")
        # object_id = self.env[model].browse(active_id)
        # print('=========object_id==================',object_id)
        # if len(ctx.get("active_ids", [])) != 1:
        #     raise ValidationError(_("Please select only 1 document"))
        # if model == "account.move":
        #     ctx.update(
        #         {
        #             "default_move_id": active_id,
        #             "wt_account_ids": self.wt_account_ids.ids,
        #         }
        #     )
        #     print('-------------xxxxxxxxxxx',ctx)
        # else:
        #     payment_wt = object_id.move_id.line_ids.filtered(
        #         lambda l: l.account_id.id in self.wt_account_ids.ids
        #     )
        #     print('2222222222222222222222222222222222222',payment_wt)
        #     if not payment_wt:
        #         raise UserError(
        #             _(
        #                 "Can not create withholding tax cert. Selected account "
        #                 "does not match with Journal Items."
        #             )
        #         )
        #     ctx.update(
        #         {
        #             "default_payment_id": active_id,
        #             "wt_account_ids": self.wt_account_ids.ids,
        #         }
        #     )
        #     print('===============xxxxxxxxxxxxxxxxxxxxxxxxxx==============================',ctx)
        # Substitute WT Cert
        # if self.substitute:
        #     ctx.update({"wt_ref_id": self.wt_cert_id.id})
        # # Other defaults
        # ctx.update(
        #     {
        #         "income_tax_form": self.income_tax_form,
        #         "wt_cert_income_type": self.wt_cert_income_type,
        #         "default_type_of_income": self.wt_cert_income_type,
        #     }
        # )
        # if self.other_income_desc:
        #     ctx.update({"default_other_income_desc": self.other_income_desc})

        # Sunen
        Cert = self.env["withholding.tax.cert"]
        cert_ids = []
        ctx = self._context.copy()

        #last
        #h payment = self.env['account.payment'].browse(ctx.get("active_id"))
        #h wt_move_lines = payment.move_id.line_ids.filtered(
        #h         lambda l: l.wt_tax_id 
        #h     )

        #new
        move_lines = self.env['account.move.line'].browse(self.env.context.get('active_id'))
        moves = self.env['account.move'].search([('line_ids.id', '=', move_lines.id)])

        # move_line = self.env['account.move.line'].browse(self.env.context.get('active_id'))
        # print('=====sssssssssssssssss============================',move_line)
        # move_id = self.env['account.move'].search([('id', '=', move_line.move_id.id)])
        # print('====sssssssssssssssss======================',move_id)
        
        # moves = self.env['account.move'].browse(ctx.get("active_id"))
        # wt_move_lines = moves.line_ids.filtered(
        #         lambda l: l.wt_tax_id 
        #     )
        wt_move_lines = move_lines.filtered(
                lambda l: l.wt_tax_id 
            )
        
        # for move_line in move_lines:
        for move_line in wt_move_lines:
            ctx = {}
            ctx.update(
                {
                    # "default_payment_id": moves.id,
                    "wt_account_ids": move_line.account_id.ids,
                    #h "wt_account_ids": self.wt_account_ids.ids,
                    "income_tax_form": self.income_tax_form,
                    "wt_cert_income_type": self.wt_cert_income_type,
                    "default_type_of_income": self.wt_cert_income_type,
                    "default_move_id": moves.id,
                }
            )
            if self.other_income_desc:
                ctx.update({"default_other_income_desc": self.other_income_desc})
            record = Cert.with_context(ctx).new()
            # wt_move_lines = record._get_wt_move_line(
            #         record.payment_id, record.move_id, move_line.account_id.ids
            #     )
            # print('----------------wt_move_lineswt_move_lines-----------------------', wt_move_lines)
            #h partner_id = record.payment_id.partner_id or record.move_id.partner_id
            partner_id = record.move_id.partner_id
            record.update(
                {
                    "name": moves.name or record.move_id.name,
                    #h "date": record.payment_id.date or record.move_id.date,
                    "date": record.move_id.date or moves.invoice_date,
                    # "ref_wt_cert_id": wt_reference or False,
                    "supplier_partner_id": partner_id or moves.partner_id,
                    "income_tax_form": self.income_tax_form,
                    "other_income_desc": self.other_income_desc,
                    "type_of_income": self.wt_cert_income_type,
                }
            )
            for line in move_line:
                record.write({'wt_line':[(0,0,record._prepare_wt_line(line))]})
            # cert._compute_wt_cert_data()
            new_cert = Cert.create(record._convert_to_write(record._cache))
            cert_ids.append(new_cert.id)



        # Cert = self.env["withholding.tax.cert"]
        # cert_ids = []
        # for active_id in active_ids:
        #     ctx.update(
        #         {"active_id": active_id, "active_ids": [active_id]}
        #     )  # Mock single cert.
        #     res = self.with_context(ctx).create_wt_cert()
        #     # Create new withholding.tax.cert
        #     cert = Cert.with_context(res["context"]).new()
        #     cert._compute_wt_cert_data()
        #     new_cert = Cert.create(cert._convert_to_write(cert._cache))
        #     cert_ids.append(new_cert.id)

        return {
            "name": _("Create Multi Withholding Tax Cert."),
            "view_mode": "tree,form",
            "res_model": "withholding.tax.cert",
            "view_id": False,
            "type": "ir.actions.act_window",
            "domain": [("id", "in", cert_ids)],
        }
        # return {
        #     "name": _("Create Withholding Tax Cert."),
        #     "view_mode": "form",
        #     "res_model": "withholding.tax.cert",
        #     "type": "ir.actions.act_window",
        #     "context": ctx,
        # }

    def create_wt_cert_multi(self):
        ctx = self._context.copy()
        active_ids = ctx.get("active_ids")
        Cert = self.env["withholding.tax.cert"]
        cert_ids = []
        for active_id in active_ids:
            ctx.update(
                {"active_id": active_id, "active_ids": [active_id]}
            )  # Mock single cert.
            res = self.with_context(ctx).create_wt_cert()
            # Create new withholding.tax.cert
            cert = Cert.with_context(res["context"]).new()
            cert._compute_wt_cert_data()
            new_cert = Cert.create(cert._convert_to_write(cert._cache))
            cert_ids.append(new_cert.id)
        return {
            "name": _("Create Multi Withholding Tax Cert."),
            "view_mode": "tree,form",
            "res_model": "withholding.tax.cert",
            "view_id": False,
            "type": "ir.actions.act_window",
            "domain": [("id", "in", cert_ids)],
        }

class WithholdingTaxCertificate(models.TransientModel):
    _name = "withholding.tax.certificate"
    _description = "Withholding Tax Certificae Wizard"


    # wt_certificate_ids = fields.One2many(
    #     comodel_name='create.withholding.tax.cert',
    #     inverse_name='wt_line_id',
    #     string="WT Certificates",)

    wt_line_id = fields.Many2one('create.withholding.tax.cert', string="Related")
    wt_account_ids = fields.Many2many(
        comodel_name="account.account",
        string="Withholing Tax Accounts",
        required=True,
        help="If accounts are specified, system will auto fill tax amount",
        default=lambda self: self.env["account.account"].search(
            [("wt_account", "=", True)]
        ),
    )
    substitute = fields.Boolean(string="Substitute")
    wt_cert_id = fields.Many2one(
        comodel_name="withholding.tax.cert",
        domain=[("state", "=", "done")],
        help="Withholding Tax is state 'done' only",
        string="WT Related"
    )
    # Used for create multi certs
    income_tax_form = fields.Selection(
        selection=INCOME_TAX_FORM, string="Income Tax Form"
    )
    wt_cert_income_type = fields.Selection(
        selection=WHT_CERT_INCOME_TYPE, string="Type of Income"
    )
    other_income_desc = fields.Char(string='Other Description')


    # wt_certificate_ids = fields.One2many('create.withholding.tax.cert', 'wt_line_id', string="WT Certificates")


