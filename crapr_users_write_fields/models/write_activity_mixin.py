from odoo import fields, models, _


class WriteActivityMixin(models.AbstractModel):
    """
    Mixin class made to add 2 custom fields served as replacement for magic methods fields,
    for the models who inherit this class.
    """
    _name = 'write.activity.mixin'
    _description = 'Write Activity Mixin'

    # Field Declarations
    custom_write_uid = fields.Many2one('res.users', string='Data Last Updated by', copy=True, store=True)
    custom_write_date = fields.Datetime(string='Data Last Updated on', copy=True, store=True)

    def write(self, vals):
        """
        Inherited this method to change the inherited model's new fields with current user and date.
        """
        if not self.user_has_groups('crapr_users_write_fields.group_write_override') and self._context.get('no_update',False) == False:
            vals.update({'custom_write_uid': self.env.user.id, 'custom_write_date': fields.Datetime.now()})
        return super(WriteActivityMixin, self).write(vals)
