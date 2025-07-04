from odoo import fields,models,api

class ScriptExecuteLog(models.Model):
    _name = 'script.execute.log'
    _description = 'Script Execute Log'

    name = fields.Char('Name', required=True)
    python_code = fields.Text(string='Code', required=True)
    output = fields.Text(string='Output', readonly=True)

    @api.multi
    def script_execute(self):
        dict = {'self': self, 'user_obj': self.env.user}
        for obj in self:
            try:
                exec(obj.python_code, dict)
                if 'output' in dict:
                    self.write({'output': dict['output']})
                else:
                    self.write({'output': ''})
            except Exception as e:
                raise Warning('Opps!! something missing ! \n message : {}'.format(e))
        return True