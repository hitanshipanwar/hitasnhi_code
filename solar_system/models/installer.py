from odoo import fields,api,models

class Installer(models.Model):
    _name= 'installer.bid'
    _rec_name = 'sequence_no'

    sequence_no = fields.Char(string='Sequence',index=True,copy=False,readonly=True)
    project_id = fields.Many2one('installation.solar.system', domain=[('installer_project_state','=','open')],string="Project")
    bid_description = fields.Char(string="Description")
    price = fields.Char(string="Price")
    customer_id = fields.Many2one('res.partner',string="Installer",tracking=True)
    installer_create_date = fields.Date(string='Date', default=fields.Date.today())

    project_state = fields.Selection(selection=[
                ('open', 'Open'),
                ('inprogress', 'InProgress'),
                ('won', 'Won'),
                ('lost', 'Lost'),
            ], string='Status', required=True, readonly=True, default='open',tracking=True)

    @api.model
    def create(self,vals):
        if vals.get('sequence_no', 'New') == 'New':
            vals['sequence_no'] = self.env['ir.sequence'].next_by_code('installer.bid') or 'New'
        result = super(Installer, self).create(vals)
        return result

    # status update after approve the supplier Bid 
    def approved_bid_installer(self):
        vals = self.env['installer.bid'].sudo().search([('project_id','=',self.project_id.id)])
        rec = self.env['installation.solar.system'].sudo().search([('id','=',self.project_id.id)])
        for data in vals:
            data.update({"project_state":"lost"})
            data.project_id.update({"project_state":"lost"})

        self.update({"project_state":"won"})
        rec.update({"project_state":"won"})
        # rec.update({"customer_project_state":"close"})    