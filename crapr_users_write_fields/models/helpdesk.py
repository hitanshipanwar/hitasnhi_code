from odoo import fields, models, api


class HelpdeskTicket(models.Model):
    _name = 'helpdesk.ticket'
    _inherit = ['helpdesk.ticket', 'write.activity.mixin']

    def action_fill_custom_write_fields_helpdesk_ticket(self):
        """
        Action for filling the records without custom write by sql queries for model helpdesk.ticket.
        """
        without_custom_fields_record = self.filtered(
            lambda el: (not (bool(el.custom_write_uid) and bool(el.custom_write_uid))) and (el.write_uid.id != 1)).ids
        if without_custom_fields_record:
            id_tuple = tuple(without_custom_fields_record)
            if len(id_tuple) == 1:
                sql = """
                UPDATE helpdesk_ticket SET custom_write_date = write_date,
                custom_write_uid = write_uid
                WHERE id = %s""" % id_tuple[0]
                self.env.cr.execute(sql)
            else:
                sql = """
                UPDATE helpdesk_ticket SET custom_write_date = write_date,
                custom_write_uid = write_uid
                WHERE id IN {}""".format(id_tuple)
                self.env.cr.execute(sql)
